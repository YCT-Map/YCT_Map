import assert from "node:assert/strict";
import test from "node:test";

import {
  createHeadingOppositionDiagnostic,
  createCircularHeadingSmoother,
  createDeviceOrientationService,
  headingFromOrientation,
  normalizeHeading,
  selectDisplayedHeading,
} from "../../static/yct_map/js/device-orientation.js";
import { recenterCameraOptions, userLocationArrowLayerDefinitions,
  userLocationArrowTipVector, userLocationFeature } from "../../static/yct_map/js/map.js";

test("heading normalization handles wrap and rejects relative orientation", () => {
  assert.equal(normalizeHeading(0), 0);
  assert.equal(normalizeHeading(360), 0);
  assert.equal(normalizeHeading(-10), 350);
  assert.equal(headingFromOrientation({ absolute: true, alpha: 0 }, 0), 0);
  assert.equal(headingFromOrientation({ absolute: true, alpha: 90 }, 0), 270);
  assert.equal(headingFromOrientation({ absolute: false, alpha: 90 }, 0), null,
    "relative orientation must not be presented as Earth-referenced heading");
  assert.equal(headingFromOrientation({ webkitCompassHeading: 350 }, 20), 10);
});

test("physical cardinal headings remain correct in portrait and both landscape orientations", () => {
  const expected = [0, 90, 180, 270];
  const fixtures = [
    { screenAngle: 0, alphas: [0, 270, 180, 90] },
    { screenAngle: 90, alphas: [90, 0, 270, 180] },
    { screenAngle: 270, alphas: [270, 180, 90, 0] },
  ];
  for (const { screenAngle, alphas } of fixtures) {
    assert.deepEqual(alphas.map((alpha) => headingFromOrientation(
      { absolute: true, alpha, beta: 45, gamma: 0 }, screenAngle,
    )), expected);
  }
  assert.deepEqual([270, 0, 90, 180].map((heading) =>
    headingFromOrientation({ webkitCompassHeading: heading }, 90)), expected);
});

test("arrow core edge and shadow share an intrinsic north-up forward axis", () => {
  const layers = userLocationArrowLayerDefinitions();
  assert.equal(layers.length, 3);
  assert.ok(layers.every((layer) => layer.layout["text-field"] === "▲"));
  assert.ok(layers.every((layer) => layer.layout["text-rotate"][1] === "heading"));
  assert.ok(layers.every((layer) => layer.layout["text-rotation-alignment"] === "map"));
  const rounded = [0, 90, 180, 270].map((heading) =>
    userLocationArrowTipVector(heading).map((value) => Math.abs(value) < 0.5 ? 0 : Math.round(value)));
  assert.deepEqual(rounded, [[0, -1], [1, 0], [0, 1], [-1, 0]]);
});

test("development diagnostic detects sustained device versus movement opposition", () => {
  const diagnostic = createHeadingOppositionDiagnostic();
  assert.equal(diagnostic.update({ deviceHeading: 0, movementHeading: 180,
    speedMetresPerSecond: 0.2 }).possibleSystematicInversion, false,
  "stationary readings are not evidence of inversion");
  diagnostic.update({ deviceHeading: 0, movementHeading: 180, speedMetresPerSecond: 1.2 });
  diagnostic.update({ deviceHeading: 5, movementHeading: 185, speedMetresPerSecond: 1.1 });
  const opposed = diagnostic.update({ deviceHeading: 355, movementHeading: 175,
    speedMetresPerSecond: 1.3 });
  assert.equal(opposed.angularDeviceMovementDifference, 180);
  assert.equal(opposed.possibleSystematicInversion, true);
  assert.equal(diagnostic.update({ deviceHeading: 90, movementHeading: 95,
    speedMetresPerSecond: 1.2 }).possibleSystematicInversion, false);
});

test("cardinal movement from consecutive GPS fixes never opposes the selected arrow tip", () => {
  const start = [3.374, 6.518];
  const fixtures = [
    { name: "north", end: [3.374, 6.519], heading: 0 },
    { name: "east", end: [3.375, 6.518], heading: 90 },
    { name: "south", end: [3.374, 6.517], heading: 180 },
    { name: "west", end: [3.373, 6.518], heading: 270 },
  ];
  for (const { name, end, heading } of fixtures) {
    const arrow = userLocationArrowTipVector(heading);
    const longitudeDelta = end[0] - start[0];
    const latitudeDelta = end[1] - start[1];
    const length = Math.hypot(longitudeDelta, latitudeDelta);
    const movementScreenVector = [longitudeDelta / length, -latitudeDelta / length];
    const dotProduct = arrow[0] * movementScreenVector[0] + arrow[1] * movementScreenVector[1];
    assert.ok(dotProduct > 0.99, `${name} arrow tip must agree with independent GPS movement`);
  }
});

