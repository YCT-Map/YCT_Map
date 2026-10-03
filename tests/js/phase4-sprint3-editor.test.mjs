import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const css = fs.readFileSync("static/yct_map/css/editor.css", "utf8");
const placeTemplate = fs.readFileSync("templates/editor/place_form.html", "utf8");
const placeScript = fs.readFileSync("static/yct_map/js/editor-place-map.js", "utf8");
const segmentScript = fs.readFileSync("static/yct_map/js/editor-segment-map.js", "utf8");

test("checkboxes are excluded from full-width editor input styling", () => {
  assert.match(css, /\.editor-input:not\(\[type=checkbox\]\)/);
  assert.match(css, /input\[type=checkbox\].*order:\s*-1/);
});

test("checkpoint checkbox is paired directly with its editor label", () => {
  assert.match(placeTemplate, /field\.name == 'is_checkpoint'.*\{\{ field \}\}<label[^>]+>\{\{ field\.label \}\}/s);
  assert.match(css, /\.editor-checkbox-field\s*\{[^}]*grid-template-columns:\s*auto minmax\(0, 1fr\)/s);
});

test("place field capture reuses the shared adaptive campus-scoped controller", () => {
  assert.match(placeScript, /bindLocationCapture/);
  assert.match(placeScript, /loadSupportedLocationArea/);
  assert.doesNotMatch(placeScript, /getCurrentPosition/);
  assert.doesNotMatch(placeScript, /watchPosition/);
});

test("path geometry always retains selected endpoints", () => {
  assert.match(segmentScript, /coordinates: a && b \? \[a, b\]/);
  assert.match(segmentScript, /splice\(-1, 0/);
});
