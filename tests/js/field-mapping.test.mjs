import assert from "node:assert/strict";
import test from "node:test";

import {
  compassHeadingFromEuler,
  headingDiagnosticSnapshot,
  headingFromOrientation,
  renderedRelativeHeading,
} from "../../static/yct_map/js/device-orientation.js";
import { bindLocationCapture, createFiveSecondLocationCapture } from "../../static/yct_map/js/location-capture.js";
import { createSupportedLocationArea } from "../../static/yct_map/js/supported-area.js";
import { userLocationArrowLayerDefinitions } from "../../static/yct_map/js/map.js";

const campus = { type: "FeatureCollection", features: [{ type: "Feature", properties: {}, geometry: {
  type: "Polygon", coordinates: [[[3.373, 6.517], [3.375, 6.517], [3.375, 6.519],
    [3.373, 6.519], [3.373, 6.517]]],
} }] };

test("tilt-aware orientation maps physical north east south and west to geographic headings", () => {
  assert.equal(compassHeadingFromEuler(0, 45, 0), 0);
  assert.ok(Math.abs(compassHeadingFromEuler(270, 45, 0) - 90) < 1e-8);
  assert.ok(Math.abs(compassHeadingFromEuler(180, 45, 0) - 180) < 1e-8);
  assert.ok(Math.abs(compassHeadingFromEuler(90, 45, 0) - 270) < 1e-8);
  assert.equal(headingFromOrientation({ absolute: true, alpha: 0, beta: 45, gamma: 0 }, 90), 90);
  assert.equal(headingFromOrientation({ webkitCompassHeading: 90 }, 90), 180);
  assert.equal(headingFromOrientation({ absolute: true, alpha: null, beta: null, gamma: null }), null,
    "missing sensor values must not fabricate north");
});

test("map bearing changes rendered relative rotation but never geographic heading", () => {
  assert.equal(renderedRelativeHeading(90, 30), 60);
  const snapshot = headingDiagnosticSnapshot({ deviceHeading: 90, deviceTimestamp: 1000,
    movementHeading: 80, selected: { headingDegrees: 90, source: "device" },
    screenAngle: 0, mapBearing: 30, now: 1500 });
  assert.equal(snapshot.selectedHeading, 90);
  assert.equal(snapshot.renderedRelativeRotation, 60);
  assert.equal(snapshot.headingAgeMs, 500);
});

test("directional user marker is a layered map-aligned arrowhead with a centred pivot", () => {
  const layers = userLocationArrowLayerDefinitions();
  assert.equal(layers.length, 3);
  assert.ok(layers.every((layer) => layer.type === "symbol"));
  assert.ok(layers.every((layer) => layer.layout["text-field"] === "▲"));
  assert.ok(layers.every((layer) => layer.layout["text-rotation-alignment"] === "map"));
  assert.ok(layers.every((layer) => !layer.layout["text-anchor"] || layer.layout["text-anchor"] === "center"));
  assert.equal(layers.at(-1).paint["text-color"], "#1267d6");
});

test("supported YCT area derives from campus geometry plus context", () => {
  const area = createSupportedLocationArea(campus, 400);
  assert.equal(area.contains({ longitude: 3.374, latitude: 6.518 }), true);
  assert.equal(area.contains({ longitude: 3.377, latitude: 6.518 }), true,
    "immediate gate/context area remains supported");
  assert.equal(area.contains({ longitude: 3.45, latitude: 6.60 }), false);
});

function position({ longitude = 3.374, latitude = 6.518, accuracy = 6, timestamp = 1000 } = {}) {
  return { timestamp, coords: { longitude, latitude, accuracy, speed: null, heading: null } };
}

function captureHarness({ area = createSupportedLocationArea(campus, 400) } = {}) {
  let watchSuccess;
  let watchFailure;
  let ticker;
  const timers = new Map();
  let current = 0;
  let nextWatch = 0;
  const cleared = [];
  const progress = [];
  const successes = [];
  const failures = [];
  const geolocation = {
    watchPosition(success, failure) { watchSuccess = success; watchFailure = failure; return ++nextWatch; },
    clearWatch(id) { cleared.push(id); },
  };
  const capture = createFiveSecondLocationCapture({
    geolocation, supportedArea: area, now: () => current,
    setTimer(callback, delay) { timers.set(delay, callback); return delay; },
    clearTimer(id) { timers.delete(id); },
    setTicker(callback) { ticker = callback; return 2; }, clearTicker() {},
    onProgress: (value) => progress.push(value),
    onSuccess: (value) => successes.push(value),
    onFailure: (reason, message) => failures.push({ reason, message }),
  });
  return { capture, progress, successes, failures, cleared,
    emit: (value) => watchSuccess(value), fail: (value) => watchFailure(value),
    advance(value) { current = value; ticker?.(); },
    runTimer(delay) { current = delay; timers.get(delay)?.(); },
    finish: () => { current = 10_000; timers.get(10_000)?.(); },
  };
}

