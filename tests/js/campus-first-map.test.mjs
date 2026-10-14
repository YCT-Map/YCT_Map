import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  CAMPUS_CORE_CAMERA,
  CAMPUS_FILL_LAYER_ID,
  CAMPUS_INTERACTIVE_LAYER_ORDER,
  CAMPUS_LABEL_LAYER_ID,
  CAMPUS_LINE_LAYER_ID,
  DESTINATION_POINT_LAYER_ID,
  NAVIGATION_FOREGROUND_LAYER_ORDER,
  SELECTED_DESTINATION_MARKER_LAYER_ID,
  bufferBoundsMetres,
  campusCameraConstraints,
  campusCoreCamera,
  campusOrientationLayerDefinitions,
} from "../../static/yct_map/js/map.js";

const APPROVED_CENTRE = [3.37424, 6.51857];

test("camera constraints retain the campus context limits", () => {
  const bounds = [[3.3714662, 6.5161567], [3.3770046, 6.5209790]];
  const buffered = bufferBoundsMetres(bounds, 400);
  const constraints = campusCameraConstraints(bounds);
  assert.equal(constraints.minZoom, 15);
  assert.equal(constraints.maxZoom, 20);
  assert.deepEqual(constraints.maxBounds, buffered);
  assert.ok(buffered[0][0] < bounds[0][0] && buffered[0][1] < bounds[0][1]);
  assert.ok(buffered[1][0] > bounds[1][0] && buffered[1][1] > bounds[1][1]);
});

test("desktop campus core uses the approved centre and a closer camera than overview", () => {
  const camera = campusCoreCamera({ centre: APPROVED_CENTRE, overviewZoom: 16, viewportWidth: 1440 });
  assert.deepEqual(camera.center, APPROVED_CENTRE);
  assert.notEqual(camera.center, APPROVED_CENTRE, "camera receives its own immutable centre array");
  assert.equal(camera.zoom, CAMPUS_CORE_CAMERA.desktop.minZoom);
  assert.ok(camera.zoom > 16);

  const upperClamp = campusCoreCamera({ centre: APPROVED_CENTRE, overviewZoom: 19, viewportWidth: 1440 });
  assert.equal(upperClamp.zoom, CAMPUS_CORE_CAMERA.desktop.maxZoom);
});

test("mobile campus core uses a separately tuned responsive profile", () => {
  const camera = campusCoreCamera({ centre: APPROVED_CENTRE, overviewZoom: 16.4, viewportWidth: 390 });
  assert.equal(camera.zoom, 17.25);
  assert.ok(camera.zoom >= CAMPUS_CORE_CAMERA.mobile.minZoom);
  assert.ok(camera.zoom <= CAMPUS_CORE_CAMERA.mobile.maxZoom);
  assert.equal(CAMPUS_CORE_CAMERA.mobileBreakpoint, 672);

  assert.equal(campusCoreCamera({ centre: APPROVED_CENTRE, viewportWidth: 390 }).zoom,
    CAMPUS_CORE_CAMERA.mobile.fallbackZoom);
  assert.equal(campusCoreCamera({ centre: APPROVED_CENTRE, viewportWidth: 1440 }).zoom,
    CAMPUS_CORE_CAMERA.desktop.fallbackZoom);
});

test("campus core rejects an invented or malformed centre", () => {
  assert.throws(() => campusCoreCamera({ centre: null, overviewZoom: 16, viewportWidth: 390 }),
    /approved campus centre/);
  assert.throws(() => campusCoreCamera({ centre: [3.37, Number.NaN], overviewZoom: 16, viewportWidth: 390 }),
    /approved campus centre/);
});

test("Liberty remains provider-rendered while YCT adds only orientation overlays", () => {
  const layers = campusOrientationLayerDefinitions();
  assert.equal(layers.fill.id, CAMPUS_FILL_LAYER_ID);
  assert.equal(layers.fill.source, "yabatech-campus-orientation");
  assert.equal(layers.fill.paint["fill-opacity"], 0.08);
  assert.equal(layers.line.id, CAMPUS_LINE_LAYER_ID);
  assert.equal(layers.line.paint["line-color"], "#2f7656");
  assert.deepEqual(layers.line.paint["line-opacity"],
    ["interpolate", ["linear"], ["zoom"], 15, 0.55, 17, 0.38, 20, 0.22]);
  assert.deepEqual(layers.line.paint["line-width"],
    ["interpolate", ["linear"], ["zoom"], 15, 1.5, 17, 1, 20, 0.6]);
  assert.equal(layers.label.id, CAMPUS_LABEL_LAYER_ID);
  assert.deepEqual(Object.keys(layers).sort(), ["fill", "label", "line"]);

  const source = readFileSync(new URL("../../static/yct_map/js/map.js", import.meta.url), "utf8");
  assert.equal(source.includes("setLayerZoomRange"), false);
  assert.equal(source.includes("sourceLayer === \"poi\""), false);
  assert.equal(source.includes("fill-extrusion"), false);
  assert.equal(source.includes("yabatech-campus-context-mask"), false);
  assert.equal(source.includes("yabatech-campus-building-shadow"), false);
});

test("campus overlays remain below destinations and navigation", () => {
  const index = (id) => CAMPUS_INTERACTIVE_LAYER_ORDER.indexOf(id);
  assert.ok(index(CAMPUS_FILL_LAYER_ID) < index(CAMPUS_LINE_LAYER_ID));
  assert.ok(index(CAMPUS_LINE_LAYER_ID) < index(CAMPUS_LABEL_LAYER_ID));
  assert.ok(index(CAMPUS_LABEL_LAYER_ID) < index(DESTINATION_POINT_LAYER_ID));
  assert.ok(index(DESTINATION_POINT_LAYER_ID) < index(SELECTED_DESTINATION_MARKER_LAYER_ID));
  assert.ok(index(SELECTED_DESTINATION_MARKER_LAYER_ID) < index("user-demo-route-line"));
  assert.ok(index("user-demo-route-line") < index("user-route-endpoint-circles"));
  assert.ok(index("user-route-endpoint-circles") < index("live-user-location-dot"));
  assert.equal(NAVIGATION_FOREGROUND_LAYER_ORDER.at(-1), "live-user-location-chevron");
});

test("initial load and Home use core framing while overview remains independently available", () => {
  const source = readFileSync(new URL("../../static/yct_map/js/map.js", import.meta.url), "utf8");
  assert.match(source, /else\s*{\s*focusCampusCore\(\{ animate: false \}\)/);
  assert.match(source, /CampusFocusControl\(\(\) => focusCampusCore\(\{ resetNavigation: true \}\)\)/);
  assert.match(source, /function focusCampusOverview\(/);
  assert.match(source, /map\.fitBounds\(campusBounds/);
  assert.match(source, /return \{ focus, focusCampus: focusCampusCore, focusCampusCore, focusCampusOverview,/);
});

test("route and destination cameras remain separate while live navigation leaves camera control to the user", () => {
  const source = readFileSync(new URL("../../static/yct_map/js/map.js", import.meta.url), "utf8");
  assert.match(source, /focusDestination\(map, feature\)/);
  assert.match(source, /map\.fitBounds\(routeBounds\(fitCoordinates\), \{/);
  assert.match(source, /padding: routePadding\(\), maxZoom: 17\.5/);
  assert.match(source, /if \(!replacement\)/);
  assert.match(source, /recenterCameraOptions\(latestUserPosition, map\.getZoom\(\), reducedMotion\)/);
  assert.doesNotMatch(source, /scheduleFollowCamera|applyFollowCamera/);
});
