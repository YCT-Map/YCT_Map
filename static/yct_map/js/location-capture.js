import { assessSample, createLocationStabilizer } from "./location-filter.js?v=system-closeout-3";

export const FIELD_CAPTURE_MIN_DURATION_MS = 6_000;
export const FIELD_CAPTURE_MAX_DURATION_MS = 10_000;
// Retained for compatibility with existing imports; capture is now adaptive.
export const FIELD_CAPTURE_DURATION_MS = FIELD_CAPTURE_MAX_DURATION_MS;

const ERROR_COPY = Object.freeze({
  "permission-denied": "Location permission was denied. Allow access or choose the point manually.",
  unavailable: "Your position is unavailable. Try again or choose the point manually.",
  "timed-out": "Location took too long. Try again or choose the point manually.",
  unsupported: "Current location is unavailable in this browser. Choose the point manually.",
  "outside-area": "You’re outside the YabaTech mapping area.",
  unreliable: "Couldn’t get a reliable position. Try again.",
  cancelled: "Location capture cancelled. You can try again.",
});

function geolocationError(error) {
  if (error?.code === 1) return "permission-denied";
  if (error?.code === 3) return "timed-out";
  return "unavailable";
}

export function createFiveSecondLocationCapture({
  geolocation = globalThis.navigator?.geolocation,
  supportedArea = null,
  durationMs = null,
  minimumDurationMs = FIELD_CAPTURE_MIN_DURATION_MS,
  maximumDurationMs = durationMs ?? FIELD_CAPTURE_MAX_DURATION_MS,
  now = Date.now,
  setTimer = globalThis.setTimeout,
  clearTimer = globalThis.clearTimeout,
  setTicker = globalThis.setInterval,
  clearTicker = globalThis.clearInterval,
  onProgress = () => {},
  onSuccess = () => {},
  onFailure = () => {},
} = {}) {
  let generation = 0;
  let watchId = null;
  let minimumTimer = null;
  let maximumTimer = null;
  let progressTimer = null;
  let lastAccepted = null;
  let stabilizer = createLocationStabilizer({ warmupReasonableFixes: 2 });

  function cleanup() {
    if (watchId !== null) geolocation?.clearWatch?.(watchId);
    if (minimumTimer !== null) clearTimer(minimumTimer);
    if (maximumTimer !== null) clearTimer(maximumTimer);
    if (progressTimer !== null) clearTicker(progressTimer);
    watchId = null;
    minimumTimer = null;
    maximumTimer = null;
    progressTimer = null;
  }

  function cancel({ notify = false } = {}) {
    generation += 1;
    cleanup();
    lastAccepted = null;
    stabilizer.reset();
    if (notify) onFailure("cancelled", ERROR_COPY.cancelled);
  }

  function start() {
    cancel();
    if (!geolocation?.watchPosition) {
      onFailure("unsupported", ERROR_COPY.unsupported);
      return false;
    }
    const token = generation;
    const startedAt = now();
    const finish = () => {
      if (token !== generation) return false;
      const selected = stabilizer.getStable() || stabilizer.finalize().sample;
      generation += 1;
      cleanup();
      onProgress(100);
      if (!selected) {
        onFailure("unreliable", ERROR_COPY.unreliable);
        return false;
      }
      if (supportedArea && !supportedArea.contains(selected)) {
        onFailure("outside-area", ERROR_COPY["outside-area"]);
        return false;
      }
      onSuccess(selected);
      return true;
    };
    const finishIfConverged = () => {
      if (token !== generation || now() - startedAt < minimumDurationMs) return false;
      return stabilizer.isConverged() ? finish() : false;
    };
    onProgress(0);
    progressTimer = setTicker(() => {
      if (token !== generation) return;
      onProgress(Math.min(99, Math.floor((now() - startedAt) / maximumDurationMs * 100)));
    }, 100);

    watchId = geolocation.watchPosition((rawPosition) => {
      if (token !== generation) return;
      const assessed = assessSample(rawPosition, lastAccepted);
      if (!assessed.accepted) return;
      lastAccepted = assessed.sample;
      stabilizer.update(assessed.sample, assessed.quality);
      finishIfConverged();
    }, (error) => {
      if (token !== generation) return;
      const reason = geolocationError(error);
      cancel();
      onFailure(reason, ERROR_COPY[reason]);
    }, { enableHighAccuracy: true, maximumAge: 0,
      timeout: Math.max(12_000, maximumDurationMs + 2_000) });

    minimumTimer = setTimer(finishIfConverged, minimumDurationMs);
    maximumTimer = setTimer(finish, maximumDurationMs);
    return true;
  }

  return { start, cancel, destroy: cancel, isCapturing: () => watchId !== null };
}

export const createAdaptiveLocationCapture = createFiveSecondLocationCapture;

export function bindLocationCapture({ button, statusElement, onPoint, supportedAreaPromise,
  documentObject = globalThis.document, captureFactory = createAdaptiveLocationCapture } = {}) {
  let capture = null;
  let destroyed = false;
  const idleLabel = button.textContent;

  async function start() {
    capture?.cancel();
    button.disabled = false;
    button.textContent = "Restart capture";
    statusElement.textContent = "Finding your position… 0%";
    let supportedArea = null;
    try { supportedArea = await supportedAreaPromise; } catch (_error) {
      statusElement.textContent = "The YabaTech mapping area could not be loaded. Try again after refreshing.";
      button.textContent = idleLabel;
      return false;
    }
    if (!supportedArea?.contains) {
      statusElement.textContent = "The YabaTech mapping area could not be loaded. Try again after refreshing.";
      button.textContent = idleLabel;
      return false;
    }
    if (destroyed) return false;
    capture = captureFactory({
      supportedArea,
      onProgress(percent) { statusElement.textContent = `Finding your position… ${percent}%`; },
      onSuccess(position) {
        button.textContent = "Use current location";
        onPoint({ lng: position.longitude, lat: position.latitude });
        statusElement.textContent = "Position selected. Adjust it on the map if needed, then save the form.";
      },
      onFailure(_reason, message) {
        button.textContent = "Try current location again";
        statusElement.textContent = message;
      },
    });
    return capture.start();
  }

  function visibilityChanged() {
    if (documentObject?.hidden && capture?.isCapturing()) capture.cancel({ notify: true });
  }

  button.addEventListener("click", start);
  documentObject?.addEventListener?.("visibilitychange", visibilityChanged);
  return {
    start,
    destroy() {
      destroyed = true;
      capture?.destroy();
      button.removeEventListener?.("click", start);
      documentObject?.removeEventListener?.("visibilitychange", visibilityChanged);
    },
  };
}
