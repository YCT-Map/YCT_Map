import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import { accuracyQuality, createPlaceCaptureController } from "../../static/yct_map/js/editor-place-map.js";

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

test("field capture is one-shot, accuracy-aware, and unverified", () => {
  assert.match(placeScript, /getCurrentPosition/);
  assert.doesNotMatch(placeScript, /watchPosition/);
  assert.match(placeScript, /accuracy > 100/);
  assert.match(placeScript, /UNVERIFIED/);
});

test("path geometry always retains selected endpoints", () => {
  assert.match(segmentScript, /coordinates: a && b \? \[a, b\]/);
  assert.match(segmentScript, /splice\(-1, 0/);
});

function captureHarness(result) {
  const listeners = new Map();
  const button = {disabled: false, textContent: "Use current location", addEventListener(type, fn) { listeners.set(type, fn); }};
  const statusElement = {textContent: "Idle"}; const points = [];
  const navigatorObject = {geolocation: {getCurrentPosition(success, failure, options) { result(success, failure, options); }}};
  createPlaceCaptureController({button, statusElement, navigatorObject, onPoint(point) { points.push(point); }});
  return {button, statusElement, points, click: () => listeners.get("click")()};
}

test("current-location success reports accuracy and permits retry/manual adjustment", () => {
  const state = captureHarness((success) => success({coords: {latitude: 6.5182, longitude: 3.3742, accuracy: 15}}));
  state.click(); assert.deepEqual(state.points, [{lng: 3.3742, lat: 6.5182}]); assert.match(state.statusElement.textContent, /Good accuracy.*15 m.*UNVERIFIED/); assert.equal(state.button.textContent, "Retry current location");
  state.click(); assert.equal(state.points.length, 2);
});

for (const [code, message] of [[1, /permission was denied/], [2, /unavailable/], [3, /timed out/]]) {
  test(`current-location error ${code} is visible`, () => { const state = captureHarness((success, failure) => failure({code})); state.click(); assert.match(state.statusElement.textContent, message); assert.equal(state.button.disabled, false); });
}

test("accuracy bands reject over 100 metres", () => {
  assert.equal(accuracyQuality(20), "good"); assert.equal(accuracyQuality(50), "fair"); assert.equal(accuracyQuality(80), "low"); assert.equal(accuracyQuality(101), "rejected");
  const state = captureHarness((success) => success({coords: {latitude: 6.5, longitude: 3.3, accuracy: 120}})); state.click(); assert.equal(state.points.length, 0); assert.match(state.statusElement.textContent, /too poor/);
});
