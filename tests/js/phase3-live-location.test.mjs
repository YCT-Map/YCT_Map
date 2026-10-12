import assert from "node:assert/strict";
import test from "node:test";

import { assessSample, createLocationStabilizer, locationQualityLabel, normalizePosition } from "../../static/yct_map/js/location-filter.js";
import { createGeolocationService, GEOLOCATION_OPTIONS } from "../../static/yct_map/js/geolocation.js";
import { createUserLocation, LIVE_LOCATION_STALE_AFTER_MS } from "../../static/yct_map/js/user-location.js";

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

test("a cached browser fix older than the fresh-acquisition window is rejected", () => {
  const clock = Date.UTC(2026, 9, 12, 12, 0, 0);
  const stale = assessSample(position({ timestamp: clock - 6_000 }), null, { currentTime: clock });
  assert.equal(stale.accepted, false);
  assert.equal(stale.reason, "stale");
  const fresh = assessSample(position({ timestamp: clock - 1_000 }), null, { currentTime: clock });
  assert.equal(fresh.accepted, true);
});

test("public stabilizer warms up, suppresses uncertainty-sized jitter and releases walking", () => {
  const stabilizer = createLocationStabilizer();
  const first = normalizePosition(position({ accuracy: 8, timestamp: 1_000 }));
  const second = normalizePosition(position({ longitude: 3.37401, accuracy: 7, timestamp: 2_000 }));
  const third = normalizePosition(position({ longitude: 3.374012, accuracy: 7, timestamp: 3_000 }));
  assert.equal(stabilizer.update(first, "reasonable").ready, false);
  assert.equal(stabilizer.update(second, "reasonable").ready, false);
  const ready = stabilizer.update(third, "reasonable");
  assert.equal(ready.ready, true);
  assert.equal(ready.sample.headingDegrees, null);
  const jitter = stabilizer.update(normalizePosition(position({ longitude: 3.374015, accuracy: 6,
    timestamp: 4_000, heading: 90, speed: 1.2 })), "reasonable");
  assert.equal(jitter.reason, "stationary");
  assert.equal(jitter.sample.headingDegrees, null);
  const firstWalking = stabilizer.update(normalizePosition(position({ longitude: 3.37412, accuracy: 7,
    timestamp: 7_000, heading: 90, speed: 1.2 })), "reasonable");
  assert.notEqual(firstWalking.motionState, "walking", "one reading cannot flip motion state");
  const walking = stabilizer.update(normalizePosition(position({ longitude: 3.37422, accuracy: 7,
    timestamp: 9_000, heading: 90, speed: 1.2 })), "reasonable");
  assert.equal(walking.reason, "movement");
  assert.equal(walking.sample.headingDegrees, 90);
  assert.equal(locationQualityLabel(7), "Good");
  assert.equal(locationQualityLabel(40), "Fair");
  assert.equal(locationQualityLabel(80), "Poor");
});

test("public stabilizer never promotes one fix or rapid callbacks without enough observation time", () => {
  const stabilizer = createLocationStabilizer();
  stabilizer.update(normalizePosition(position({ timestamp: 1_000, accuracy: 8 })), "reasonable");
  assert.equal(stabilizer.finalize().reason, "unconfirmed-fix");
  for (const [longitude, timestamp] of [[3.374001, 1_200], [3.374002, 1_400], [3.374003, 1_600]]) {
    const result = stabilizer.update(normalizePosition(position({ longitude, timestamp, accuracy: 8 })), "reasonable");
    assert.equal(result.ready, false, "callback count alone must not prove location convergence");
  }
  const confirmed = stabilizer.update(normalizePosition(position({ longitude: 3.374004,
    timestamp: 2_600, accuracy: 8 })), "reasonable");
  assert.equal(confirmed.ready, true);
});

