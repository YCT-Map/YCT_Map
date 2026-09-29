import assert from "node:assert/strict";
import test from "node:test";
import { createLiveRouteTracker, formatEta, projectOntoRoute,
  sliceRouteAtDistance } from "../../static/yct_map/js/live-route-progress.js";

const route = [[3.3740, 6.5180], [3.3745, 6.5180], [3.3750, 6.5185]];

test("progress projects onto the complete route geometry", () => {
  const projection = projectOntoRoute([3.37475, 6.51825], route);
  assert.ok(projection.along > 55);
  assert.ok(projection.distance < 1);
});

test("tracker keeps progress stable and confirms arrival twice", () => {
  const tracker = createLiveRouteTracker(route, 134);
  let result = tracker.update({ longitude: 3.3745, latitude: 6.5180, accuracyMetres: 8, timestamp: 1_000 });
  const progressed = result.progressMetres;
  result = tracker.update({ longitude: 3.3741, latitude: 6.5180, accuracyMetres: 8, timestamp: 5_000 });
  assert.equal(result.progressMetres, progressed, "one backward sample must not move progress backward");
  tracker.update({ longitude: 3.3750, latitude: 6.5185, accuracyMetres: 8, timestamp: 10_000 });
  result = tracker.update({ longitude: 3.3750, latitude: 6.5185, accuracyMetres: 8, timestamp: 14_000 });
  assert.equal(result.state, "arrived");
});

test("dynamic ETA uses a filtered plausible walking pace", () => {
  const tracker = createLiveRouteTracker(route, 134);
  const samples = [
    [3.3740, 1_000], [3.37405, 5_000], [3.37410, 9_000], [3.37415, 13_000],
  ];
  let result;
  for (const [longitude, timestamp] of samples) {
    result = tracker.update({ longitude, latitude: 6.5180, accuracyMetres: 5, timestamp });
  }
  assert.equal(result.etaSource, "live");
  assert.equal(formatEta(70), "~2 min");
});

test("route replacement resets progress while preserving trustworthy walking pace", () => {
  const tracker = createLiveRouteTracker(route, 134);
  for (const [longitude, timestamp] of [[3.3740, 1_000], [3.37405, 5_000], [3.37410, 9_000], [3.37415, 13_000]]) {
    tracker.update({ longitude, latitude: 6.5180, accuracyMetres: 5, timestamp });
  }
  tracker.replaceRoute([[3.37415, 6.5180], [3.3750, 6.5180]], 94);
  const result = tracker.update({ longitude: 3.37415, latitude: 6.5180, accuracyMetres: 5, timestamp: 17_000 });
  assert.equal(result.progressMetres, 0);
  assert.equal(result.etaSource, "live");
});

test("route slicing handles start, mid-leg, exact vertex, end, and does not mutate input", () => {
  const input = route.map((point) => [...point]);
  const firstLeg = projectOntoRoute(route[1], route).along;
  const start = sliceRouteAtDistance(route, 0);
  assert.deepEqual(start.completedCoordinates, [route[0]]);
  assert.deepEqual(start.remainingCoordinates, route);

  const middle = sliceRouteAtDistance(route, firstLeg / 2);
  assert.equal(middle.completedCoordinates.length, 2);
  assert.deepEqual(middle.completedCoordinates.at(-1), middle.remainingCoordinates[0]);
  assert.ok(middle.progressPoint[0] > route[0][0] && middle.progressPoint[0] < route[1][0]);

  const vertex = sliceRouteAtDistance(route, firstLeg);
  assert.deepEqual(vertex.progressPoint, route[1]);
  assert.deepEqual(vertex.completedCoordinates.at(-1), route[1]);
  assert.deepEqual(vertex.remainingCoordinates[0], route[1]);

  const end = sliceRouteAtDistance(route, Number.POSITIVE_INFINITY);
  assert.deepEqual(end.completedCoordinates, route);
  assert.deepEqual(end.remainingCoordinates, [route.at(-1)]);
  assert.deepEqual(route, input);
});

test("route slicing tolerates empty, single-point and degenerate legs", () => {
  assert.deepEqual(sliceRouteAtDistance([], 10).remainingCoordinates, []);
  assert.deepEqual(sliceRouteAtDistance([[3.374, 6.518]], 10).remainingCoordinates, [[3.374, 6.518]]);
  const degenerate = [[3.374, 6.518], [3.374, 6.518], [3.375, 6.518]];
  const sliced = sliceRouteAtDistance(degenerate, 20);
  assert.ok(sliced.remainingCoordinates.length >= 2);
  assert.ok(sliced.progressPoint[0] > 3.374);
});
