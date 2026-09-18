import { assessSample } from "./location-filter.js?v=p3s1-live-location-1";
import { createGeolocationService } from "./geolocation.js?v=p3s1-live-location-1";

const COPY = {
  idle: "Location is optional and stays on this device.",
  unsupported: "Live location is not supported in this browser. Manual directions still work.",
  "requesting-permission": "Allow location access to show your position on the map.",
  locating: "Finding your location…",
  active: "Live location active.",
  "low-accuracy": "Location found with limited accuracy.",
  "permission-denied": "Location access was denied. You can still choose a starting point manually.",
  unavailable: "Your location is temporarily unavailable. Try again or use a manual start.",
  "timed-out": "Location is taking too long. Try again or use a manual start.",
  stopped: "Live location stopped. Manual directions remain available.",
};

export function createUserLocation({
  element,
  onPosition,
  onClear,
  onRecenter,
  service = createGeolocationService(),
  documentObject = globalThis.document,
} = {}) {
  const locateButton = element.querySelector("#locate-me");
  const recenterButton = element.querySelector("#recenter-me");
  const stopButton = element.querySelector("#stop-location");
  const message = element.querySelector("#location-message");
  const accuracy = element.querySelector("#location-accuracy");
  let state = service.isSupported ? "idle" : "unsupported";
  let acceptedPosition = null;
  let trackingRequested = false;
  let focusedInitially = false;

  function render(nextState) {
    state = nextState;
    element.dataset.state = state;
    message.textContent = COPY[state];
    locateButton.hidden = ["requesting-permission", "locating", "active", "low-accuracy"].includes(state);
    locateButton.disabled = state === "unsupported";
    recenterButton.hidden = !acceptedPosition;
    stopButton.hidden = !trackingRequested;
    accuracy.hidden = !acceptedPosition;
    if (acceptedPosition) accuracy.textContent = `Accuracy approximately ${Math.round(acceptedPosition.accuracyMetres)} m`;
  }

  function receive(rawPosition) {
    const result = assessSample(rawPosition, acceptedPosition);
    if (!result.accepted) {
      if (!acceptedPosition && ["poor-accuracy", "keep-better-position"].includes(result.reason)) render("locating");
      return result;
    }
    acceptedPosition = result.sample;
    const shouldFocus = !focusedInitially && result.quality !== "provisional";
    if (shouldFocus) focusedInitially = true;
    onPosition(acceptedPosition, { focus: shouldFocus, quality: result.quality });
    render(result.quality === "reasonable" ? "active" : "low-accuracy");
    return result;
  }

  function fail(nextState) {
    if (nextState === "unsupported" || nextState === "permission-denied") {
      trackingRequested = false;
      if (acceptedPosition) {
        acceptedPosition = null;
        onClear();
      }
    }
    render(nextState);
  }

  function start() {
    if (!service.isSupported) {
      render("unsupported");
      return false;
    }
    trackingRequested = true;
    render("requesting-permission");
    const started = service.start(
      (position) => {
        if (!acceptedPosition) render("locating");
        receive(position);
      },
      fail,
    );
    return started;
  }

  function stop() {
    trackingRequested = false;
    service.stop();
    acceptedPosition = null;
    focusedInitially = false;
    onClear();
    render("stopped");
  }

  function visibilityChanged() {
    if (!trackingRequested) return;
    if (documentObject.hidden) service.stop({ preserveCallbacks: true });
    else service.resume();
  }

  locateButton.addEventListener("click", start);
  recenterButton.addEventListener("click", () => acceptedPosition && onRecenter(acceptedPosition));
  stopButton.addEventListener("click", stop);
  documentObject?.addEventListener?.("visibilitychange", visibilityChanged);
  render(state);

  return {
    start,
    stop,
    receive,
    getState: () => state,
    getAcceptedPosition: () => acceptedPosition,
    destroy() {
      service.stop();
      documentObject?.removeEventListener?.("visibilitychange", visibilityChanged);
    },
  };
}