test("circular smoothing crosses north without averaging toward south", () => {
  const smoother = createCircularHeadingSmoother({ response: 0.5 });
  const values = [358, 359, 1, 2].map((value) => smoother.update(value));
  assert.ok(values.at(-1) < 10 || values.at(-1) > 350);
});

test("smoothing dampens an isolated jump but follows a deliberate gradual turn", () => {
  const smoother = createCircularHeadingSmoother({ response: 0.5 });
  assert.equal(smoother.update(10), 10);
  assert.equal(smoother.update(170), 10, "one implausible jump is held");
  const gradual = [25, 45, 70, 95].map((value) => smoother.update(value));
  assert.ok(gradual.at(-1) > 60, "repeated plausible rotation must remain responsive");
});

test("device heading has priority, then movement heading, then no heading", () => {
  assert.deepEqual(selectDisplayedHeading({ deviceHeading: 20, deviceTimestamp: 1_000,
    movementHeading: 180, now: 2_000 }), { headingDegrees: 20, source: "device" });
  assert.deepEqual(selectDisplayedHeading({ deviceHeading: 20, deviceTimestamp: 1_000,
    movementHeading: 180, now: 6_000 }), { headingDegrees: 180, source: "movement" });
  assert.deepEqual(selectDisplayedHeading({ deviceHeading: null, deviceTimestamp: null,
    movementHeading: null, now: 2_000 }), { headingDegrees: null, source: null });
});

function orientationWindow({ permission = "granted", supported = true } = {}) {
  const listeners = new Map();
  function DeviceOrientationEvent() {}
  if (permission !== null) DeviceOrientationEvent.requestPermission = async () => permission;
  return {
    isSecureContext: true,
    DeviceOrientationEvent: supported ? DeviceOrientationEvent : undefined,
    ondeviceorientationabsolute: null,
    addEventListener(name, callback) { listeners.set(name, callback); },
    removeEventListener(name, callback) { if (listeners.get(name) === callback) listeners.delete(name); },
    listeners,
  };
}

test("orientation permission success starts one listener and lifecycle never duplicates it", async () => {
  const windowObject = orientationWindow();
  const readings = [];
  const service = createDeviceOrientationService({ windowObject,
    screenObject: { orientation: { angle: 0 } }, now: () => 1_000 });
  assert.equal(await service.start((reading) => readings.push(reading)), true);
  assert.equal(windowObject.listeners.size, 1);
  service.resume();
  assert.equal(windowObject.listeners.size, 1);
  windowObject.listeners.get("deviceorientationabsolute")({ absolute: true, alpha: 90 });
  assert.equal(readings[0].headingDegrees, 270);
  service.pause();
  assert.equal(windowObject.listeners.size, 0);
  service.resume();
  assert.equal(windowObject.listeners.size, 1);
  service.destroy();
  assert.equal(windowObject.listeners.size, 0);
});

test("denied and absent orientation support fail safely", async () => {
  const deniedStates = [];
  const denied = createDeviceOrientationService({ windowObject: orientationWindow({ permission: "denied" }) });
  assert.equal(await denied.start(() => {}, (state) => deniedStates.push(state)), false);
  assert.deepEqual(deniedStates, ["denied"]);
  const absentStates = [];
  const absent = createDeviceOrientationService({ windowObject: orientationWindow({ supported: false }) });
  assert.equal(await absent.start(() => {}, (state) => absentStates.push(state)), false);
  assert.deepEqual(absentStates, ["unsupported"]);
});

test("marker heading changes presentation without changing GPS position", () => {
  const position = { longitude: 3.3742, latitude: 6.5185, accuracyMetres: 6 };
  const device = userLocationFeature(position, 85, "device");
  const movement = userLocationFeature(position, 120, "movement");
  const dot = userLocationFeature(position);
  assert.deepEqual(device.geometry.coordinates, movement.geometry.coordinates);
  assert.deepEqual(device.geometry.coordinates, dot.geometry.coordinates);
  assert.equal(device.properties.heading_source, "device");
  assert.equal(movement.properties.heading_source, "movement");
  assert.equal("heading" in dot.properties, false);
});

test("recenter is a one-shot camera move that preserves user bearing", () => {
  const options = recenterCameraOptions({ longitude: 3.3742, latitude: 6.5185 }, 16, false);
  assert.deepEqual(options.center, [3.3742, 6.5185]);
  assert.equal(options.zoom, 17);
  assert.equal("bearing" in options, false, "recenter must not rotate or lock the camera");
  assert.equal("padding" in options, false);
  assert.equal(recenterCameraOptions({ longitude: 3.3742, latitude: 6.5185 }, 18, true).duration, 0);
});
