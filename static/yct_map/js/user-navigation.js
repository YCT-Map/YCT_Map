import { createLiveRouteTracker, formatEta } from "./live-route-progress.js?v=p3s2-live-route-1";

export function createUserNavigation({ panel, features, routeUrl, liveRouteUrl, onRoute, onClear, onBrowse,
  onCancel, onStateChange, requestRoute = fetch }) {
  const form = panel.querySelector("#user-route-form");
  const originSelect = panel.querySelector("#user-route-origin");
  const destinationName = panel.querySelector("#user-route-destination");
  const submitButton = panel.querySelector("#show-user-route");
  const error = panel.querySelector("#user-route-error");
  const result = panel.querySelector("#user-route-result");
  const formState = panel.querySelector("#user-route-form-state");
  let destination = null;
  let livePosition = null;
  let activeTracker = null;

  const csrfToken = () => document.cookie.split("; ").find((row) => row.startsWith("csrftoken="))?.split("=")[1] || "";
  const liveOption = () => [...originSelect.options].find((option) => option.value === "__live__");
  function updateLiveOption() {
    const option = liveOption();
    if (!option) return;
    option.disabled = !livePosition || livePosition.accuracyMetres > 40;
    option.textContent = option.disabled ? "Use my location (locate first)" : "Use my live location";
  }
  function resetMessages() { error.hidden = true; result.hidden = true; }

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
    panel.hidden = false;
    submitButton.disabled = true;
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
    resetMessages();
    submitButton.disabled = true;
    submitButton.textContent = "Calculating…";
    const useLive = originSelect.value === "__live__";
    try {
      let response;
      if (useLive) {
        response = await requestRoute(liveRouteUrl, { method: "POST", headers: {
          Accept: "application/json", "Content-Type": "application/json", "X-CSRFToken": csrfToken(),
        }, body: JSON.stringify({ destination: destination.properties.id, position: {
          latitude: livePosition.latitude, longitude: livePosition.longitude, accuracy_metres: livePosition.accuracyMetres,
        } }) });
      } else {
        const parameters = new URLSearchParams({ origin: originSelect.value, destination: destination.properties.id });
        response = await requestRoute(`${routeUrl}?${parameters}`, { headers: { Accept: "application/json" } });
      }
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "No route is available.");
      const origin = useLive ? null : features.find((item) => item.properties.id === originSelect.value);
      const totalDistance = payload.summary.total_distance_metres ?? payload.summary.distance_metres;
      panel.querySelector("#user-route-from").textContent = payload.summary.origin.name;
      panel.querySelector("#user-route-to").textContent = payload.summary.destination.name;
      panel.querySelector("#user-route-distance").textContent = `${Math.round(totalDistance)} m`;
      panel.querySelector("#user-route-eta").textContent = payload.summary.eta_label;
      panel.querySelector("#user-route-progress-status").hidden = !useLive;
      panel.querySelector("#user-route-progress-status").textContent = "Live route active · waiting for movement";
      panel.querySelector("#user-route-eta-source").textContent = useLive ? "Approximate ETA at 1.35 m/s" : "";
      panel.querySelector("#user-route-data-notice").textContent =
        "DEMO destinations with OSM-derived UNVERIFIED route geometry — not field-verified campus navigation.";
      formState.hidden = true;
      result.hidden = false;
      activeTracker = useLive ? createLiveRouteTracker(payload.route.geometry.coordinates, totalDistance) : null;
      onRoute(payload.route, origin, destination, { originType: useLive ? "live" : "manual" });
      onStateChange?.("route-available");
    } catch (routeError) {
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
    panel.hidden = true;
    resetMessages();
    onClear();
    if (notify) onStateChange?.("browsing");
    if (browse) onBrowse?.();
  }

  function updateLivePosition(position) {
    livePosition = position;
    updateLiveOption();
    if (!activeTracker) return;
    const progress = activeTracker.update(position);
    const copy = { walking: "Following live route", stationary: "Stationary · ETA uses your recent pace",
      "position-uncertain": "Position uncertain · retaining stable route progress", arrived: "You have arrived" };
    panel.querySelector("#user-route-progress-status").textContent = copy[progress.state];
    panel.querySelector("#user-route-distance").textContent = `${Math.round(progress.remainingDistanceMetres)} m remaining`;
    panel.querySelector("#user-route-eta").textContent = progress.state === "arrived" ? "Arrived" : formatEta(progress.etaSeconds);
    panel.querySelector("#user-route-eta-source").textContent = progress.etaSource === "live"
      ? "ETA from your recent walking pace" : progress.etaSource === "recent"
        ? "ETA from recent pace" : "Approximate ETA at 1.35 m/s";
  }
  function clearLivePosition() { livePosition = null; updateLiveOption(); }

  form.addEventListener("submit", calculate);
  originSelect.addEventListener("change", () => { submitButton.disabled = !originSelect.value; });
  panel.querySelector("#change-route-origin").addEventListener("click", () => { result.hidden = true; formState.hidden = false; originSelect.focus(); });
  panel.querySelector("#change-route-destination").addEventListener("click", () => reset({ browse: true }));
  panel.querySelector("#clear-user-route").addEventListener("click", () => reset());
  panel.querySelector("#close-user-route").addEventListener("click", () => reset());
  panel.querySelector("#cancel-user-route").addEventListener("click", () => {
    const cancelledDestination = destination; reset({ notify: false }); if (cancelledDestination) onCancel?.(cancelledDestination);
  });
  return { begin, reset, updateLivePosition, clearLivePosition };
}
