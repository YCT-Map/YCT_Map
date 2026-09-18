import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const css = readFileSync(new URL("../../static/yct_map/css/app.css", import.meta.url), "utf8");

test("mobile discovery keeps category chips horizontally reachable", () => {
  assert.match(css, /\.category-list\s*\{[^}]*overflow-x:\s*auto/s);
  assert.match(css, /scroll-snap-type:\s*x proximity/);
  assert.match(css, /\.category-chip\s*\{[^}]*min-height:\s*2\.75rem/s);
});

test("mobile sheets are height-capped and internally scrollable", () => {
  assert.match(css, /\.destination-panel,\s*\.user-route-panel,\s*\.contribution-panel\s*\{[^}]*max-height:\s*70dvh[^}]*overflow-y:\s*auto/s);
  assert.match(css, /@media \(max-height:\s*25rem\)[\s\S]*max-height:\s*68dvh/);
});

test("narrow route actions use a touch-sized responsive grid", () => {
  assert.match(css, /\.route-actions\s*\{[^}]*grid-template-columns:\s*repeat\(2, minmax\(0, 1fr\)\)/s);
  assert.match(css, /\.route-actions button\s*\{[^}]*min-height:\s*2\.75rem/s);
  assert.match(css, /@media \(max-width:\s*20rem\)[\s\S]*\.route-actions\s*\{\s*grid-template-columns:\s*1fr/);
});

test("foreground sheets suppress competing narrow-screen controls", () => {
  for (const state of ["choosing-origin", "route-available", "contributing"]) {
    assert.match(css, new RegExp(`data-interface-state=\\"${state}\\"`));
  }
  assert.match(css, /\.maplibregl-ctrl-bottom-right/);
  assert.match(css, /pointer-events:\s*none/);
});
