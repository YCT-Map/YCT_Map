import { assessSample, createLocationStabilizer } from "./location-filter.js?v=field-mapping-1";

export const FIELD_CAPTURE_DURATION_MS = 5_000;

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
  durationMs = FIELD_CAPTURE_DURATION_MS,
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
  let finishTimer = null;
  let progressTimer = null;
  let lastAccepted = null;
  let stabilizer = createLocationStabilizer({ warmupReasonableFixes: 2 });

  function cleanup() {
    if (watchId !== null) geolocation?.clearWatch?.(watchId);
    if (finishTimer !== null) clearTimer(finishTimer);
    if (progressTimer !== null) clearTicker(progressTimer);
    watchId = null;
    finishTimer = null;
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
    onProgress(0);
    progressTimer = setTicker(() => {
      if (token !== generation) return;
      onProgress(Math.min(99, Math.floor((now() - startedAt) / durationMs * 100)));
    }, 100);

    watchId = geolocation.watchPosition((rawPosition) => {
      if (token !== generation) return;
      const assessed = assessSample(rawPosition, lastAccepted);
      if (!assessed.accepted) return;
      lastAccepted = assessed.sample;
      stabilizer.update(assessed.sample, assessed.quality);
    }, (error) => {
      if (token !== generation) return;
      const reason = geolocationError(error);
      cancel();
      onFailure(reason, ERROR_COPY[reason]);
    }, { enableHighAccuracy: true, maximumAge: 0, timeout: Math.max(12_000, durationMs + 2_000) });

    finishTimer = setTimer(() => {
      if (token !== generation) return;
      const selected = stabilizer.getStable();
      generation += 1;
      cleanup();
      onProgress(100);
      if (!selected) {
        onFailure("unreliable", ERROR_COPY.unreliable);
        return;
      }
      if (supportedArea && !supportedArea.contains(selected)) {
        onFailure("outside-area", ERROR_COPY["outside-area"]);
        return;
      }
      onSuccess(selected);
    }, durationMs);
    return true;
  }

  return { start, cancel, destroy: cancel, isCapturing: () => watchId !== null };
}

export function bindLocationCapture({ button, statusElement, onPoint, supportedAreaPromise,
  documentObject = globalThis.document, captureFactory = createFiveSecondLocationCapture } = {}) {
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
