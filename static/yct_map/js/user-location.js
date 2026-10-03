import { assessSample, createLocationStabilizer, locationQualityLabel } from "./location-filter.js?v=final-web-closeout-1";
import { createGeolocationService } from "./geolocation.js?v=final-web-closeout-1";
import { createDeviceOrientationService, DEVICE_HEADING_STALE_MS,
  createHeadingOppositionDiagnostic, headingDiagnosticSnapshot, screenOrientationDegrees,
  selectDisplayedHeading } from "./device-orientation.js?v=final-web-closeout-1";

export const INITIAL_LOCATION_ACQUISITION_MAX_MS = 10_000;

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
  retained: "Location quality reduced · retaining the last reliable position.",
  "outside-area": "You’re outside the YabaTech mapping area.",
};

export function createUserLocation({
  element,
  onPosition,
  onClear,
  onRecenter,
  onHeading = () => {},
  service = createGeolocationService(),
  orientationService = createDeviceOrientationService(),
  documentObject = globalThis.document,
  now = Date.now,
  setDeadline = globalThis.setTimeout,
  clearDeadline = globalThis.clearTimeout,
  supportedArea = null,
  getMapBearing = () => 0,
  screenObject = globalThis.screen,
} = {}) {
  const locateButton = element.querySelector("#locate-me");
  const recenterButton = element.querySelector("#recenter-me");
  const stopButton = element.querySelector("#stop-location");
  const message = element.querySelector("#location-message");
  const accuracy = element.querySelector("#location-accuracy");
  const directionStatus = element.querySelector("#direction-status");
  let state = service.isSupported ? "idle" : "unsupported";
  let acceptedPosition = null;
  let lastRawAccepted = null;
  const stabilizer = createLocationStabilizer({ warmupMinimumSpanMs: 3_000 });
  let trackingRequested = false;
  let focusedInitially = false;
  let deviceHeading = null;
  let deviceHeadingTimestamp = null;
  let deviceHeadingExpiry = null;
  let acquisitionDeadline = null;
  const headingOpposition = createHeadingOppositionDiagnostic();

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
      const quality = `Location quality: ${locationQualityLabel(acceptedPosition.accuracyMetres)}`;
      const confidenceCopy = confidence === "unstable" ? " · position unstable" : "";
      accuracy.textContent = `${quality}${confidenceCopy} · estimated uncertainty ~${Math.round(acceptedPosition.deviceAccuracyMetres ?? acceptedPosition.accuracyMetres)} m`;
    }
    publishHeading();
  }

  function clearAcquisitionDeadline() {
    if (acquisitionDeadline !== null) clearDeadline(acquisitionDeadline);
    acquisitionDeadline = null;
  }

  function publishStabilized(stabilized) {
    if (!stabilized?.ready || !stabilized.sample) return false;
    if (supportedArea && !supportedArea.contains(stabilized.sample)) {
      clearAcquisitionDeadline();
      acceptedPosition = null;
      lastRawAccepted = null;
      stabilizer.reset();
      focusedInitially = false;
      onClear();
      render("outside-area");
      return false;
    }
    if (stabilized.reason === "keep-better-position") {
      acceptedPosition = stabilized.sample;
      render("retained");
      return false;
    }
    clearAcquisitionDeadline();
    acceptedPosition = stabilized.sample;
    headingOpposition.update({
      deviceHeading,
      movementHeading: acceptedPosition.headingDegrees,
      speedMetresPerSecond: acceptedPosition.speedMetresPerSecond,
    });
    const shouldFocus = !focusedInitially && stabilized.quality !== "provisional";
    if (shouldFocus) focusedInitially = true;
    const displayed = currentHeading();
    onPosition({ ...acceptedPosition, displayedHeadingDegrees: displayed.headingDegrees,
      displayedHeadingSource: displayed.source },
    { focus: shouldFocus, quality: stabilized.quality, stabilized: !stabilized.moved,
      motionState: stabilized.motionState });
    render(stabilized.quality === "reasonable" ? "active" : "low-accuracy");
    return true;
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
    const displayed = publishStabilized(stabilized);
    return { ...result, displayed, stabilization: stabilized.reason,
      sample: displayed ? acceptedPosition : stabilized.sample };
  }

  function finishInitialAcquisition() {
    acquisitionDeadline = null;
    if (acceptedPosition || !trackingRequested) return;
    const stabilized = stabilizer.finalize();
    if (!publishStabilized(stabilized) && state !== "outside-area") render("timed-out");
  }

  function fail(nextState) {
    if (["unsupported", "permission-denied", "unavailable", "timed-out", "outside-area"].includes(nextState)) {
      clearAcquisitionDeadline();
      if (["unsupported", "permission-denied"].includes(nextState)) trackingRequested = false;
      lastRawAccepted = null;
      stabilizer.reset();
      headingOpposition.reset();
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
    clearAcquisitionDeadline();
    acquisitionDeadline = setDeadline(finishInitialAcquisition, INITIAL_LOCATION_ACQUISITION_MAX_MS);
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
    clearAcquisitionDeadline();
    deviceHeadingExpiry = null;
    deviceHeading = null;
    deviceHeadingTimestamp = null;
    acceptedPosition = null;
    lastRawAccepted = null;
    focusedInitially = false;
    stabilizer.reset();
    headingOpposition.reset();
    onClear();
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
  stopButton.addEventListener("click", stop);
  documentObject?.addEventListener?.("visibilitychange", visibilityChanged);
  render(state);

  return {
    start, stop, receive,
    getState: () => state,
    getAcceptedPosition: () => acceptedPosition,
    getHeadingDiagnostic() {
      const selected = currentHeading();
      const orientation = orientationService.getDiagnostic?.() || {};
      return {
        ...headingDiagnosticSnapshot({
          rawOrientation: orientation.rawOrientation || null,
          deviceHeading,
          deviceTimestamp: deviceHeadingTimestamp,
          movementHeading: acceptedPosition?.headingDegrees,
          selected,
          screenAngle: screenOrientationDegrees(screenObject),
          mapBearing: getMapBearing(),
          now: now(),
        }),
        ...headingOpposition.getState(),
      };
    },
    destroy() {
      service.stop();
      orientationService.destroy();
      if (deviceHeadingExpiry !== null) clearDeadline(deviceHeadingExpiry);
      clearAcquisitionDeadline();
      documentObject?.removeEventListener?.("visibilitychange", visibilityChanged);
    },
  };
}
