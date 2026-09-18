import assert from "node:assert/strict";
import test from "node:test";
import { createOffRouteDetector, routeThresholds } from "../../static/yct_map/js/off-route.js";
import { offRouteTrace, poorAccuracyTrace } from "./fixtures/p3s3-traces.mjs";

const route = [[3.3740, 6.5180], [3.3750, 6.5180]];
const sample = (longitude, latitude, timestamp, accuracyMetres = 5) =>
  ({ longitude, latitude, timestamp, accuracyMetres });

test("accuracy-aware thresholds stay bounded", () => {
  assert.deepEqual(routeThresholds(3), { onRouteMetres: 8, offRouteMetres: 12 });
  assert.deepEqual(routeThresholds(15), { onRouteMetres: 15, offRouteMetres: 23 });
  assert.deepEqual(routeThresholds(25), { onRouteMetres: 20, offRouteMetres: 30 });
});

test("one lateral anomaly does not reroute and route recovery cancels it", () => {
  const detector = createOffRouteDetector();
  assert.equal(detector.evaluate(sample(3.3741, 6.5182, 1_000), route).shouldReroute, false);
  assert.equal(detector.evaluate(sample(3.3742, 6.5180, 5_000), route).state, "following");
});

test("poor accuracy creates uncertainty and never confirms departure", () => {
  const detector = createOffRouteDetector();
  for (const timestamp of [1_000, 5_000, 9_000, 13_000]) {
    const result = detector.evaluate(sample(3.3742, 6.5185, timestamp, 60), route);
    assert.equal(result.shouldReroute, false);
    assert.equal(result.state, "checking-position");
  }
});

test("three reliable moving deviations over eight seconds confirm once", () => {
  const detector = createOffRouteDetector();
  assert.equal(detector.evaluate(sample(3.3741, 6.5182, 1_000), route).shouldReroute, false);
  assert.equal(detector.evaluate(sample(3.3742, 6.5182, 5_000), route).shouldReroute, false);
  const confirmed = detector.evaluate(sample(3.3743, 6.5182, 9_000), route);
  assert.equal(confirmed.state, "off-route-confirmed");
  assert.equal(confirmed.shouldReroute, true);
  detector.markRerouting();
  assert.equal(detector.evaluate(sample(3.3744, 6.5182, 13_000), route).shouldReroute, false);
});

test("backtracking inside the route corridor remains on route", () => {
  const detector = createOffRouteDetector();
  detector.evaluate(sample(3.3748, 6.5180, 1_000), route);
  assert.equal(detector.evaluate(sample(3.3744, 6.5180, 5_000), route).state, "following");
});

test("arrival takes precedence and successful reroute enforces cooldown plus movement", () => {
  const detector = createOffRouteDetector();
  assert.equal(detector.evaluate(sample(3.3742, 6.5184, 1_000), route, { arrived: true }).state, "arrived");
  detector.recover();
  detector.markSuccess(10_000);
  for (const [longitude, timestamp] of [[3.3741, 21_000], [3.3742, 25_000], [3.3743, 29_000]]) {
    assert.equal(detector.evaluate(sample(longitude, 6.5182, timestamp), route).shouldReroute, false);
  }
});

test("repository-derived trace ignores one anomaly then confirms the mapped-path deviation", () => {
  const detector = createOffRouteDetector();
  const asSample = ([longitude, latitude], timestamp, accuracyMetres = offRouteTrace.accuracyMetres) =>
    ({ longitude, latitude, timestamp, accuracyMetres });
  detector.evaluate(asSample(offRouteTrace.start, 1_000), offRouteTrace.initialRoute);
  detector.evaluate(asSample(offRouteTrace.oneNoisySample, 5_000), offRouteTrace.initialRoute);
  assert.equal(detector.evaluate(asSample(offRouteTrace.recovery, 9_000), offRouteTrace.initialRoute).state, "following");
  let result;
  offRouteTrace.deviationOnWay1335008711.forEach((point, index) => {
    result = detector.evaluate(asSample(point, 29_000 + index * 4_000), offRouteTrace.initialRoute);
  });
  assert.equal(result.shouldReroute, true);
});

test("repository-derived poor-accuracy trace causes no false reroute", () => {
  const detector = createOffRouteDetector();
  let result;
  for (const timestamp of [1_000, 5_000, 9_000]) {
    result = detector.evaluate(sample(...poorAccuracyTrace.uncertain, timestamp, poorAccuracyTrace.accuracyMetres), route);
  }
  assert.equal(result.state, "checking-position");
  assert.equal(result.shouldReroute, false);
});
