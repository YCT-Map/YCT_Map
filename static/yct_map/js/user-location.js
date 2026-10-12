import { accuracyState, assessSample, createLocationStabilizer, locationQualityLabel } from "./location-filter.js?v=location-reliability-1";
import { createGeolocationService } from "./geolocation.js?v=location-reliability-1";
import { createDeviceOrientationService, DEVICE_HEADING_STALE_MS,
  createHeadingOppositionDiagnostic, headingDiagnosticSnapshot, screenOrientationDegrees,
  selectDisplayedHeading } from "./device-orientation.js?v=location-reliability-1";

export const INITIAL_LOCATION_ACQUISITION_MAX_MS = 20_000;
export const LIVE_LOCATION_STALE_AFTER_MS = 30_000;
export const LIVE_LOCATION_RESUME_REACQUIRE_MS = 30_000;

const COPY = {
  idle: "Location is optional and stays on this device.",
  unsupported: "Live location is not supported in this browser. Manual directions still work.",
  "requesting-permission": "Allow location access to show your position on the map.",
  locating: "Finding your location…",
  "warming-up": "Location quality improving...",
  retrying: "GPS is temporarily unavailable. Still trying for a fresh position...",
  "needs-precision": "Precise location is not confirmed yet. Move outdoors or enable Precise location; still trying.",
  active: "Live location active.",
  "low-accuracy": "Approximate position only. Live routing is waiting for better accuracy.",
  "permission-denied": "Location access was denied. You can still choose a starting point manually.",
  unavailable: "Your location is temporarily unavailable. Try again or use a manual start.",
  "timed-out": "Location is taking too long. Try again or use a manual start.",
  refreshing: "Refreshing your location...",
  stopped: "Live location stopped. Manual directions remain available.",
  retained: "Location stable · using a recent reliable position.",
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
  let freshnessDeadline = null;
  let reacquisitionActive = false;
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
    locateButton.hidden = ["requesting-permission", "locating", "warming-up", "retrying",
      "needs-precision", "active", "low-accuracy", "retained", "refreshing"].includes(state);
    locateButton.disabled = state === "unsupported";
    recenterButton.hidden = !acceptedPosition;
    stopButton.hidden = !trackingRequested;
    accuracy.hidden = !acceptedPosition;
    if (acceptedPosition) {
      const confidence = acceptedPosition.locationConfidence;
      const confidenceCopy = confidence === "unstable" ? " · position unstable" : "";
      const uncertainty = Math.round(acceptedPosition.deviceAccuracyMetres ?? acceptedPosition.accuracyMetres);
      accuracy.textContent = acceptedPosition.freshness === "retained"
        ? `Recent reliable position · estimated uncertainty ~${uncertainty} m`
        : `Location quality: ${locationQualityLabel(acceptedPosition.accuracyMetres)}${confidenceCopy} · estimated uncertainty ~${uncertainty} m`;
    }
    publishHeading();
  }

  function clearAcquisitionDeadline() {
    if (acquisitionDeadline !== null) clearDeadline(acquisitionDeadline);
    acquisitionDeadline = null;
  }

  function clearFreshnessDeadline() {
    if (freshnessDeadline !== null) clearDeadline(freshnessDeadline);
    freshnessDeadline = null;
  }

  function startAcquisitionDeadline() {
    clearAcquisitionDeadline();
    acquisitionDeadline = setDeadline(finishInitialAcquisition, INITIAL_LOCATION_ACQUISITION_MAX_MS);
  }

  function scheduleFreshnessExpiry() {
    clearFreshnessDeadline();
    if (!trackingRequested || !acceptedPosition) return;
    const age = Math.max(0, now() - acceptedPosition.timestamp);
    freshnessDeadline = setDeadline(expireDisplayedPosition,
      Math.max(0, LIVE_LOCATION_STALE_AFTER_MS - age));
  }

  function notifyPosition(position, stabilized, { focus = false } = {}) {
    const displayed = currentHeading();
    onPosition({ ...position, displayedHeadingDegrees: displayed.headingDegrees,
      displayedHeadingSource: displayed.source },
    { focus, quality: stabilized.quality, stabilized: !stabilized.moved,
      motionState: stabilized.motionState, freshness: stabilized.freshness });
  }

  function navigationReady(stabilized, position = stabilized?.sample) {
    return Boolean(position) && stabilized?.quality === "reasonable" &&
      stabilized?.confidence !== "unstable";
  }

  function resetAcquisitionEvidence() {
    lastRawAccepted = null;
    stabilizer.reset();
    headingOpposition.reset();
  }

  function publishRetained(stabilized) {
    reacquisitionActive = false;
    clearAcquisitionDeadline();
    acceptedPosition = { ...stabilized.sample, freshness: "retained",
      retainedAgeMs: stabilized.retainedAgeMs,
      navigationReady: stabilized.sample.navigationReady ?? navigationReady(stabilized) };
    notifyPosition(acceptedPosition, stabilized);
    scheduleFreshnessExpiry();
    render("retained");
    return false;
  }

  function publishStabilized(stabilized) {
    if (!stabilized?.ready || !stabilized.sample) return false;
    if (supportedArea && !supportedArea.contains(stabilized.sample)) {
      clearAcquisitionDeadline();
      acceptedPosition = null;
      lastRawAccepted = null;
      stabilizer.reset();
      focusedInitially = false;
      onClear({ reason: "outside-area", reacquiring: false });
      render("outside-area");
      return false;
    }
    if (stabilized.freshness === "retained" ||
        ["keep-better-position", "checking-movement"].includes(stabilized.reason)) {
      return publishRetained(stabilized);
    }
    clearAcquisitionDeadline();
    reacquisitionActive = false;
    acceptedPosition = { ...stabilized.sample, freshness: "fresh",
      navigationReady: navigationReady(stabilized), supportedAreaValid: true };
    headingOpposition.update({
      deviceHeading,
      movementHeading: acceptedPosition.headingDegrees,
      speedMetresPerSecond: acceptedPosition.speedMetresPerSecond,
    });
    const shouldFocus = !focusedInitially && acceptedPosition.navigationReady;
    if (shouldFocus) focusedInitially = true;
    notifyPosition(acceptedPosition, stabilized, { focus: shouldFocus });
    scheduleFreshnessExpiry();
    render(stabilized.quality === "reasonable" ? "active" : "low-accuracy");
    return true;
  }

  function receive(rawPosition) {
    const result = assessSample(rawPosition, lastRawAccepted, { currentTime: now() });
    if (!result.accepted) {
      if (acceptedPosition && result.reason === "poor-accuracy") {
        publishRetained({ ready: true, reason: "keep-better-position",
          sample: acceptedPosition, quality: accuracyState(acceptedPosition.accuracyMetres),
          freshness: "retained", retainedAgeMs: Math.max(0, result.sample.timestamp - acceptedPosition.timestamp),
          moved: false, motionState: acceptedPosition.motionState || "stationary" });
      }
      else if (!acceptedPosition && ["poor-accuracy", "keep-better-position", "stale"].includes(result.reason)) {
        render(state === "needs-precision" ? "needs-precision" : "warming-up");
      }
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
    if (reacquisitionActive) {
      reacquisitionActive = false;
      if (acceptedPosition) {
        scheduleFreshnessExpiry();
        render("retained");
      } else {
        render("needs-precision");
      }
      return;
    }
    if (acceptedPosition || !trackingRequested) return;
    render("needs-precision");
  }

  function restartFreshAcquisition({ preserveDisplayed = true, hardReset = !preserveDisplayed,
    notifyClear = true, clearReason = "refreshing" } = {}) {
    if (!trackingRequested) return false;
    if (reacquisitionActive) return true;
    reacquisitionActive = true;
    const previousPosition = acceptedPosition;
    focusedInitially = preserveDisplayed && Boolean(previousPosition);
    if (hardReset) {
      acceptedPosition = null;
      focusedInitially = false;
      resetAcquisitionEvidence();
      if (notifyClear) onClear({ reason: clearReason, reacquiring: true });
    } else if (previousPosition && preserveDisplayed) {
      acceptedPosition = { ...acceptedPosition, freshness: "retained" };
      notifyPosition(acceptedPosition, {
        quality: accuracyState(acceptedPosition.accuracyMetres), moved: false,
        motionState: acceptedPosition.motionState || "stationary", freshness: "retained",
      });
      scheduleFreshnessExpiry();
    } else if (!preserveDisplayed) {
      acceptedPosition = null;
      if (notifyClear) onClear({ reason: clearReason, reacquiring: true });
    }
    render("refreshing");
    startAcquisitionDeadline();
    const restarted = service.reacquire?.();
    if (restarted === undefined) service.resume?.();
    if (restarted === false) {
      reacquisitionActive = false;
      fail("unavailable");
    }
    return restarted !== false;
  }

  function expireDisplayedPosition() {
    freshnessDeadline = null;
    if (!trackingRequested || !acceptedPosition) return;
    const age = Math.max(0, now() - acceptedPosition.timestamp);
    if (age < LIVE_LOCATION_STALE_AFTER_MS) {
      scheduleFreshnessExpiry();
      return;
    }
    acceptedPosition = null;
    focusedInitially = false;
    onClear({ reason: "stale", reacquiring: true });
    restartFreshAcquisition({ preserveDisplayed: false, hardReset: true,
      notifyClear: false, clearReason: "stale" });
  }

  function receiveServiceError(nextState, details = {}) {
    if (["permission-denied", "unsupported"].includes(nextState) || !details.willRetry) {
      fail(nextState);
      return;
    }
    if (!trackingRequested) return;
    if (acceptedPosition) {
      acceptedPosition = { ...acceptedPosition, freshness: "retained" };
      scheduleFreshnessExpiry();
      render("retained");
    } else {
      render("retrying");
    }
  }

  function fail(nextState) {
    if (["unsupported", "permission-denied", "unavailable", "timed-out", "outside-area"].includes(nextState)) {
      clearAcquisitionDeadline();
      clearFreshnessDeadline();
      reacquisitionActive = false;
      trackingRequested = false;
      service.stop?.();
      resetAcquisitionEvidence();
      focusedInitially = false;
      if (acceptedPosition) {
        acceptedPosition = null;
        onClear({ reason: nextState, reacquiring: false });
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
    reacquisitionActive = false;
    acceptedPosition = null;
    focusedInitially = false;
    resetAcquisitionEvidence();
    // Called directly from the Locate me gesture so permission-gated browsers
    // may display their orientation prompt. Failure never blocks GPS startup.
    void orientationService.start(receiveOrientation, () => publishHeading());
    render("requesting-permission");
    startAcquisitionDeadline();
    return service.start(
      (position) => { if (!acceptedPosition) render("locating"); receive(position); },
      receiveServiceError,
    );
  }

  function stop() {
    trackingRequested = false;
    service.stop();
    orientationService.stop();
    if (deviceHeadingExpiry !== null) clearDeadline(deviceHeadingExpiry);
    clearAcquisitionDeadline();
    clearFreshnessDeadline();
    reacquisitionActive = false;
    deviceHeadingExpiry = null;
    deviceHeading = null;
    deviceHeadingTimestamp = null;
    acceptedPosition = null;
    lastRawAccepted = null;
    focusedInitially = false;
    stabilizer.reset();
    headingOpposition.reset();
    onClear({ reason: "stopped", reacquiring: false });
    render("stopped");
  }

  function visibilityChanged() {
    if (!trackingRequested) return;
    if (documentObject.hidden) {
      service.stop({ preserveCallbacks: true });
      orientationService.pause();
    } else {
      const age = acceptedPosition ? Math.max(0, now() - acceptedPosition.timestamp) : Infinity;
      if (!acceptedPosition || age >= LIVE_LOCATION_RESUME_REACQUIRE_MS) {
        restartFreshAcquisition({ preserveDisplayed: false, hardReset: true,
          clearReason: "stale" });
      } else {
        service.resume();
        scheduleFreshnessExpiry();
      }
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
    refresh: () => restartFreshAcquisition({ preserveDisplayed: false, hardReset: true }),
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
      clearFreshnessDeadline();
      documentObject?.removeEventListener?.("visibilitychange", visibilityChanged);
    },
  };
}