test("rolling estimate corrects an early biased fix and reports observed instability", () => {
  const stabilizer = createLocationStabilizer();
  stabilizer.update(normalizePosition(position({ longitude: 3.37400, accuracy: 5, timestamp: 1_000 })), "reasonable");
  stabilizer.update(normalizePosition(position({ longitude: 3.37401, accuracy: 5, timestamp: 2_000 })), "reasonable");
  const initial = stabilizer.update(normalizePosition(position({ longitude: 3.374012, accuracy: 5, timestamp: 3_000 })), "reasonable");
  assert.equal(initial.ready, true);
  stabilizer.update(normalizePosition(position({ longitude: 3.37409, accuracy: 6, timestamp: 5_000 })), "reasonable");
  const corrected = stabilizer.update(normalizePosition(position({ longitude: 3.37410, accuracy: 6, timestamp: 8_000 })), "reasonable");
  assert.ok(corrected.sample.longitude > initial.sample.longitude, "sustained later evidence must move a biased centre");
  assert.ok(["stable", "approximate", "unstable"].includes(corrected.confidence));
});

test("robust estimate caps optimistic accuracy and gives recent consistent evidence influence", () => {
  const stabilizer = createLocationStabilizer();
  for (const [longitude, timestamp, accuracy] of [
    [3.37400, 1_000, 7], [3.37401, 2_000, 7], [3.374015, 3_000, 7],
    [3.37409, 4_000, 2],
  ]) stabilizer.update(normalizePosition(position({ longitude, timestamp, accuracy })), "reasonable");
  const optimistic = stabilizer.getStable();
  assert.ok(optimistic.longitude < 3.37406,
    "one claimed 2 m fix must not dominate several consistent readings");

  stabilizer.update(normalizePosition(position({ longitude: 3.37410, timestamp: 7_000, accuracy: 7 })), "reasonable");
  const shifted = stabilizer.update(normalizePosition(position({ longitude: 3.37412, timestamp: 9_000,
    accuracy: 7, speed: 1.2 })), "reasonable");
  assert.ok(shifted.sample.longitude > optimistic.longitude,
    "recent coherent movement should move the rolling estimate");
});

test("movement is uncertainty-aware and requires hysteresis", () => {
  const uncertain = createLocationStabilizer();
  for (const [longitude, timestamp] of [[3.37400, 1_000], [3.374005, 2_000], [3.37401, 3_000]]) {
    uncertain.update(normalizePosition(position({ longitude, timestamp, accuracy: 15 })), "reasonable");
  }
  const fourMetresUncertain = uncertain.update(normalizePosition(position({ longitude: 3.374046,
    timestamp: 5_000, accuracy: 15, speed: 1 })), "reasonable");
  assert.equal(fourMetresUncertain.motionState, "stationary");
  assert.equal(fourMetresUncertain.sample.headingDegrees, null);

  const precise = createLocationStabilizer();
  for (const [longitude, timestamp] of [[3.37400, 1_000], [3.374002, 2_000], [3.374004, 3_000]]) {
    precise.update(normalizePosition(position({ longitude, timestamp, accuracy: 3 })), "reasonable");
  }
  precise.update(normalizePosition(position({ longitude: 3.37404, timestamp: 5_000,
    accuracy: 3, speed: .7, heading: 90 })), "reasonable");
  const confirmed = precise.update(normalizePosition(position({ longitude: 3.37408, timestamp: 7_000,
    accuracy: 3, speed: .7, heading: 90 })), "reasonable");
  assert.equal(confirmed.motionState, "slow-walk");
});

test("impossible jumps are rejected while a strong recovery from a poor fix is allowed", () => {
  const good = normalizePosition(position({ timestamp: 1_000, accuracy: 6 }));
  const jump = assessSample(position({ longitude: 3.3747, timestamp: 2_000, accuracy: 6 }), good);
  assert.equal(jump.reason, "implausible-jump");
  const poor = normalizePosition(position({ timestamp: 1_000, accuracy: 80 }));
  const recovery = assessSample(position({ longitude: 3.3747, timestamp: 2_000, accuracy: 15 }), poor);
  assert.equal(recovery.accepted, true);
});

