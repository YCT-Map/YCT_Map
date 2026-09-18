export const GEOLOCATION_OPTIONS = Object.freeze({
  initial: { enableHighAccuracy: true, timeout: 12_000, maximumAge: 15_000 },
  watch: { enableHighAccuracy: true, timeout: 20_000, maximumAge: 0 },
});

export function normalizeGeolocationError(error) {
  if (error?.code === 1) return "permission-denied";
  if (error?.code === 2) return "unavailable";
  if (error?.code === 3) return "timed-out";
  return "unavailable";
}

export function createGeolocationService({ geolocation = globalThis.navigator?.geolocation } = {}) {
  let watchId = null;
  let callbacks = null;

  function startWatch() {
    if (watchId !== null || !callbacks) return;
    watchId = geolocation.watchPosition(
      callbacks.onPosition,
      (error) => {
        const state = normalizeGeolocationError(error);
        const onError = callbacks?.onError;
        if (state === "permission-denied") stop();
        onError?.(state);
      },
      GEOLOCATION_OPTIONS.watch,
    );
  }

  function start(onPosition, onError) {
    stop();
    callbacks = { onPosition, onError };
    if (!geolocation) {
      onError("unsupported");
      return false;
    }
    geolocation.getCurrentPosition(
      (position) => {
        callbacks?.onPosition(position);
        startWatch();
      },
      (error) => {
        const state = normalizeGeolocationError(error);
        callbacks?.onError(state);
        if (state !== "permission-denied") startWatch();
      },
      GEOLOCATION_OPTIONS.initial,
    );
    return true;
  }

  function stop({ preserveCallbacks = false } = {}) {
    if (watchId !== null && geolocation) geolocation.clearWatch(watchId);
    watchId = null;
    if (!preserveCallbacks) callbacks = null;
  }

  function resume() {
    if (geolocation && callbacks) startWatch();
  }

  return { start, stop, resume, isSupported: Boolean(geolocation) };
}
