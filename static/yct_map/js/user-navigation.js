import { createLiveRouteTracker, distanceMetres,
  formatEta } from "./live-route-progress.js?v=system-closeout-4";
import { createOffRouteDetector } from "./off-route.js?v=system-closeout-4";

export const MAX_LIVE_POSITION_AGE_MS = 30_000;
export const NEARBY_MAPPED_START_MAX_METRES = 350;
export const MAX_LIVE_ROUTE_ATTEMPTS = 3;
export const LIVE_ROUTE_RECOVERY_WINDOW_MS = 10_000;
const TRANSIENT_LIVE_ROUTE_CODES = new Set(["NO_SAFE_NETWORK_MATCH", "INSUFFICIENT_ACCURACY"]);
const LIVE_ROUTE_FINAL_MESSAGE = "Your location is clear, but it cannot yet be safely connected to the mapped campus paths. Choose a mapped starting point or try live location again after moving closer to a mapped walkway.";

export function isLivePositionRouteUsable(position, { now = Date.now(),
  maxAgeMs = MAX_LIVE_POSITION_AGE_MS } = {}) {
  if (!position || position.accuracyMetres > 40 || !Number.isFinite(position.timestamp)) return false;
  if (position.freshness === "stale" || position.supportedAreaValid === false) return false;
  return now - position.timestamp <= maxAgeMs;
}

function routeOriginSnapshot(position) {
  return Object.freeze({
    longitude: position.longitude,
    latitude: position.latitude,
    accuracyMetres: position.accuracyMetres,
    timestamp: position.timestamp,
    freshness: position.freshness || "fresh",
  });
}

function featureKey(feature) {
  return feature?.properties?.destination_key || feature?.properties?.id || feature?.id || "";
}

export function findNearbyMappedStart(features, destination, position,
  { maxDistanceMetres = NEARBY_MAPPED_START_MAX_METRES } = {}) {
  if (!position || !Number.isFinite(position.longitude) || !Number.isFinite(position.latitude)) return null;
  const destinationKey = featureKey(destination);
  const point = [position.longitude, position.latitude];
  const candidates = features
    .filter((feature) => feature?.properties?.routing_available === true
      && featureKey(feature) !== destinationKey
      && feature?.geometry?.type === "Point"
      && Array.isArray(feature.geometry.coordinates))
    .map((feature) => ({ feature,
      distanceMetres: distanceMetres(point, feature.geometry.coordinates) }))
    .filter((candidate) => candidate.distanceMetres <= maxDistanceMetres)
    .sort((left, right) => left.distanceMetres - right.distanceMetres);
  return candidates[0] || null;
}