test("a worse fix is retained briefly but released after the reliable fix ages", () => {
  const stabilizer = createLocationStabilizer({ retainedFixMaximumAgeMs: 8_000 });
  for (const [longitude, timestamp] of [[3.37400, 1_000], [3.374005, 2_000], [3.37401, 3_000]]) {
    stabilizer.update(normalizePosition(position({ longitude, timestamp, accuracy: 6 })), "reasonable");
  }
  const retained = stabilizer.update(normalizePosition(position({ longitude: 3.37402,
    timestamp: 9_000, accuracy: 70 })), "provisional");
  assert.equal(retained.reason, "keep-better-position");
  const released = stabilizer.update(normalizePosition(position({ longitude: 3.37403,
    timestamp: 12_000, accuracy: 70 })), "provisional");
  assert.notEqual(released.reason, "keep-better-position");
  assert.equal(released.sample.deviceAccuracyMetres, 70);
});

test("coherent newer movement overrides an older precise retained position", () => {
  const stabilizer = createLocationStabilizer({ retainedFixMaximumAgeMs: 12_000 });
  for (const [longitude, timestamp] of [[3.374, 1_000], [3.374001, 2_000], [3.374002, 3_000]]) {
    stabilizer.update(normalizePosition(position({ longitude, timestamp, accuracy: 4 })), "reasonable");
  }
  const oldPosition = stabilizer.getStable();
  const first = stabilizer.update(normalizePosition(position({ longitude: 3.37410,
    timestamp: 5_000, accuracy: 15, speed: 1 })), "reasonable");
  assert.equal(first.freshness, "retained");
  assert.equal(first.sample.timestamp, oldPosition.timestamp,
    "a retained coordinate must keep the timestamp of its supporting evidence");

  const moved = stabilizer.update(normalizePosition(position({ longitude: 3.37420,
    timestamp: 7_000, accuracy: 15, speed: 1 })), "reasonable");
  assert.equal(moved.freshness, "fresh");
  assert.equal(moved.reason, "movement");
  assert.ok(moved.sample.longitude > oldPosition.longitude + 0.00005,
    "several coherent fresh fixes must displace an older precise cluster");
  assert.equal(moved.sample.timestamp, 7_000);
});

test("fresh seven-to-ten metre fixes can replace an older four-metre fix", () => {
  const stabilizer = createLocationStabilizer();
  for (const [longitude, timestamp] of [[3.374, 1_000], [3.374001, 2_000], [3.374002, 3_000]]) {
    stabilizer.update(normalizePosition(position({ longitude, timestamp, accuracy: 4 })), "reasonable");
  }
  let result;
  for (const [longitude, timestamp] of [[3.37408, 5_000], [3.37416, 7_000], [3.37424, 9_000]]) {
    result = stabilizer.update(normalizePosition(position({ longitude, timestamp,
      accuracy: 9, speed: 1 })), "reasonable");
  }
  assert.equal(result.freshness, "fresh");
  assert.equal(result.reason, "movement");
  assert.ok(result.sample.longitude > 3.37408);
});

