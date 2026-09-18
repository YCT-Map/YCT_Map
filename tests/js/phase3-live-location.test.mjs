import assert from "node:assert/strict";
import test from "node:test";

import { assessSample, normalizePosition } from "../../static/yct_map/js/location-filter.js";
import { createGeolocationService } from "../../static/yct_map/js/geolocation.js";
import { createUserLocation } from "../../static/yct_map/js/user-location.js";

function position({ longitude = 3.374, latitude = 6.519, accuracy = 12, timestamp = 1_000,
  heading = null, speed = null } = {}) {
  return { timestamp, coords: { longitude, latitude, accuracy, heading, speed } };
}

test("normalization rejects malformed samples and never fabricates heading", () => {
  assert.equal(normalizePosition(position({ longitude: Infinity })), null);
  assert.equal(normalizePosition(position({ latitude: 91 })), null);
  assert.equal(normalizePosition(position({ accuracy: -1 })), null);
  assert.equal(normalizePosition(position()).headingDegrees, null);
  assert.equal(normalizePosition(position({ heading: 85, speed: 0.2 })).headingDegrees, null);
  assert.equal(normalizePosition(position({ heading: 85, speed: 1.2 })).headingDegrees, 85);
});

test("filter accepts useful updates while rejecting poor accuracy, stale data and noisy jumps", () => {
  const first = assessSample(position());
  assert.equal(first.accepted, true);
  assert.equal(first.quality, "reasonable");
  assert.equal(assessSample(position({ accuracy: 140 }), first.sample).reason, "poor-accuracy");
  assert.equal(assessSample(position({ timestamp: 900 }), first.sample).reason, "stale");
  const jump = assessSample(position({ longitude: 3.384, timestamp: 2_000, accuracy: 18 }), first.sample);
  assert.equal(jump.accepted, false);
  assert.equal(jump.reason, "implausible-jump");
  const update = assessSample(position({ longitude: 3.37402, timestamp: 3_000, accuracy: 14 }), first.sample);
  assert.equal(update.accepted, true);
});

test("geolocation service reports unsupported and cleans up its watcher", () => {
  let unsupported = null;
  const missing = createGeolocationService({ geolocation: null });
  assert.equal(missing.start(() => {}, (state) => { unsupported = state; }), false);
  assert.equal(unsupported, "unsupported");

  let initialSuccess;
  let watchSuccess;
  const cleared = [];
  const geolocation = {
    getCurrentPosition(success) { initialSuccess = success; },
    watchPosition(success) { watchSuccess = success; return 17; },
    clearWatch(id) { cleared.push(id); },
  };
  const received = [];
  const service = createGeolocationService({ geolocation });
  assert.equal(service.start((sample) => received.push(sample), () => {}), true);
  initialSuccess(position());
  watchSuccess(position({ timestamp: 2_000 }));
  assert.equal(received.length, 2);
  service.stop();
  service.stop();
  assert.deepEqual(cleared, [17]);
});

test("watch permission denial clears the active watcher", () => {
  let initialSuccess;
  let watchError;
  const cleared = [];
  const geolocation = {
    getCurrentPosition(success) { initialSuccess = success; },
    watchPosition(_success, error) { watchError = error; return 23; },
    clearWatch(id) { cleared.push(id); },
  };
  const errors = [];
  const service = createGeolocationService({ geolocation });
  service.start(() => {}, (state) => errors.push(state));
  initialSuccess(position());
  watchError({ code: 1 });
  assert.deepEqual(errors, ["permission-denied"]);
  assert.deepEqual(cleared, [23]);
});

class FakeElement {
  constructor() {
    this.hidden = false;
    this.disabled = false;
    this.textContent = "";
    this.dataset = {};
    this.listeners = new Map();
  }
  addEventListener(type, callback) { this.listeners.set(type, callback); }
  querySelector(selector) { return this.queries.get(selector); }
}

function locationHarness() {
  const root = new FakeElement();
  const selectors = ["#locate-me", "#recenter-me", "#stop-location", "#location-message", "#location-accuracy"];
  root.queries = new Map(selectors.map((selector) => [selector, new FakeElement()]));
  return { root, get: (selector) => root.querySelector(selector) };
}

test("user controller handles permission, accepted position, recenter, rejection and stop", () => {
  const harness = locationHarness();
  let positionCallback;
  let errorCallback;
  let stopCount = 0;
  const service = {
    isSupported: true,
    start(onPosition, onError) { positionCallback = onPosition; errorCallback = onError; return true; },
    stop() { stopCount += 1; },
    resume() {},
  };
  const shown = [];
  let cleared = 0;
  let recentered = 0;
  const fakeDocument = { hidden: false, addEventListener() {}, removeEventListener() {} };
  const controller = createUserLocation({
    element: harness.root,
    service,
    documentObject: fakeDocument,
    onPosition: (...args) => shown.push(args),
    onClear: () => { cleared += 1; },
    onRecenter: () => { recentered += 1; },
  });

  harness.get("#locate-me").listeners.get("click")();
  assert.equal(controller.getState(), "requesting-permission");
  positionCallback(position());
  assert.equal(controller.getState(), "active");
  assert.equal(shown.length, 1);
  assert.equal(shown[0][1].focus, true);
  positionCallback(position({ longitude: 3.39, timestamp: 2_000, accuracy: 20 }));
  assert.equal(shown.length, 1, "an implausible noisy jump must not move the marker");
  harness.get("#recenter-me").listeners.get("click")();
  assert.equal(recentered, 1);
  harness.get("#stop-location").listeners.get("click")();
  assert.equal(controller.getState(), "stopped");
  assert.equal(stopCount, 1);
  assert.equal(cleared, 1);

  controller.start();
  errorCallback("permission-denied");
  assert.equal(controller.getState(), "permission-denied");
  assert.match(harness.get("#location-message").textContent, /manually/);
});
