import { createLiveRouteTracker, formatEta } from "./live-route-progress.js?v=checkpoint-flex-nav-1";
import { createOffRouteDetector } from "./off-route.js?v=checkpoint-flex-nav-1";

export const MAX_LIVE_POSITION_AGE_MS = 30_000;
export const MAX_LIVE_ROUTE_ATTEMPTS = 3;
export const LIVE_ROUTE_RECOVERY_WINDOW_MS = 10_000;
const TRANSIENT_LIVE_ROUTE_CODES = new Set(["NO_SAFE_NETWORK_MATCH", "INSUFFICIENT_ACCURACY"]);
const LIVE_ROUTE_FINAL_MESSAGE = "Your location is clear, but it cannot yet be safely connected to the mapped campus paths. Choose a mapped starting point or try live location again after moving closer to a mapped walkway.";

export function createUserNavigation({ panel, features, routeUrl, liveRouteUrl, onRoute, onClear, onBrowse,
  onCancel, onStateChange, onRouteStale, onRouteProgress = () => {}, requestRoute = fetch, now = Date.now,
  setDeadline = globalThis.setTimeout, clearDeadline = globalThis.clearTimeout }) {
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
  let liveOptionSignature = "";

  const csrfToken = () => document.cookie.split("; ").find((row) => row.startsWith("csrftoken="))?.split("=")[1] || "";
  function livePositionUsable(position = livePosition) {
    if (!position || position.accuracyMetres > 40 || !Number.isFinite(position.timestamp)) return false;
    const age = now() - position.timestamp;
    return age >= -5_000 && age <= MAX_LIVE_POSITION_AGE_MS;
  }
  function updateLiveOption() {
    const usable = livePositionUsable();
    const stale = Boolean(livePosition) && !usable;
    const status = usable ? `Live location ready Â· ~${Math.round(livePosition.accuracyMetres)} m`
      : stale ? "Waiting for a current location" : "Locate first";
    const signature = `${usable}:${status}`;
    if (signature !== liveOptionSignature) {
      liveOriginInput.disabled = !usable;
      liveOriginStatus.textContent = status;
      liveOptionSignature = signature;
    }
    updateSubmitState();
  }
  function updateSubmitState() {
    submitButton.disabled = setupRequestActive || Boolean(liveRecovery) || !selectedOrigin
      || (selectedOrigin === "__live__" && !livePositionUsable());
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
  function cancelPendingSetup() {
    setupRequestGeneration += 1;
    setupAbortController?.abort();
    setupAbortController = null;
    setupRequestActive = false;
    clearRecoveryTimer();
    liveRecovery = null;
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
    retryButton.hidden = true;
    const firstMappedInput = mappedOrigins.children[0]?.children?.[0];
    (liveOriginInput.disabled ? firstMappedInput : liveOriginInput)?.focus();
    onStateChange?.("choosing-origin");
    return true;
  }

  function activateRoute(payload, { useLive, origin }) {
    const totalDistance = payload.summary.total_distance_metres ?? payload.summary.distance_metres;
    panel.querySelector("#user-route-from").textContent = payload.summary.origin.name;
    renderDestinationSummary(payload.summary.destination);
    panel.querySelector("#user-route-distance").textContent = `${Math.round(totalDistance)} m`;
    panel.querySelector("#user-route-eta").textContent = payload.summary.eta_label;
    panel.querySelector("#user-route-progress-status").hidden = !useLive;
    panel.querySelector("#user-route-progress-status").textContent = "Live route active · waiting for movement";
    panel.querySelector("#user-route-eta-source").textContent = useLive ? "Approximate ETA at 1.35 m/s" : "";
    panel.querySelector("#user-route-data-notice").textContent =
      "OSM-derived route geometry is UNVERIFIED and is not field-verified campus navigation.";
    formState.hidden = true;
    result.hidden = false;
    requestStatus.hidden = true;
    requestStatus.textContent = "";
    setRoutePanelState("active", false);
    activeTracker = useLive ? createLiveRouteTracker(payload.route.geometry.coordinates, totalDistance) : null;
    offRouteDetector = useLive ? createOffRouteDetector() : null;
    retryButton.hidden = true;
    onRouteStale?.(false);
    onRoute(payload.route, origin, destination, {
      originType: useLive ? "live" : "manual",
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

  async function attemptLiveRoute(position, recovery) {
    if (liveRecovery !== recovery || setupRequestActive || !livePositionUsable(position)
        || position.timestamp <= recovery.lastAttemptTimestamp) return false;
    if (recovery.attempts >= MAX_LIVE_ROUTE_ATTEMPTS
        || now() - recovery.startedAt > LIVE_ROUTE_RECOVERY_WINDOW_MS) {
      finishLiveRecovery(recovery);
      return false;
    }
    recovery.pendingPosition = null;
    recovery.lastAttemptTimestamp = position.timestamp;
    recovery.attempts += 1;
    setupRequestActive = true;
    setupAbortController = new AbortController();
    error.hidden = true;
    showSetupActivity(recovery.attempts === 1 ? "Calculating route…" : "Checking a newer live position…");
    try {
      const response = await requestLiveRoute(position, { signal: setupAbortController.signal });
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
      showSetupError("Your live position is no longer current. Use Locate me again or choose a mapped start.");
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
    rerouteRequestActive = true;
    retryButton.hidden = true;
    offRouteDetector.markRerouting();
    panel.querySelector("#user-route-progress-status").textContent = "Finding a new route…";
    try {
      const response = await requestLiveRoute(position);
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "Unable to calculate a replacement route.");
      const totalDistance = payload.summary.total_distance_metres;
      renderDestinationSummary(payload.summary.destination);
      activeTracker.replaceRoute(payload.route.geometry.coordinates, totalDistance);
      offRouteDetector.markSuccess(position.timestamp);
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
    livePosition = position;
    updateLiveOption();
    if (liveRecovery && position.timestamp > liveRecovery.lastAttemptTimestamp) {
      if (setupRequestActive) liveRecovery.pendingPosition = position;
      else void attemptLiveRoute(position, liveRecovery);
    }
    if (!activeTracker) return;
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
  function clearLivePosition() {
    livePosition = null;
    if (liveRecovery || setupRequestActive) cancelPendingSetup();
    if (selectedOrigin === "__live__") {
      selectedOrigin = "";
      liveOriginInput.checked = false;
      error.hidden = true;
      setRoutePanelState("setup");
    }
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