test("geolocation service reports unsupported and cleans up its watcher", () => {
  let unsupported = null;
  const missing = createGeolocationService({ geolocation: null });
  assert.equal(missing.start(() => {}, (state) => { unsupported = state; }), false);
  assert.equal(unsupported, "unsupported");

  let initialSuccess;
  let watchSuccess;
  let initialOptions;
  let watchOptions;
  const cleared = [];
  const geolocation = {
    getCurrentPosition(success, _error, options) { initialSuccess = success; initialOptions = options; },
    watchPosition(success, _error, options) { watchSuccess = success; watchOptions = options; return 17; },
    clearWatch(id) { cleared.push(id); },
  };
  const received = [];
  const service = createGeolocationService({ geolocation });
  assert.equal(service.start((sample) => received.push(sample), () => {}), true);
  assert.equal(initialOptions.maximumAge, 0);
  assert.deepEqual(initialOptions, GEOLOCATION_OPTIONS.initial);
  initialSuccess(position());
  assert.equal(watchOptions.maximumAge, 0);
  assert.deepEqual(watchOptions, GEOLOCATION_OPTIONS.watch);
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

test("fresh reacquisition replaces the watcher without duplicating it", () => {
  const initialCallbacks = [];
  const initialOptions = [];
  const cleared = [];
  let watchId = 0;
  const geolocation = {
    getCurrentPosition(success, _error, options) { initialCallbacks.push(success); initialOptions.push(options); },
    watchPosition() { watchId += 1; return watchId; },
    clearWatch(id) { cleared.push(id); },
  };
  const service = createGeolocationService({ geolocation });
  service.start(() => {}, () => {});
  initialCallbacks[0](position());
  assert.equal(watchId, 1);
  assert.equal(service.reacquire(), true);
  assert.deepEqual(cleared, [1]);
  assert.deepEqual(initialOptions.map((options) => options.maximumAge), [0, 0]);
  initialCallbacks[1](position({ timestamp: 2_000 }));
  assert.equal(watchId, 2, "reacquisition starts exactly one replacement watcher");
  service.stop();
  assert.deepEqual(cleared, [1, 2]);
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
  const selectors = ["#locate-me", "#recenter-me", "#stop-location",
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
  assert.equal(controller.getState(), "warming-up");
  positionCallback(position({ longitude: 3.374012, timestamp: 3_000, accuracy: 9 }));
  assert.equal(controller.getState(), "warming-up");
  positionCallback(position({ longitude: 3.374014, timestamp: 4_000, accuracy: 8 }));
  assert.equal(controller.getState(), "active");
  assert.equal(shown.length, 1);
  assert.equal(shown[0][1].focus, true);
  assert.match(harness.get("#location-accuracy").textContent, /Location quality: Good.*estimated uncertainty/);
  positionCallback(position({ longitude: 3.39, timestamp: 5_000, accuracy: 20 }));
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
  positionCallback(position({longitude:3.374012,timestamp:3_000,accuracy:9}));
  positionCallback(position({longitude:3.374014,timestamp:4_000,accuracy:8}));
  assert.ok(controller.getAcceptedPosition());
  errorCallback("unavailable");
  assert.equal(controller.getAcceptedPosition(),null);
  assert.equal(controller.getState(),"unavailable");
  assert.equal(cleared,1);
});

test("retryable GPS errors keep acquisition alive and do not clear a confirmed position", () => {
  const harness = locationHarness();
  let positionCallback;
  let errorCallback;
  let cleared = 0;
  const shown = [];
  const controller = createUserLocation({
    element: harness.root,
    service: {
      isSupported: true,
      start(onPosition, onError) { positionCallback = onPosition; errorCallback = onError; return true; },
      stop() {}, resume() {},
    },
    documentObject: { hidden: false, addEventListener() {}, removeEventListener() {} },
    onPosition: (sample) => shown.push(sample), onClear() { cleared += 1; }, onRecenter() {},
  });
  controller.start();
  errorCallback("timed-out", { phase: "initial", willRetry: true });
  assert.equal(controller.getState(), "retrying");
  assert.equal(cleared, 0);
  for (const [longitude, timestamp] of [
    [3.374, 1_000], [3.374001, 2_000], [3.374002, 3_000], [3.374003, 4_000],
  ]) positionCallback(position({ longitude, timestamp, accuracy: 6 }));
  assert.equal(controller.getState(), "active");
  const confirmedTimestamp = controller.getAcceptedPosition().timestamp;
  errorCallback("unavailable", { phase: "watch", willRetry: true });
  assert.equal(controller.getState(), "retained");
  assert.equal(controller.getAcceptedPosition().timestamp, confirmedTimestamp,
    "a transient error must not make retained evidence appear newer");
  assert.equal(cleared, 0);
  assert.equal(shown.at(-1).navigationReady, true);
  controller.destroy();
});

test("initial acquisition deadline never publishes one unconfirmed fix and keeps trying", () => {
  const harness = locationHarness();
  let positionCallback;
  const deadlines = new Map();
  let nextDeadline = 0;
  const shown = [];
  const controller = createUserLocation({
    element: harness.root,
    service: { isSupported: true, start(onPosition) { positionCallback = onPosition; return true; },
      stop() {}, resume() {} },
    documentObject: { hidden: false, addEventListener() {}, removeEventListener() {} },
    setDeadline(callback, delay) { const id = ++nextDeadline; deadlines.set(id, { callback, delay }); return id; },
    clearDeadline(id) { deadlines.delete(id); },
    onPosition: (sample) => shown.push(sample), onClear() {}, onRecenter() {},
  });
  controller.start();
  positionCallback(position({ accuracy: 18, timestamp: 1_000 }));
  assert.equal(shown.length, 0);
  const acquisition = [...deadlines.values()].find((item) => item.delay === 20_000);
  acquisition.callback();
  assert.equal(shown.length, 0, "one accurate-looking callback is not enough evidence to place the user");
  assert.equal(controller.getAcceptedPosition(), null);
  assert.equal(controller.getState(), "needs-precision");

  for (const [longitude, timestamp] of [[3.37401, 2_000], [3.374012, 3_000], [3.374014, 4_000]]) {
    positionCallback(position({ longitude, accuracy: 8, timestamp }));
  }
  assert.equal(shown.length, 1, "a later coherent cluster can complete the still-running acquisition");
  assert.equal(shown[0].navigationReady, true);
  controller.destroy();
});

test("retained position is labelled honestly and expires into fresh reacquisition", () => {
  const harness = locationHarness();
  let positionCallback;
  let reacquisitions = 0;
  let clock = 4_000;
  let nextDeadline = 0;
  const deadlines = new Map();
  const shown = [];
  const controller = createUserLocation({
    element: harness.root,
    service: {
      isSupported: true,
      start(onPosition) { positionCallback = onPosition; return true; },
      stop() {}, resume() {}, reacquire() { reacquisitions += 1; return true; },
    },
    documentObject: { hidden: false, addEventListener() {}, removeEventListener() {} },
    now: () => clock,
    setDeadline(callback, delay) {
      const id = ++nextDeadline; deadlines.set(id, { callback, delay }); return id;
    },
    clearDeadline(id) { deadlines.delete(id); },
    onPosition: (sample, meta) => shown.push({ sample, meta }),
    onClear() {}, onRecenter() {},
  });
  controller.start();
  for (const [longitude, timestamp, accuracy] of [
    [3.374, 1_000, 5], [3.374001, 2_000, 5], [3.374002, 3_000, 5], [3.374003, 4_000, 5],
  ]) positionCallback(position({ longitude, timestamp, accuracy }));
  positionCallback(position({ longitude: 3.37401, timestamp: 5_000, accuracy: 100 }));
  assert.equal(shown.at(-1).meta.freshness, "retained");
  assert.match(harness.get("#location-accuracy").textContent, /Recent reliable position/);
  assert.doesNotMatch(harness.get("#location-accuracy").textContent, /Location quality: Good/);

  clock = 4_000 + LIVE_LOCATION_STALE_AFTER_MS + 1;
  const freshnessTimer = [...deadlines.values()].find((item) => item.delay <= LIVE_LOCATION_STALE_AFTER_MS);
  freshnessTimer.callback();
  assert.equal(controller.getAcceptedPosition(), null);
  assert.equal(controller.getState(), "refreshing");
  assert.equal(reacquisitions, 1);
  controller.destroy();
});

test("manual refresh discards old evidence and requires a newly confirmed fix", () => {
  const harness = locationHarness();
  let positionCallback;
  let reacquisitions = 0;
  const shown = [];
  const service = {
    isSupported: true,
    start(onPosition) { positionCallback = onPosition; return true; },
    stop() {}, resume() {},
    reacquire() { reacquisitions += 1; return true; },
  };
  const controller = createUserLocation({
    element: harness.root, service,
    documentObject: { hidden: false, addEventListener() {}, removeEventListener() {} },
    now: () => 6_000,
    onPosition: (sample) => shown.push(sample), onClear() {}, onRecenter() {},
  });
  controller.start();
  for (const [longitude, timestamp] of [
    [3.374, 1_000], [3.374001, 2_000], [3.374002, 3_000], [3.374003, 4_000],
  ]) positionCallback(position({ longitude, timestamp, accuracy: 6 }));
  const before = shown.length;
  assert.equal(controller.refresh(), true);
  assert.equal(reacquisitions, 1);
  assert.equal(controller.getAcceptedPosition(), null);
  positionCallback(position({ longitude: 3.3742, timestamp: 6_000, accuracy: 6 }));
  assert.equal(shown.length, before, "one callback must not reuse evidence from the previous session");
  for (const [longitude, timestamp] of [
    [3.374201, 7_000], [3.374202, 8_000], [3.374203, 9_000],
  ]) positionCallback(position({ longitude, timestamp, accuracy: 6 }));
  assert.equal(shown.length, before + 1);
  assert.equal(controller.getAcceptedPosition().navigationReady, true);
  controller.destroy();
});

test("visibility resume keeps a recent fix but hard-resets stale session evidence", () => {
  const harness = locationHarness();
  let positionCallback;
  let visibilityCallback;
  let clock = 4_000;
  let resumes = 0;
  let reacquisitions = 0;
  const fakeDocument = {
    hidden: false,
    addEventListener(type, callback) { if (type === "visibilitychange") visibilityCallback = callback; },
    removeEventListener() {},
  };
  const service = {
    isSupported: true,
    start(onPosition) { positionCallback = onPosition; return true; },
    stop() {}, resume() { resumes += 1; }, reacquire() { reacquisitions += 1; return true; },
  };
  const controller = createUserLocation({
    element: harness.root, service, documentObject: fakeDocument, now: () => clock,
    onPosition() {}, onClear() {}, onRecenter() {},
  });
  controller.start();
  for (const [longitude, timestamp] of [
    [3.374, 1_000], [3.374001, 2_000], [3.374002, 3_000], [3.374003, 4_000],
  ]) positionCallback(position({ longitude, timestamp, accuracy: 6 }));

  fakeDocument.hidden = true; visibilityCallback();
  clock = 29_000;
  fakeDocument.hidden = false; visibilityCallback();
  assert.equal(resumes, 1);
  assert.equal(reacquisitions, 0, "a 25-second-old stationary fix remains within route tolerance");

  fakeDocument.hidden = true; visibilityCallback();
  clock = 34_001;
  fakeDocument.hidden = false; visibilityCallback();
  assert.equal(reacquisitions, 1);
  assert.equal(controller.getAcceptedPosition(), null);
  positionCallback(position({ longitude: 3.3742, timestamp: 35_000, accuracy: 6 }));
  assert.equal(controller.getAcceptedPosition(), null,
    "one resumed callback cannot inherit the pre-background stabilizer history");
  for (const [longitude, timestamp] of [
    [3.374201, 36_000], [3.374202, 37_000], [3.374203, 38_000],
  ]) positionCallback(position({ longitude, timestamp, accuracy: 6 }));
  assert.equal(controller.getAcceptedPosition().navigationReady, true);
  controller.destroy();
});

test("outside-area live fixes never render or move the map", () => {
  const harness=locationHarness(); let positionCallback; let shown=0; let cleared=0;
  const service={isSupported:true,start(onPosition){positionCallback=onPosition;return true;},stop(){},resume(){}};
  const controller=createUserLocation({element:harness.root,service,
    supportedArea:{contains:()=>false},
    documentObject:{hidden:false,addEventListener(){},removeEventListener(){}},
    onPosition(){shown+=1;},onClear(){cleared+=1;},onRecenter(){}});
  controller.start();
  positionCallback(position({longitude:3.45,latitude:6.60}));
  positionCallback(position({longitude:3.45001,latitude:6.60,timestamp:2_000}));
  positionCallback(position({longitude:3.450012,latitude:6.60,timestamp:3_000}));
  positionCallback(position({longitude:3.450014,latitude:6.60,timestamp:4_000}));
  assert.equal(shown,0);
  assert.equal(controller.getAcceptedPosition(),null);
  assert.equal(controller.getState(),"outside-area");
  assert.equal(cleared,1);
  assert.match(harness.get("#location-message").textContent,/outside the YabaTech mapping area/);
});