export function createUserNavigation({ panel, features, routeUrl, liveRouteUrl, onRoute, onClear, onBrowse,
  onCancel, onStateChange, onRouteStale, onRouteProgress = () => {}, requestRoute = fetch, now = Date.now,
  setDeadline = globalThis.setTimeout, clearDeadline = globalThis.clearTimeout,
  onFreshLocationRequired = () => false }) {
  const form = panel.querySelector("#user-route-form");
  const liveOriginInput = panel.querySelector("#user-route-origin-live");
  const liveOriginStatus = panel.querySelector("#user-route-live-status");
  const mappedOrigins = panel.querySelector("#user-route-mapped-origins");
  const destinationName = panel.querySelector("#user-route-destination");
  const summaryDestinationName = panel.querySelector("#user-route-summary-destination");
  const submitButton = panel.querySelector("#show-user-route");
  const requestStatus = panel.querySelector("#user-route-request-status");

  // Keep the controller's sentinel explicit for lightweight DOM harnesses and
  // for any server-rendered markup restored from an older cached document.
  liveOriginInput.value = "__live__";
  const retryButton = panel.querySelector("#retry-reroute");
  const error = panel.querySelector("#user-route-error");
  const result = panel.querySelector("#user-route-result");
  const formState = panel.querySelector("#user-route-form-state");
  const detailsToggle = panel.querySelector("#toggle-route-details");
  let destination = null;
  let livePosition = null;
  let activeTracker = null;
  let offRouteDetector = null;
  let rerouteRequestActive = false;
  let visibleBeforeSuspend = false;
  let activeDestinationSummary = null;
  let selectedOrigin = "";
  let setupRequestActive = false;
  let setupRequestGeneration = 0;
  let setupAbortController = null;
  let liveRecovery = null;
  let freshStartWait = null;
  let liveOptionSignature = "";
  let livePositionRefreshing = false;
  let activeMappedJoin = null;

  const csrfToken = () => document.cookie.split("; ").find((row) => row.startsWith("csrftoken="))?.split("=")[1] || "";
  function livePositionUsable(position = livePosition) {
    return isLivePositionRouteUsable(position, { now: now() });
  }
  function updateLiveOption() {
    const usable = livePositionUsable();
    const stale = Boolean(livePosition) && !usable;
    const retained = usable && livePosition?.freshness === "retained";
    const status = retained
      ? `Recent stable position Â· ~${Math.round(livePosition.accuracyMetres)} m`
      : usable ? `Live location ready Â· ~${Math.round(livePosition.accuracyMetres)} m`
        : livePositionRefreshing ? "Refreshing current location"
          : stale || selectedOrigin === "__live__" ? "Current location needs refreshing" : "Locate first";
    const signature = `${usable}:${status}`;
    if (signature !== liveOptionSignature) {
      liveOriginInput.disabled = !usable;
      liveOriginStatus.textContent = status;
      liveOptionSignature = signature;
    }
    updateSubmitState();
  }
  function updateSubmitState() {
    submitButton.disabled = setupRequestActive || Boolean(liveRecovery) || Boolean(freshStartWait)
      || !selectedOrigin;
  }
  function resetMessages() {
    error.hidden = true;
    result.hidden = true;
    requestStatus.hidden = true;
    requestStatus.textContent = "";
  }
  function setRoutePanelState(state, expanded = false) {
    panel.dataset.routeState = state;
    panel.dataset.detailsExpanded = String(expanded);
    detailsToggle?.setAttribute("aria-expanded", String(expanded));
  }
  function requestLiveRoute(position, { signal } = {}) {
    return requestRoute(liveRouteUrl, { method: "POST", headers: {
      Accept: "application/json", "Content-Type": "application/json", "X-CSRFToken": csrfToken(),
    }, body: JSON.stringify({ destination: destination.properties.destination_key || destination.properties.id, position: {
      latitude: position.latitude, longitude: position.longitude, accuracy_metres: position.accuracyMetres,
    } }), signal });
  }
  function clearRecoveryTimer(recovery = liveRecovery) {
    if (recovery && recovery.deadlineId !== null) clearDeadline(recovery.deadlineId);
    if (recovery) recovery.deadlineId = null;
  }
  function clearFreshStartWait(wait = freshStartWait) {
    if (wait?.deadlineId !== null && wait?.deadlineId !== undefined) clearDeadline(wait.deadlineId);
    if (freshStartWait === wait) freshStartWait = null;
  }
  function cancelPendingSetup() {
    setupRequestGeneration += 1;
    setupAbortController?.abort();
    setupAbortController = null;
    setupRequestActive = false;
    clearRecoveryTimer();
    liveRecovery = null;
    clearFreshStartWait();
    requestStatus.hidden = true;
    requestStatus.textContent = "";
    submitButton.textContent = "Show route";
    updateSubmitState();
  }
  function showSetupActivity(message, state = "loading") {
    requestStatus.textContent = message;
    requestStatus.hidden = false;
    submitButton.textContent = state === "loading" ? "Calculatingâ€¦" : "Show route";
    setRoutePanelState(state);
    updateSubmitState();
  }
  function showSetupError(message) {
    requestStatus.hidden = true;
    requestStatus.textContent = "";
    error.textContent = message;
    error.hidden = false;
    submitButton.textContent = "Show route";
    setRoutePanelState("error", true);
    updateSubmitState();
  }
  function routeResponseError(payload, fallback) {
    const routeError = new Error(payload?.error || fallback);
    routeError.code = payload?.code || "";
    return routeError;
  }
  function chooseOrigin(value) {
    cancelPendingSetup();
    selectedOrigin = value;
    error.hidden = true;
    result.hidden = true;
    setRoutePanelState("setup");
    updateSubmitState();
  }
  function createMappedOrigin(candidate, index) {
    const label = mappedOrigins.ownerDocument.createElement("label");
    label.className = "route-origin-option";
    const input = mappedOrigins.ownerDocument.createElement("input");
    input.type = "radio";
    input.name = "user-route-origin";
    input.value = candidate.properties.id;
    input.id = `user-route-origin-${index}`;
    input.addEventListener("change", () => chooseOrigin(input.value));
    const copy = mappedOrigins.ownerDocument.createElement("span");
    copy.className = "route-origin-copy";
    const name = mappedOrigins.ownerDocument.createElement("strong");
    name.textContent = candidate.properties.name;
    copy.append(name);
    label.setAttribute("for", input.id);
    label.append(input);
    label.append(copy);
    return label;
  }

  function renderDestinationSummary(summary) {
    activeDestinationSummary = summary;
    const arrival = summary.outdoor_arrival;
    const handoff = summary.indoor_handoff;
    panel.querySelector("#user-route-to").textContent = arrival?.label || summary.name;
    const arrivalPrefix = panel.querySelector("#user-route-arrival-prefix");
    if (arrivalPrefix) arrivalPrefix.textContent = handoff ? "Outdoor arrival:" : "Arrive at";
    if (summaryDestinationName) summaryDestinationName.textContent = summary.name;
    const compact = panel.querySelector("#user-route-summary-handoff");
    const section = panel.querySelector("#user-route-internal-handoff");
    if (!handoff) {
      if (compact) compact.hidden = true;
      if (section) section.hidden = true;
      return;
    }
    const indoorLocation = [handoff.floor, handoff.room_code, handoff.wing_section].filter(Boolean).join(" · ");
    if (compact) {
      compact.textContent = `Inside: ${indoorLocation || handoff.name}`;
      compact.hidden = false;
    }
    if (section) section.hidden = false;
    const internalName = panel.querySelector("#user-route-internal-name");
    const internalLocation = panel.querySelector("#user-route-internal-location");
    const internalDirection = panel.querySelector("#user-route-internal-direction");
    if (internalName) internalName.textContent = handoff.name;
    if (internalLocation) internalLocation.textContent = indoorLocation || "Indoor location details are incomplete.";
    if (internalDirection) internalDirection.textContent = handoff.direction_note
      || "No indoor direction note has been recorded.";
  }

  function begin(feature) {
    if (feature?.properties?.routing_available !== true) return false;
    cancelPendingSetup();
    destination = feature;
    destinationName.textContent = feature.properties.name;
    selectedOrigin = "";
    liveOriginInput.checked = false;
    mappedOrigins.replaceChildren();
    updateLiveOption();
    features.filter((item) => item.properties.routing_available === true
      && item.properties.id !== feature.properties.id)
      .forEach((candidate, index) => mappedOrigins.append(createMappedOrigin(candidate, index)));
    resetMessages();
    formState.hidden = false;
    setRoutePanelState("setup");
    panel.hidden = false;
    updateSubmitState();
    if (livePosition && !livePositionUsable()) onFreshLocationRequired();
    retryButton.hidden = true;
    const firstMappedInput = mappedOrigins.children[0]?.children?.[0];
    (liveOriginInput.disabled ? firstMappedInput : liveOriginInput)?.focus();
    onStateChange?.("choosing-origin");
    return true;
  }

  function activateRoute(payload, { useLive, origin, mappedJoin = null }) {
    const totalDistance = payload.summary.total_distance_metres ?? payload.summary.distance_metres;
    const originArrival = payload.summary.origin.outdoor_arrival?.label || payload.summary.origin.name;
    panel.querySelector("#user-route-from").textContent = originArrival;
    renderDestinationSummary(payload.summary.destination);
    panel.querySelector("#user-route-distance").textContent = `${Math.round(totalDistance)} m`;
    panel.querySelector("#user-route-eta").textContent = payload.summary.eta_label;
    panel.querySelector("#user-route-progress-status").hidden = !useLive;
    panel.querySelector("#user-route-progress-status").textContent = mappedJoin
      ? `Walk to ${originArrival} to join the mapped route`
      : "Live route active · waiting for movement";
    panel.querySelector("#user-route-eta-source").textContent = mappedJoin
      ? `Distance and ETA begin at ${originArrival}`
      : useLive ? "Approximate ETA at 1.35 m/s" : "";
    const routeState = payload.summary?.verification_state
      || payload.route?.properties?.route_state
      || "UNVERIFIED";
    const routeBadge = panel.querySelector("#user-route-badge") || panel.querySelector(".demo-route-label");
    const routeNotice = panel.querySelector("#user-route-data-notice");
    if (routeBadge) {
      if (routeState === "FIELD_VERIFIED") {
        routeBadge.hidden = true;
      } else {
        routeBadge.hidden = false;
        routeBadge.textContent = routeState === "DEMO" ? "DEMO ROUTE" : "UNVERIFIED ROUTE";
      }
    }
    if (routeNotice) {
      if (routeState === "FIELD_VERIFIED") {
        routeNotice.hidden = true;
      } else {
        routeNotice.hidden = false;
        routeNotice.textContent = mappedJoin
          ? `Walk to ${originArrival} to join the mapped route; no route from your dot to that entrance is claimed.`
          : routeState === "DEMO"
          ? "Synthetic information for product demonstration only."
          : "Campus route guidance.";
      }
    }
    formState.hidden = true;
    result.hidden = false;
    requestStatus.hidden = true;
    requestStatus.textContent = "";
    setRoutePanelState("active", false);
    activeTracker = useLive ? createLiveRouteTracker(payload.route.geometry.coordinates, totalDistance) : null;
    offRouteDetector = useLive ? createOffRouteDetector() : null;
    activeMappedJoin = mappedJoin ? { ...mappedJoin, label: originArrival,
      coordinate: [...payload.route.geometry.coordinates[0]] } : null;
    retryButton.hidden = true;
    onRouteStale?.(false);
    onRoute(payload.route, origin, destination, {
      originType: mappedJoin ? "live-mapped-start" : useLive ? "live" : "manual",
      startName: originArrival,
      arrivalName: payload.summary.destination.outdoor_arrival?.label || payload.summary.destination.name,
    });
    onStateChange?.("route-available");
  }

  function finishLiveRecovery(recovery, message = LIVE_ROUTE_FINAL_MESSAGE) {
    if (liveRecovery !== recovery) return;
    clearRecoveryTimer(recovery);
    liveRecovery = null;
    setupAbortController?.abort();
    setupAbortController = null;
    setupRequestActive = false;
    showSetupError(message);
  }

  async function tryNearbyMappedStart(position, recovery) {
    const nearby = findNearbyMappedStart(features, destination, position);
    if (!nearby || liveRecovery !== recovery) return false;
    const origin = nearby.feature;
    const parameters = new URLSearchParams({ origin: featureKey(origin), destination: featureKey(destination) });
    requestStatus.textContent =
      `Your position is away from mapped paths. Starting at ${origin.properties.name}'s entrance…`;
    requestStatus.hidden = false;
    try {
      const response = await requestRoute(`${routeUrl}?${parameters}`, {
        headers: { Accept: "application/json" }, signal: setupAbortController.signal,
      });
      const payload = await response.json();
      if (!response.ok || liveRecovery !== recovery) return false;
      clearRecoveryTimer(recovery);
      liveRecovery = null;
      setupRequestActive = false;
      setupAbortController = null;
      activateRoute(payload, { useLive: true, origin, mappedJoin: {
        placeName: origin.properties.name,
        representativeDistanceMetres: nearby.distanceMetres,
      } });
      return true;
    } catch (fallbackError) {
      if (fallbackError.name === "AbortError") return false;
      return false;
    }
  }

  async function attemptLiveRoute(position, recovery) {
    if (liveRecovery !== recovery || setupRequestActive || !livePositionUsable(position)
        || position.timestamp <= recovery.lastAttemptTimestamp) return false;
    if (recovery.attempts >= MAX_LIVE_ROUTE_ATTEMPTS
        || now() - recovery.startedAt > LIVE_ROUTE_RECOVERY_WINDOW_MS) {
      finishLiveRecovery(recovery);
      return false;
    }
    const originSnapshot = routeOriginSnapshot(position);
    recovery.pendingPosition = null;
    recovery.lastAttemptTimestamp = originSnapshot.timestamp;
    recovery.attempts += 1;
    setupRequestActive = true;
    setupAbortController = new AbortController();
    error.hidden = true;
    showSetupActivity(recovery.attempts === 1 ? "Calculating route…" : "Checking a newer live position…");
    try {
      const response = await requestLiveRoute(originSnapshot, { signal: setupAbortController.signal });
      const payload = await response.json();
      if (!response.ok) throw routeResponseError(payload, "No route is available.");
      if (liveRecovery !== recovery) return false;
      clearRecoveryTimer(recovery);
      liveRecovery = null;
      setupRequestActive = false;
      setupAbortController = null;
      activateRoute(payload, { useLive: true, origin: null });
      return true;
    } catch (routeError) {
      if (liveRecovery !== recovery || routeError.name === "AbortError") return false;
      if (routeError.code === "NO_SAFE_NETWORK_MATCH"
          && await tryNearbyMappedStart(originSnapshot, recovery)) return true;
      const retryable = TRANSIENT_LIVE_ROUTE_CODES.has(routeError.code);
      const withinWindow = now() - recovery.startedAt <= LIVE_ROUTE_RECOVERY_WINDOW_MS;
      if (!retryable) {
        finishLiveRecovery(recovery, routeError.message);
        return false;
      }
      if (recovery.attempts >= MAX_LIVE_ROUTE_ATTEMPTS || !withinWindow) {
        finishLiveRecovery(recovery);
        return false;
      }
      requestStatus.textContent = "Checking a newer live position…";
      requestStatus.hidden = false;
      submitButton.textContent = "Show route";
      setRoutePanelState("recovering");
      return false;
    } finally {
      if (liveRecovery === recovery) {
        setupRequestActive = false;
        setupAbortController = null;
        updateSubmitState();
        const pending = recovery.pendingPosition;
        if (pending && pending.timestamp > recovery.lastAttemptTimestamp) void attemptLiveRoute(pending, recovery);
      }
    }
  }

  function startLiveRouteRecovery(position) {
    const recovery = {
      attempts: 0,
      startedAt: now(),
      lastAttemptTimestamp: -Infinity,
      pendingPosition: null,
      deadlineId: null,
    };
    liveRecovery = recovery;
    recovery.deadlineId = setDeadline(() => finishLiveRecovery(recovery), LIVE_ROUTE_RECOVERY_WINDOW_MS);
    updateSubmitState();
    return attemptLiveRoute(position, recovery);
  }

  function waitForFreshRouteOrigin() {
    const wait = { deadlineId: null };
    freshStartWait = wait;
    showSetupActivity("Refreshing your location...", "recovering");
    const requested = onFreshLocationRequired();
    if (requested === false) {
      clearFreshStartWait(wait);
      showSetupError("Current location is unavailable. Use Locate me again or choose a mapped start.");
      return false;
    }
    wait.deadlineId = setDeadline(() => {
      if (freshStartWait !== wait) return;
      clearFreshStartWait(wait);
      showSetupError("Current location could not be refreshed. Try Locate me again or choose a mapped start.");
    }, LIVE_ROUTE_RECOVERY_WINDOW_MS);
    updateSubmitState();
    return true;
  }

  async function calculate(event) {
    event.preventDefault();
    if (setupRequestActive || liveRecovery) return;
    if (!destination || !selectedOrigin) {
      showSetupError("Choose a starting point.");
      return;
    }
    const useLive = selectedOrigin === "__live__";
    if (useLive && !livePositionUsable()) {
      updateLiveOption();
      waitForFreshRouteOrigin();
      return;
    }
    resetMessages();
    if (useLive) {
      await startLiveRouteRecovery(livePosition);
      return;
    }

    const generation = ++setupRequestGeneration;
    setupRequestActive = true;
    setupAbortController = new AbortController();
    showSetupActivity("Calculating route…");
    try {
      const parameters = new URLSearchParams({ origin: selectedOrigin,
        destination: destination.properties.destination_key || destination.properties.id });
      const response = await requestRoute(`${routeUrl}?${parameters}`, {
        headers: { Accept: "application/json" }, signal: setupAbortController.signal,
      });
      const payload = await response.json();
      if (!response.ok) throw routeResponseError(payload, "No route is available.");
      if (generation !== setupRequestGeneration) return;
      const origin = features.find((item) => item.properties.id === selectedOrigin);
      activateRoute(payload, { useLive: false, origin });
    } catch (routeError) {
      if (generation === setupRequestGeneration && routeError.name !== "AbortError") showSetupError(routeError.message);
    } finally {
      if (generation === setupRequestGeneration) {
        setupRequestActive = false;
        setupAbortController = null;
        submitButton.textContent = "Show route";
        updateSubmitState();
      }
    }
  }

  function reset({ browse = false, notify = true } = {}) {
    cancelPendingSetup();
    destination = null;
    selectedOrigin = "";
    liveOriginInput.checked = false;
    activeTracker = null;
    offRouteDetector = null;
    activeMappedJoin = null;
    rerouteRequestActive = false;
    activeDestinationSummary = null;
    panel.hidden = true;
    setRoutePanelState("setup");
    resetMessages();
    onClear();
    if (notify) onStateChange?.("browsing");
    if (browse) onBrowse?.();
  }

  function renderProgress(progress) {
    const copy = { walking: "Following route", stationary: "Stationary · ETA uses your recent pace",
      "position-uncertain": "Checking your position…", arrived: "You have arrived" };
    const arrivalLabel = activeDestinationSummary?.outdoor_arrival?.label || activeDestinationSummary?.name || "the entrance";
    panel.querySelector("#user-route-progress-status").textContent = progress.state === "arrived"
      ? `You have reached ${arrivalLabel}.` : copy[progress.state];
    panel.querySelector("#user-route-distance").textContent = `${Math.round(progress.remainingDistanceMetres)} m remaining`;
    panel.querySelector("#user-route-eta").textContent = progress.state === "arrived" ? "Arrived" : formatEta(progress.etaSeconds);
    panel.querySelector("#user-route-eta-source").textContent = progress.etaSource === "live"
      ? "ETA from your recent walking pace" : progress.etaSource === "recent"
        ? "ETA from recent pace" : "Approximate ETA at 1.35 m/s";
    if (progress.state === "arrived") setRoutePanelState("arrived", true);
  }

  async function performReroute(position, { manualRetry = false } = {}) {
    if (!activeTracker || !destination || rerouteRequestActive) return false;
    if (!livePositionUsable(position)) {
      panel.querySelector("#user-route-progress-status").textContent = "Refreshing your position before rerouting.";
      return false;
    }
    const originSnapshot = routeOriginSnapshot(position);
    rerouteRequestActive = true;
    retryButton.hidden = true;
    offRouteDetector.markRerouting();
    panel.querySelector("#user-route-progress-status").textContent = "Finding a new route…";
    try {
      const response = await requestLiveRoute(originSnapshot);
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "Unable to calculate a replacement route.");
      const totalDistance = payload.summary.total_distance_metres;
      renderDestinationSummary(payload.summary.destination);
      activeTracker.replaceRoute(payload.route.geometry.coordinates, totalDistance);
      offRouteDetector.markSuccess(originSnapshot.timestamp);
      onRoute(payload.route, null, destination, {
        originType: "live", replacement: true,
        arrivalName: payload.summary.destination.outdoor_arrival?.label || payload.summary.destination.name,
      });
      onRouteStale?.(false);
      panel.querySelector("#user-route-distance").textContent = `${Math.round(totalDistance)} m remaining`;
      panel.querySelector("#user-route-eta").textContent = payload.summary.eta_label;
      panel.querySelector("#user-route-progress-status").textContent = "Route updated · following route";
      return true;
    } catch (rerouteError) {
      offRouteDetector.markFailure();
      onRouteStale?.(true);
      panel.querySelector("#user-route-progress-status").textContent = "Unable to safely reroute from your current position.";
      error.textContent = manualRetry ? rerouteError.message : "Your previous route is retained as reference.";
      error.hidden = false;
      retryButton.hidden = false;
      return false;
    } finally {
      rerouteRequestActive = false;
    }
  }

  function updateLivePosition(position) {
    livePositionRefreshing = false;
    livePosition = position;
    updateLiveOption();
    if (freshStartWait && livePositionUsable(position)) {
      clearFreshStartWait();
      void startLiveRouteRecovery(position);
      return;
    }
    if (liveRecovery && position.timestamp > liveRecovery.lastAttemptTimestamp) {
      if (setupRequestActive) liveRecovery.pendingPosition = position;
      else void attemptLiveRoute(position, liveRecovery);
    }
    // Route-origin freshness is intentionally stricter than progress tracking.
    // Once a route is active, the tracker owns accuracy/age plausibility, but an
    // explicitly retained old coordinate must never advance navigation.
    if (!activeTracker || ["retained", "stale"].includes(position?.freshness)) return;
    if (activeMappedJoin) {
      const joinDistance = distanceMetres(
        [position.longitude, position.latitude], activeMappedJoin.coordinate,
      );
      const joinThreshold = position.accuracyMetres <= 25
        ? Math.min(25, Math.max(12, position.accuracyMetres + 8)) : -1;
      if (joinDistance > joinThreshold) {
        panel.querySelector("#user-route-progress-status").textContent =
          `Walk to ${activeMappedJoin.label} to join the mapped route · ~${Math.round(joinDistance)} m`;
        return;
      }
      activeMappedJoin = null;
      panel.querySelector("#user-route-progress-status").textContent = "Mapped route joined · following route";
    }
    const progress = activeTracker.update(position);
    renderProgress(progress);
    const routeState = offRouteDetector.evaluate(position, activeTracker.getCoordinates(), { arrived: progress.state === "arrived" });
    const trustworthyProgress = ["walking", "stationary", "arrived"].includes(progress.state)
      && ["following", "arrived"].includes(routeState.state) && !routeState.shouldReroute;
    if (trustworthyProgress) onRouteProgress({ progressMetres: progress.progressMetres, state: progress.state });
    if (routeState.state === "checking-position") {
      panel.querySelector("#user-route-progress-status").textContent = routeState.reason === "location-uncertain"
        ? "Location uncertain · retaining your last trustworthy route state" : "Checking your position…";
    } else if (routeState.shouldReroute) {
      panel.querySelector("#user-route-progress-status").textContent = "You appear to be off route";
      void performReroute(position);
    }
  }
  function clearLivePosition({ reacquiring = false } = {}) {
    livePosition = null;
    livePositionRefreshing = reacquiring;
    if (!reacquiring) {
      if (liveRecovery || setupRequestActive) cancelPendingSetup();
      if (selectedOrigin === "__live__") {
        selectedOrigin = "";
        liveOriginInput.checked = false;
        error.hidden = true;
        setRoutePanelState("setup");
      }
    }
    if (freshStartWait) {
      updateLiveOption();
      return;
    }
    // Passive display expiry must not abort a route request that already owns
    // an immutable origin snapshot, nor silently discard the user's choice.
    updateLiveOption();
  }

  form.addEventListener("submit", calculate);
  liveOriginInput.addEventListener("change", () => chooseOrigin("__live__"));
  panel.querySelector("#change-route-origin").addEventListener("click", () => {
    cancelPendingSetup();
    resetMessages();
    formState.hidden = false;
    setRoutePanelState("setup");
    const firstMappedInput = mappedOrigins.children[0]?.children?.[0];
    (liveOriginInput.disabled ? firstMappedInput : liveOriginInput)?.focus();
  });
  panel.querySelector("#change-route-destination").addEventListener("click", () => reset({ browse: true }));
  panel.querySelector("#clear-user-route").addEventListener("click", () => reset());
  panel.querySelector("#close-user-route").addEventListener("click", () => reset());
  detailsToggle?.addEventListener("click", () => {
    setRoutePanelState("active", panel.dataset.detailsExpanded !== "true");
  });
  panel.querySelector("#cancel-user-route").addEventListener("click", () => {
    const cancelledDestination = destination; reset({ notify: false }); if (cancelledDestination) onCancel?.(cancelledDestination);
  });
  retryButton.addEventListener("click", () => {
    if (!livePosition || !offRouteDetector) return;
    offRouteDetector.retry();
    void performReroute(livePosition, { manualRetry: true });
  });
  function suspend() { visibleBeforeSuspend = !panel.hidden; panel.hidden = true; return visibleBeforeSuspend; }
  function resume() { if (visibleBeforeSuspend) panel.hidden = false; const restored = visibleBeforeSuspend; visibleBeforeSuspend = false; return restored; }
  return { begin, reset, updateLivePosition, clearLivePosition, performReroute, suspend, resume };
}
