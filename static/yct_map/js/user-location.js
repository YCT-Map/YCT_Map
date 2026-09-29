import { assessSample, createLocationStabilizer, locationQualityLabel } from "./location-filter.js?v=campus-core-liberty-2";
import { createGeolocationService } from "./geolocation.js?v=campus-core-liberty-2";
import { createDeviceOrientationService, DEVICE_HEADING_STALE_MS,
  selectDisplayedHeading } from "./device-orientation.js?v=campus-core-liberty-2";

const COPY = {
  idle: "Location is optional and stays on this device.",
  unsupported: "Live location is not supported in this browser. Manual directions still work.",
  "requesting-permission": "Allow location access to show your position on the map.",
  locating: "Finding your location…",
  "warming-up": "Location quality improving...",
  active: "Live location active.",
  "low-accuracy": "Location found with limited accuracy.",
  "permission-denied": "Location access was denied. You can still choose a starting point manually.",
  unavailable: "Your location is temporarily unavailable. Try again or use a manual start.",
  "timed-out": "Location is taking too long. Try again or use a manual start.",
  stopped: "Live location stopped. Manual directions remain available.",
  retained: "Location accuracy decreased. Keeping your previous better position.",
};

export function createUserLocation({
  element,
  onPosition,
  onClear,
  onRecenter,
  onHeading = () => {},
  onFollowDirection = () => "following",
  onNorthUp = () => {},
  service = createGeolocationService(),
  orientationService = createDeviceOrientationService(),
  documentObject = globalThis.document,
  now = Date.now,
  setDeadline = globalThis.setTimeout,
  clearDeadline = globalThis.clearTimeout,
} = {}) {
  const locateButton = element.querySelector("#locate-me");
  const recenterButton = element.querySelector("#recenter-me");
  const stopButton = element.querySelector("#stop-location");
  const followButton = element.querySelector("#follow-direction");
  const northUpButton = element.querySelector("#north-up");
  const message = element.querySelector("#location-message");
  const accuracy = element.querySelector("#location-accuracy");
  const directionStatus = element.querySelector("#direction-status");
  let state = service.isSupported ? "idle" : "unsupported";
  let acceptedPosition = null;
  let lastRawAccepted = null;
  const stabilizer = createLocationStabilizer();
  let trackingRequested = false;
  let focusedInitially = false;
  let deviceHeading = null;
  let deviceHeadingTimestamp = null;
  let deviceHeadingExpiry = null;
  let followState = "north-up";

  function currentHeading() {
    return selectDisplayedHeading({ deviceHeading, deviceTimestamp: deviceHeadingTimestamp,
      movementHeading: acceptedPosition?.headingDegrees, now: now() });
  }

  function publishHeading() {
    const displayed = currentHeading();
    directionStatus.textContent = displayed.source === "device" ? "Facing direction active"
      : displayed.source === "movement" ? "Direction from movement" : "Direction unavailable";
    directionStatus.hidden = !acceptedPosition;
    onHeading(displayed);
    return displayed;
  }

  function expireDeviceHeading() {
    deviceHeading = null;
    deviceHeadingTimestamp = null;
    deviceHeadingExpiry = null;
    publishHeading();
  }

  function receiveOrientation(reading) {
    deviceHeading = reading.headingDegrees;
    deviceHeadingTimestamp = reading.timestamp;
    if (deviceHeadingExpiry !== null) clearDeadline(deviceHeadingExpiry);
    deviceHeadingExpiry = setDeadline(expireDeviceHeading, DEVICE_HEADING_STALE_MS + 50);
    publishHeading();
  }

  function setFollowState(nextState) {
    followState = nextState;
    followButton.hidden = !acceptedPosition;
    northUpButton.hidden = !acceptedPosition || nextState === "north-up";
    followButton.textContent = nextState === "suspended" ? "Resume following"
      : nextState === "following" ? "Following direction" : "Follow direction";
    followButton.setAttribute?.("aria-pressed", String(nextState === "following"));
  }

  function render(nextState) {
    state = nextState;
    element.dataset.state = state;
    message.textContent = COPY[state];
    locateButton.hidden = ["requesting-permission", "locating", "warming-up", "active", "low-accuracy", "retained"].includes(state);
    locateButton.disabled = state === "unsupported";
    recenterButton.hidden = !acceptedPosition;
    stopButton.hidden = !trackingRequested;
    accuracy.hidden = !acceptedPosition;
    if (acceptedPosition) {
      const confidence = acceptedPosition.locationConfidence;
      const quality = confidence === "unstable" ? "Position unstable" : confidence === "approximate"
        ? "Approximate location" : `Location quality: ${locationQualityLabel(acceptedPosition.accuracyMetres)}`;
      accuracy.textContent = `${quality} · estimated device uncertainty ~${Math.round(acceptedPosition.deviceAccuracyMetres ?? acceptedPosition.accuracyMetres)} m`;
    }
    setFollowState(followState);
    publishHeading();
  }

  function receive(rawPosition) {
    const result = assessSample(rawPosition, lastRawAccepted);
    if (!result.accepted) {
      if (acceptedPosition && ["poor-accuracy", "keep-better-position"].includes(result.reason)) render("retained");
      else if (!acceptedPosition && ["poor-accuracy", "keep-better-position"].includes(result.reason)) render("locating");
      return result;
    }
    lastRawAccepted = result.sample;
    const stabilized = stabilizer.update(result.sample, result.quality);
    if (!stabilized.ready) {
      render("warming-up");
      return { ...result, displayed: false, stabilization: stabilized.reason };
    }
    acceptedPosition = stabilized.sample;
    const shouldFocus = !focusedInitially && stabilized.quality !== "provisional";
    if (shouldFocus) focusedInitially = true;
    const displayed = currentHeading();
    onPosition({ ...acceptedPosition, displayedHeadingDegrees: displayed.headingDegrees,
      displayedHeadingSource: displayed.source },
    { focus: shouldFocus, quality: stabilized.quality, stabilized: !stabilized.moved });
    render(stabilized.quality === "reasonable" ? "active" : "low-accuracy");
    return { ...result, displayed: true, stabilization: stabilized.reason, sample: acceptedPosition };
  }

  function fail(nextState) {
    if (["unsupported", "permission-denied", "unavailable", "timed-out"].includes(nextState)) {
      if (["unsupported", "permission-denied"].includes(nextState)) trackingRequested = false;
      lastRawAccepted = null;
      stabilizer.reset();
      focusedInitially = false;
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
    // Called directly from the Locate me gesture so permission-gated browsers
    // may display their orientation prompt. Failure never blocks GPS startup.
    void orientationService.start(receiveOrientation, () => publishHeading());
    render("requesting-permission");
    return service.start(
      (position) => { if (!acceptedPosition) render("locating"); receive(position); },
      fail,
    );
  }

  function stop() {
    trackingRequested = false;
    service.stop();
    orientationService.stop();
    if (deviceHeadingExpiry !== null) clearDeadline(deviceHeadingExpiry);
    deviceHeadingExpiry = null;
    deviceHeading = null;
    deviceHeadingTimestamp = null;
    acceptedPosition = null;
    lastRawAccepted = null;
    focusedInitially = false;
    stabilizer.reset();
    onClear();
    setFollowState("north-up");
    render("stopped");
  }

  function visibilityChanged() {
    if (!trackingRequested) return;
    if (documentObject.hidden) {
      service.stop({ preserveCallbacks: true });
      orientationService.pause();
    } else {
      service.resume();
      orientationService.resume();
    }
  }

  locateButton.addEventListener("click", start);
  recenterButton.addEventListener("click", () => acceptedPosition && onRecenter(acceptedPosition));
  followButton.addEventListener("click", () => {
    if (!acceptedPosition) return;
    setFollowState(onFollowDirection(currentHeading()));
  });
  northUpButton.addEventListener("click", () => { onNorthUp(); setFollowState("north-up"); });
  stopButton.addEventListener("click", stop);
  documentObject?.addEventListener?.("visibilitychange", visibilityChanged);
  render(state);

  return {
    start, stop, receive, setFollowState,
    getState: () => state,
    getAcceptedPosition: () => acceptedPosition,
    destroy() {
      service.stop();
      orientationService.destroy();
      if (deviceHeadingExpiry !== null) clearDeadline(deviceHeadingExpiry);
      documentObject?.removeEventListener?.("visibilitychange", visibilityChanged);
    },
  };
}
