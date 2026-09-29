import assert from "node:assert/strict";
import test from "node:test";

import { assessSample, createLocationStabilizer, locationQualityLabel, normalizePosition } from "../../static/yct_map/js/location-filter.js";
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

test("public stabilizer warms up, suppresses uncertainty-sized jitter and releases walking", () => {
  const stabilizer = createLocationStabilizer();
  const first = normalizePosition(position({ accuracy: 8, timestamp: 1_000 }));
  const second = normalizePosition(position({ longitude: 3.37401, accuracy: 7, timestamp: 2_000 }));
  assert.equal(stabilizer.update(first, "reasonable").ready, false);
  const ready = stabilizer.update(second, "reasonable");
  assert.equal(ready.ready, true);
  assert.equal(ready.sample.headingDegrees, null);
  const jitter = stabilizer.update(normalizePosition(position({ longitude: 3.374015, accuracy: 6,
    timestamp: 4_000, heading: 90, speed: 1.2 })), "reasonable");
  assert.equal(jitter.reason, "stationary");
  assert.equal(jitter.sample.headingDegrees, null);
  const walking = stabilizer.update(normalizePosition(position({ longitude: 3.37412, accuracy: 7,
    timestamp: 7_000, heading: 90, speed: 1.2 })), "reasonable");
  assert.equal(walking.reason, "movement");
  assert.equal(walking.sample.headingDegrees, 90);
  assert.equal(locationQualityLabel(7), "Good");
  assert.equal(locationQualityLabel(40), "Fair");
  assert.equal(locationQualityLabel(80), "Poor");
});

test("rolling estimate corrects an early biased fix and reports observed instability", () => {
  const stabilizer = createLocationStabilizer();
  stabilizer.update(normalizePosition(position({ longitude: 3.37400, accuracy: 5, timestamp: 1_000 })), "reasonable");
  const initial = stabilizer.update(normalizePosition(position({ longitude: 3.37401, accuracy: 5, timestamp: 2_000 })), "reasonable");
  assert.equal(initial.ready, true);
  stabilizer.update(normalizePosition(position({ longitude: 3.37409, accuracy: 6, timestamp: 5_000 })), "reasonable");
  const corrected = stabilizer.update(normalizePosition(position({ longitude: 3.37410, accuracy: 6, timestamp: 8_000 })), "reasonable");
  assert.ok(corrected.sample.longitude > initial.sample.longitude, "sustained later evidence must move a biased centre");
  assert.ok(["stable", "approximate", "unstable"].includes(corrected.confidence));
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

test("an obsolete initial request cannot restart a watcher or publish a stale point", () => {
  const initialCallbacks=[]; let watchCount=0;
  const geolocation={
    getCurrentPosition(success){initialCallbacks.push(success);},
    watchPosition(){watchCount+=1;return watchCount;},
    clearWatch(){},
  };
  const received=[]; const service=createGeolocationService({geolocation});
  service.start((sample)=>received.push(["old",sample]),()=>{});
  service.start((sample)=>received.push(["new",sample]),()=>{});
  initialCallbacks[0](position());
  assert.equal(watchCount,0);
  assert.equal(received.length,0);
  initialCallbacks[1](position({timestamp:2_000}));
  assert.equal(watchCount,1);
  assert.equal(received[0][0],"new");
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
  setAttribute(name, value) { this[name] = value; }
  querySelector(selector) { return this.queries.get(selector); }
}

function locationHarness() {
  const root = new FakeElement();
  const selectors = ["#locate-me", "#recenter-me", "#stop-location", "#follow-direction", "#north-up",
    "#location-message", "#location-accuracy", "#direction-status"];
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
  assert.equal(controller.getState(), "warming-up");
  assert.equal(shown.length, 0);
  positionCallback(position({ longitude: 3.37401, timestamp: 2_000, accuracy: 10 }));
  assert.equal(controller.getState(), "active");
  assert.equal(shown.length, 1);
  assert.equal(shown[0][1].focus, true);
  assert.match(harness.get("#location-accuracy").textContent, /Location quality: Good.*estimated device uncertainty/);
  positionCallback(position({ longitude: 3.39, timestamp: 3_000, accuracy: 20 }));
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

test("a location-service failure clears the old route origin instead of retaining stale coordinates", () => {
  const harness=locationHarness(); let positionCallback; let errorCallback; let cleared=0;
  const service={isSupported:true,start(onPosition,onError){positionCallback=onPosition;errorCallback=onError;return true;},stop(){},resume(){}};
  const controller=createUserLocation({element:harness.root,service,
    documentObject:{hidden:false,addEventListener(){},removeEventListener(){}},onPosition(){},onClear(){cleared+=1;},onRecenter(){}});
  controller.start();
  positionCallback(position());
  positionCallback(position({longitude:3.37401,timestamp:2_000,accuracy:10}));
  assert.ok(controller.getAcceptedPosition());
  errorCallback("unavailable");
  assert.equal(controller.getAcceptedPosition(),null);
  assert.equal(controller.getState(),"unavailable");
  assert.equal(cleared,1);
});
