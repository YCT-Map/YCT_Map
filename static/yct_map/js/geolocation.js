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
  let generation = 0;

  function startWatch(token = generation) {
    if (watchId !== null || !callbacks) return;
    watchId = geolocation.watchPosition(
      (position) => {
        if (token === generation) callbacks?.onPosition(position);
      },
      (error) => {
        if (token !== generation) return;
        const state = normalizeGeolocationError(error);
        const onError = callbacks?.onError;
        if (state === "permission-denied") stop();
        onError?.(state);
      },
      GEOLOCATION_OPTIONS.watch,
    );
  }

  function requestCurrentAndWatch(token = generation) {
    geolocation.getCurrentPosition(
      (position) => {
        if (token !== generation) return;
        callbacks?.onPosition(position);
        startWatch(token);
      },
      (error) => {
        if (token !== generation) return;
        const state = normalizeGeolocationError(error);
        callbacks?.onError(state);
        if (state !== "permission-denied") startWatch(token);
      },
      GEOLOCATION_OPTIONS.initial,
    );
  }

  function start(onPosition, onError) {
    stop();
    callbacks = { onPosition, onError };
    const token = generation;
    if (!geolocation) {
      onError("unsupported");
      return false;
    }
    requestCurrentAndWatch(token);
    return true;
  }

  function stop({ preserveCallbacks = false } = {}) {
    generation += 1;
    if (watchId !== null && geolocation) geolocation.clearWatch(watchId);
    watchId = null;
    if (!preserveCallbacks) callbacks = null;
  }

  function resume() {
    if (geolocation && callbacks) startWatch(generation);
  }

  function reacquire() {
    if (!geolocation || !callbacks) return false;
    stop({ preserveCallbacks: true });
    requestCurrentAndWatch(generation);
    return true;
  }

  return { start, stop, resume, reacquire, isSupported: Boolean(geolocation) };
}
