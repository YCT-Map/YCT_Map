import { createLiveRouteTracker, formatEta } from "./live-route-progress.js?v=p4-predeploy-1";
import { createOffRouteDetector } from "./off-route.js?v=p4-predeploy-1";

export const MAX_LIVE_POSITION_AGE_MS = 30_000;

export function createUserNavigation({ panel, features, routeUrl, liveRouteUrl, onRoute, onClear, onBrowse,
  onCancel, onStateChange, onRouteStale, requestRoute = fetch, now = Date.now }) {
  const form = panel.querySelector("#user-route-form");
  const originSelect = panel.querySelector("#user-route-origin");
  const destinationName = panel.querySelector("#user-route-destination");
  const summaryDestinationName = panel.querySelector("#user-route-summary-destination");
  const submitButton = panel.querySelector("#show-user-route");
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

  const csrfToken = () => document.cookie.split("; ").find((row) => row.startsWith("csrftoken="))?.split("=")[1] || "";
  const liveOption = () => [...originSelect.options].find((option) => option.value === "__live__");
  function livePositionUsable() {
    if (!livePosition || livePosition.accuracyMetres > 40 || !Number.isFinite(livePosition.timestamp)) return false;
    const age = now() - livePosition.timestamp;
    return age >= -5_000 && age <= MAX_LIVE_POSITION_AGE_MS;
  }
  function updateLiveOption() {
    const option = liveOption();
    if (!option) return;
    option.disabled = !livePositionUsable();
    option.textContent = option.disabled ? "Use my location (locate first)" : "Use my live location";
  }
  function resetMessages() { error.hidden = true; result.hidden = true; }
  function setRoutePanelState(state, expanded = false) {
    panel.dataset.routeState = state;
    panel.dataset.detailsExpanded = String(expanded);
    detailsToggle?.setAttribute("aria-expanded", String(expanded));
  }
  function requestLiveRoute(position) {
    return requestRoute(liveRouteUrl, { method: "POST", headers: {
      Accept: "application/json", "Content-Type": "application/json", "X-CSRFToken": csrfToken(),
    }, body: JSON.stringify({ destination: destination.properties.destination_key || destination.properties.id, position: {
      latitude: position.latitude, longitude: position.longitude, accuracy_metres: position.accuracyMetres,
    } }) });
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
    destination = feature;
    destinationName.textContent = feature.properties.name;
    originSelect.replaceChildren();
    const placeholder = originSelect.ownerDocument.createElement("option");
    Object.assign(placeholder, { value: "", textContent: "Select starting point", disabled: true, selected: true });
    originSelect.append(placeholder);
    const locationOption = originSelect.ownerDocument.createElement("option");
    locationOption.value = "__live__";
    originSelect.append(locationOption);
    updateLiveOption();
    for (const candidate of features.filter((item) => item.properties.routing_available === true
      && item.properties.id !== feature.properties.id)) {
      const option = originSelect.ownerDocument.createElement("option");
      option.value = candidate.properties.id;
      option.textContent = candidate.properties.name;
      originSelect.append(option);
    }
    resetMessages();
    formState.hidden = false;
    setRoutePanelState("setup");
    panel.hidden = false;
    submitButton.disabled = true;
    retryButton.hidden = true;
    originSelect.focus();
    onStateChange?.("choosing-origin");
    return true;
  }

  async function calculate(event) {
    event.preventDefault();
    if (!destination || !originSelect.value) {
      error.textContent = "Choose a starting point.";
      error.hidden = false;
      return;
    }
    const useLive = originSelect.value === "__live__";
    if (useLive && !livePositionUsable()) {
      updateLiveOption();
      error.textContent = "Your live position is no longer current. Use Locate me again or choose a manual start.";
      error.hidden = false;
      return;
    }
    resetMessages();
    submitButton.disabled = true;
    submitButton.textContent = "Calculating…";
    setRoutePanelState("loading");
    try {
      let response;
      if (useLive) response = await requestLiveRoute(livePosition);
      else {
        const parameters = new URLSearchParams({ origin: originSelect.value, destination: destination.properties.destination_key || destination.properties.id });
        response = await requestRoute(`${routeUrl}?${parameters}`, { headers: { Accept: "application/json" } });
      }
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "No route is available.");
      const origin = useLive ? null : features.find((item) => item.properties.id === originSelect.value);
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
    } catch (routeError) {
      setRoutePanelState("error", true);
      error.textContent = routeError.message;
      error.hidden = false;
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Show route";
    }
  }

  function reset({ browse = false, notify = true } = {}) {
    destination = null;
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
    if (!activeTracker) return;
    const progress = activeTracker.update(position);
    renderProgress(progress);
    const routeState = offRouteDetector.evaluate(position, activeTracker.getCoordinates(), { arrived: progress.state === "arrived" });
    if (routeState.state === "checking-position") {
      panel.querySelector("#user-route-progress-status").textContent = routeState.reason === "location-uncertain"
        ? "Location uncertain · retaining your last trustworthy route state" : "Checking your position…";
    } else if (routeState.shouldReroute) {
      panel.querySelector("#user-route-progress-status").textContent = "You appear to be off route";
      void performReroute(position);
    }
  }
  function clearLivePosition() { livePosition = null; updateLiveOption(); }

  form.addEventListener("submit", calculate);
  originSelect.addEventListener("change", () => { submitButton.disabled = !originSelect.value; });
  panel.querySelector("#change-route-origin").addEventListener("click", () => { result.hidden = true; formState.hidden = false; setRoutePanelState("setup"); originSelect.focus(); });
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
