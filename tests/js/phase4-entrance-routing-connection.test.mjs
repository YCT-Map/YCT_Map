import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

import {
  candidateSummary,
  connectorDistanceMetres,
  proposedConnectionLine,
} from "../../static/yct_map/js/entrance-routing-connection.js";

const template = readFileSync(new URL("../../templates/editor/entrance_form.html", import.meta.url), "utf8");
const css = readFileSync(new URL("../../static/yct_map/css/editor.css", import.meta.url), "utf8");

test("proposed routing line joins the entrance to the explicitly selected candidate", () => {
  const line = proposedConnectionLine(
    {longitude: 3.374, latitude: 6.518},
    {longitude: 3.3742, latitude: 6.5181},
  );
  assert.deepEqual(line.geometry.coordinates, [[3.3742, 6.5181], [3.374, 6.518]]);
  assert.equal(line.geometry.type, "LineString");
  assert.ok(connectorDistanceMetres(line) > 0);
});

test("candidate summary communicates identity and measured distance", () => {
  assert.equal(
    candidateSummary({display_label: "OSM path junction · node/42", distance_label: "12.4 m"}),
    "OSM path junction · node/42 · 12.4 m",
  );
});

test("connection workflow separates proposal from confirmation and explicit disconnection", () => {
  assert.match(template, /id="find-routing-candidates"/);
  assert.match(template, /id="routing-connection-proposal"[^>]*hidden/);
  assert.match(template, /name="action" value="connect"/);
  assert.match(template, /name="connector_geometry"/);
  assert.match(template, /Confirm connection/);
  assert.match(template, /id="undo-connector-bend"/);
  assert.match(template, /id="reset-connector"/);
  assert.match(template, /name="confirm_disconnect" value="yes" required/);
});

test("mobile candidate and confirmation controls use one-column comfortable touch targets", () => {
  assert.match(css, /@media \(max-width: 640px\)[\s\S]*?\.routing-candidate-list\s*\{\s*grid-template-columns:\s*1fr/);
  assert.match(css, /\.routing-candidate\s*\{[^}]*min-height:\s*3\.75rem/s);
  assert.match(css, /\.entrance-confirm-form > \*\s*\{[^}]*min-height:\s*2\.9rem/s);
});
