export const DEVICE_HEADING_STALE_MS = 4_000;

export function normalizeHeading(value) {
  if (!Number.isFinite(value)) return null;
  return ((value % 360) + 360) % 360;
}

export function screenOrientationDegrees(screenObject = globalThis.screen) {
  const angle = Number(screenObject?.orientation?.angle ?? globalThis.orientation ?? 0);
  return Number.isFinite(angle) ? normalizeHeading(angle) : 0;
}

export function headingFromOrientation(event, screenAngle = 0) {
  const nativeHeading = Number(event?.webkitCompassHeading);
  if (Number.isFinite(nativeHeading)) return normalizeHeading(nativeHeading + screenAngle);
  if (event?.absolute !== true || !Number.isFinite(Number(event?.alpha))) return null;
  return normalizeHeading(360 - Number(event.alpha) + screenAngle);
}

export function shortestHeadingDelta(from, to) {
  return ((to - from + 540) % 360) - 180;
}

export function createCircularHeadingSmoother({ response = 0.42, jumpDegrees = 120 } = {}) {
  let heading = null;
  let pendingJump = null;
  return {
    update(value) {
      const next = normalizeHeading(value);
      if (next === null) return heading;
      if (heading === null) { heading = next; return heading; }
      const delta = shortestHeadingDelta(heading, next);
      if (Math.abs(delta) > jumpDegrees) {
        if (pendingJump === null || Math.abs(shortestHeadingDelta(pendingJump, next)) > 25) {
          pendingJump = next;
          return heading;
        }
      }
      pendingJump = null;
      const adaptiveResponse = Math.abs(delta) > 45 ? Math.max(response, 0.68) : response;
      heading = normalizeHeading(heading + delta * adaptiveResponse);
      return heading;
    },
    reset() { heading = null; pendingJump = null; },
    getHeading: () => heading,
  };
}

export function selectDisplayedHeading({ deviceHeading, deviceTimestamp, movementHeading, now = Date.now(),
  staleAfterMs = DEVICE_HEADING_STALE_MS } = {}) {
  if (Number.isFinite(deviceHeading) && Number.isFinite(deviceTimestamp)
      && now - deviceTimestamp >= 0 && now - deviceTimestamp <= staleAfterMs) {
    return { headingDegrees: normalizeHeading(deviceHeading), source: "device" };
  }
  if (Number.isFinite(movementHeading)) {
    return { headingDegrees: normalizeHeading(movementHeading), source: "movement" };
  }
  return { headingDegrees: null, source: null };
}

export function createDeviceOrientationService({
  windowObject = globalThis.window,
  screenObject = globalThis.screen,
  now = Date.now,
  smoother = createCircularHeadingSmoother(),
} = {}) {
  const OrientationEvent = windowObject?.DeviceOrientationEvent;
  const eventName = "ondeviceorientationabsolute" in (windowObject || {})
    ? "deviceorientationabsolute" : "deviceorientation";
  let callback = null;
  let stateCallback = null;
  let listening = false;
  let enabled = false;

  function handle(event) {
    const raw = headingFromOrientation(event, screenOrientationDegrees(screenObject));
    if (raw === null) return;
    const headingDegrees = smoother.update(raw);
    callback?.({ headingDegrees, timestamp: now(), absolute: true });
  }

  function listen() {
    if (listening || !enabled) return;
    windowObject.addEventListener(eventName, handle, true);
    listening = true;
    stateCallback?.("active");
  }

  async function start(onHeading, onState = () => {}) {
    callback = onHeading;
    stateCallback = onState;
    if (!OrientationEvent || !windowObject?.isSecureContext) {
      stateCallback("unsupported");
      return false;
    }
    try {
      if (typeof OrientationEvent.requestPermission === "function") {
        const permission = await OrientationEvent.requestPermission();
        if (permission !== "granted") {
          stateCallback("denied");
          return false;
        }
      }
      enabled = true;
      listen();
      return true;
    } catch (_error) {
      stateCallback("unavailable");
      return false;
    }
  }

  function pause() {
    if (listening) windowObject.removeEventListener(eventName, handle, true);
    listening = false;
  }

  function resume() { listen(); }

  function stop() {
    pause();
    enabled = false;
    callback = null;
    smoother.reset();
  }

  return { start, pause, resume, stop, destroy: stop,
    isSupported: Boolean(OrientationEvent && windowObject?.isSecureContext),
    isListening: () => listening };
}
