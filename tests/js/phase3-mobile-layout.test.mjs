import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const css = readFileSync(new URL("../../static/yct_map/css/app.css", import.meta.url), "utf8");

test("mobile discovery keeps category chips horizontally reachable", () => {
  assert.match(css, /\.category-list\s*\{[^}]*overflow-x:\s*auto/s);
  assert.match(css, /scroll-snap-type:\s*x proximity/);
  assert.match(css, /\.category-chip\s*\{[^}]*min-height:\s*2\.75rem/s);
  assert.match(css, /mask-image:\s*linear-gradient/);
  assert.match(css, /\.category-list::\-webkit-scrollbar\s*\{[^}]*display:\s*none[^}]*height:\s*0/s);
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

test("route panel and controls cannot exceed the viewport", () => {
  assert.match(css, /\.user-route-panel\s*\{[^}]*max-width:\s*100%[^}]*overflow-x:\s*hidden/s);
  assert.match(css, /@media \(min-width:\s*42rem\)[\s\S]*\.user-route-panel\s*\{[^}]*max-width:\s*calc\(100vw - var\(--safe-left\) - var\(--safe-right\)\)/s);
  assert.match(css, /\.active-route-summary\s*>\s*\*\s*\{\s*min-width:\s*0/);
  assert.match(css, /\.route-end-action\s*\{[^}]*flex:\s*0 0 auto/s);
  assert.match(css, /\.route-actions button\s*\{[^}]*flex:\s*1 1 8rem[^}]*min-width:\s*0[^}]*overflow-wrap:\s*anywhere/s);
});

test("foreground sheets suppress competing narrow-screen controls", () => {
  for (const state of ["choosing-origin", "route-available", "contributing"]) {
    assert.match(css, new RegExp(`data-interface-state=\\"${state}\\"`));
  }
  assert.match(css, /\.maplibregl-ctrl-bottom-right/);
  assert.match(css, /pointer-events:\s*none/);
});

test("mobile header and search stay compact without shrinking touch targets", () => {
  assert.match(css, /Consolidated Phase 4 mobile public-map HUD/);
  assert.match(css, /\.team-menu summary\s*\{[^}]*min-height:\s*2\.75rem/s);
  assert.match(css, /\.search-form\s*\{[^}]*min-height:\s*2\.75rem/s);
  assert.match(css, /\.brand\s*\{[^}]*min-height:\s*2\.75rem/s);
});

test("idle locate control is compact and lower-right controls keep separate offsets", () => {
  assert.match(css, /#user-location-controls\[data-state="idle"\]\s*\{[^}]*width:\s*auto[^}]*box-shadow:\s*none/s);
  assert.match(css, /data-state="idle"\]\s+\.locate-action\s*\{[^}]*min-height:\s*2\.75rem/s);
  assert.match(css, /#user-location-controls\s*\{[^}]*7\.3rem/s);
  assert.match(css, /\.maplibregl-ctrl-bottom-right\s*\{[^}]*2\.35rem/s);
});

test("mobile attribution stays compact until the legal text is opened", () => {
  assert.match(css, /\.maplibregl-ctrl-attrib\.maplibregl-compact:not\(\.maplibregl-compact-show\)/);
  assert.match(css, /\.maplibregl-ctrl-attrib-inner\s*\{[^}]*display:\s*none/s);
  assert.match(css, /\.maplibregl-compact\.maplibregl-compact-show\s*\{[^}]*max-width:/s);
});

test("successful mobile routing uses a compact expandable map-first card", () => {
  assert.match(css, /data-route-state="active"[^}]*\{[^}]*max-height:\s*min\(28dvh, 10\.5rem\)/s);
  assert.match(css, /data-details-expanded="true"[^}]*\{[^}]*max-height:\s*70dvh/s);
  assert.match(css, /data-route-state="active"[^}]*\.route-expanded-content\s*\{\s*display:\s*none/s);
  assert.match(css, /data-details-expanded="true"[^}]*\.route-expanded-content\s*\{\s*display:\s*block/s);
});
