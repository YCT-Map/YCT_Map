import assert from "node:assert/strict";
import test from "node:test";
import { createLiveRouteTracker, formatEta, projectOntoRoute } from "../../static/yct_map/js/live-route-progress.js";

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
