import assert from "node:assert/strict";
import test from "node:test";

import { calculateRoutePadding, routeBounds } from "../../static/yct_map/js/map.js";

test("YabaTech route bounds retain GeoJSON longitude latitude order", () => {
  assert.deepEqual(routeBounds([[3.37378, 6.51828], [3.37424, 6.51857]]),
    [[3.37378, 6.51828], [3.37424, 6.51857]]);
  assert.throws(() => routeBounds([[6.51828, 3.37378], [6.51857, 3.37424]]), /coordinate order/);
  assert.throws(() => routeBounds([[3.37, 6.52], [Infinity, 6.52]]), /finite/);
});

test("route bounds include an appended exact entrance-arrival connector", () => {
  const entrance = [3.37472, 6.51812];
  const bounds = routeBounds([[3.3738, 6.5183], [3.3745, 6.5182], entrance]);
  assert.equal(bounds[1][0], entrance[0]);
  assert.ok(bounds[0][1] <= entrance[1] && bounds[1][1] >= entrance[1]);
});

test("mobile route camera padding leaves a usable map viewport", () => {
  const padding = calculateRoutePadding({ mobile: true, panelHeight: 600, panelWidth: 390,
    discoveryBottom: 190, viewportHeight: 700 });
  assert.deepEqual(padding, { top: 206, right: 24, bottom: 168, left: 24 });
  assert.ok(padding.top + padding.bottom < 700 * 0.60);
});

test("desktop route camera retains side-panel padding", () => {
  assert.deepEqual(calculateRoutePadding({ mobile: false, panelHeight: 500, panelWidth: 400,
    discoveryBottom: 180, viewportHeight: 800 }), { top: 112, right: 448, bottom: 72, left: 72 });
});
