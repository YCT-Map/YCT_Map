export const DEVICE_HEADING_STALE_MS = 4_000;

export function normalizeHeading(value) {
  if (!Number.isFinite(value)) return null;
  return ((value % 360) + 360) % 360;
}

export function screenOrientationDegrees(screenObject = globalThis.screen) {
  const angle = Number(screenObject?.orientation?.angle ?? globalThis.orientation ?? 0);
  return Number.isFinite(angle) ? normalizeHeading(angle) : 0;
}

export function compassHeadingFromEuler(alpha, beta = 0, gamma = 0) {
  if (![alpha, beta, gamma].every((value) => typeof value === "number" && Number.isFinite(value))) return null;
  const radians = (degrees) => degrees * Math.PI / 180;
  const a = radians(alpha);
  const b = radians(beta);
  const g = radians(gamma);
  const x = -Math.cos(a) * Math.sin(g) - Math.sin(a) * Math.sin(b) * Math.cos(g);
  const y = -Math.sin(a) * Math.sin(g) + Math.cos(a) * Math.sin(b) * Math.cos(g);
  // When the screen is essentially flat, the horizontal projection is
  // degenerate; alpha's Earth-referenced z rotation is the stable answer.
  if (Math.hypot(x, y) < 1e-7) return normalizeHeading(360 - Number(alpha));
  return normalizeHeading(Math.atan2(x, y) * 180 / Math.PI);
}

export function headingFromOrientation(event, screenAngle = 0) {
  const nativeHeading = event?.webkitCompassHeading;
  if (Number.isFinite(nativeHeading)) return normalizeHeading(nativeHeading - screenAngle);
  if (event?.absolute !== true || !Number.isFinite(event?.alpha)) return null;
  const beta = Number.isFinite(event?.beta) ? event.beta : 0;
  const gamma = Number.isFinite(event?.gamma) ? event.gamma : 0;
  const heading = compassHeadingFromEuler(event.alpha, beta, gamma);
  return heading === null ? null : normalizeHeading(heading - screenAngle);
}

export function renderedRelativeHeading(geographicHeading, mapBearing = 0) {
  const heading = normalizeHeading(geographicHeading);
  return heading === null ? null : normalizeHeading(heading - (Number(mapBearing) || 0));
}

export function headingDiagnosticSnapshot({ rawOrientation = null, deviceHeading = null,
  deviceTimestamp = null, movementHeading = null, selected = null, screenAngle = 0,
  mapBearing = 0, now = Date.now() } = {}) {
  return {
    rawOrientation,
    normalizedDeviceHeading: normalizeHeading(deviceHeading),
    screenOrientation: normalizeHeading(screenAngle) ?? 0,
    movementHeading: normalizeHeading(movementHeading),
    selectedHeading: normalizeHeading(selected?.headingDegrees),
    selectedSource: selected?.source || null,
    headingAgeMs: Number.isFinite(deviceTimestamp) ? Math.max(0, now - deviceTimestamp) : null,
    mapBearing: normalizeHeading(mapBearing) ?? 0,
    renderedRelativeRotation: renderedRelativeHeading(selected?.headingDegrees, mapBearing),
  };
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
  let lastRawOrientation = null;

  function handle(event) {
    const screenAngle = screenOrientationDegrees(screenObject);
    lastRawOrientation = {
      alpha: Number.isFinite(event?.alpha) ? event.alpha : null,
      beta: Number.isFinite(event?.beta) ? event.beta : null,
      gamma: Number.isFinite(event?.gamma) ? event.gamma : null,
      webkitCompassHeading: Number.isFinite(event?.webkitCompassHeading)
        ? event.webkitCompassHeading : null,
      absolute: event?.absolute === true,
      screenAngle,
    };
    const raw = headingFromOrientation(event, screenAngle);
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
    isListening: () => listening,
    getDiagnostic: () => ({ rawOrientation: lastRawOrientation, heading: smoother.getHeading() }) };
}