test("adaptive capture waits for stabilized evidence and reports elapsed progress", () => {
  const harness = captureHarness();
  harness.capture.start();
  harness.emit(position({ accuracy: 120 }));
  harness.emit(position({ timestamp: 2000, longitude: 3.37401 }));
  assert.equal(harness.successes.length, 0, "the first acceptable callback is not selected immediately");
  harness.emit(position({ timestamp: 3000, longitude: 3.37402 }));
  harness.advance(2500);
  harness.advance(4900);
  harness.finish();
  assert.equal(harness.successes.length, 1);
  assert.deepEqual(harness.progress, [0, 25, 49, 100]);
});

test("adaptive capture completes at six seconds when good fixes converge", () => {
  const harness = captureHarness();
  harness.capture.start();
  harness.emit(position({ timestamp: 1_000, longitude: 3.37400, accuracy: 7 }));
  harness.emit(position({ timestamp: 2_000, longitude: 3.37401, accuracy: 6 }));
  harness.emit(position({ timestamp: 3_000, longitude: 3.374015, accuracy: 6 }));
  assert.equal(harness.successes.length, 0);
  harness.runTimer(6_000);
  assert.equal(harness.successes.length, 1);
  assert.equal(harness.progress.at(-1), 100);
});

test("adaptive capture has a strict ten-second outcome when fixes never converge", () => {
  const harness = captureHarness();
  harness.capture.start();
  harness.finish();
  assert.equal(harness.successes.length, 0);
  assert.equal(harness.failures[0].reason, "unreliable");
});

test("capture rejects outside-area results and leaves coordinates untouched", () => {
  const harness = captureHarness();
  harness.capture.start();
  harness.emit(position({ longitude: 3.45, latitude: 6.60 }));
  harness.emit(position({ longitude: 3.45001, latitude: 6.60, timestamp: 2000 }));
  harness.finish();
  assert.equal(harness.successes.length, 0);
  assert.equal(harness.failures[0].reason, "outside-area");
});

test("capture handles denial, cancellation and repeated-start watcher cleanup", () => {
  const denied = captureHarness();
  denied.capture.start();
  denied.fail({ code: 1 });
  assert.equal(denied.failures[0].reason, "permission-denied");
  const repeated = captureHarness();
  repeated.capture.start();
  repeated.capture.start();
  assert.deepEqual(repeated.cleared, [1]);
  repeated.capture.cancel({ notify: true });
  assert.deepEqual(repeated.cleared, [1, 2]);
  assert.equal(repeated.failures.at(-1).reason, "cancelled");
});

test("bound editor capture changes coordinates only after final success", async () => {
  const listeners = new Map();
  const button = { textContent: "Use current location", disabled: false,
    addEventListener: (name, callback) => listeners.set(name, callback),
    removeEventListener() {} };
  const statusElement = { textContent: "" };
  const documentObject = { hidden: false, addEventListener() {}, removeEventListener() {} };
  const selected = [];
  let captureOptions;
  bindLocationCapture({ button, statusElement, documentObject,
    supportedAreaPromise: Promise.resolve(createSupportedLocationArea(campus, 400)),
    onPoint: (point) => selected.push(point),
    captureFactory(options) {
      captureOptions = options;
      return { start: () => true, cancel() {}, destroy() {}, isCapturing: () => true };
    },
  });
  await listeners.get("click")();
  assert.deepEqual(selected, [], "starting capture cannot populate editor coordinates");
  captureOptions.onProgress(60);
  assert.match(statusElement.textContent, /60%/);
  captureOptions.onSuccess({ longitude: 3.3742, latitude: 6.5185 });
  assert.deepEqual(selected, [{ lng: 3.3742, lat: 6.5185 }]);
});

test("editor capture fails closed when supported-area configuration is unavailable", async () => {
  const listeners = new Map();
  const button = { textContent: "Use current location", disabled: false,
    addEventListener: (name, callback) => listeners.set(name, callback),
    removeEventListener() {} };
  const statusElement = { textContent: "" };
  let factoryCalled = false;
  bindLocationCapture({ button, statusElement,
    documentObject: { addEventListener() {}, removeEventListener() {} },
    supportedAreaPromise: Promise.resolve(null), onPoint() {},
    captureFactory() { factoryCalled = true; },
  });
  assert.equal(await listeners.get("click")(), false);
  assert.equal(factoryCalled, false);
  assert.match(statusElement.textContent, /mapping area could not be loaded/i);
});
