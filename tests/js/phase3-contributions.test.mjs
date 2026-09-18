import assert from "node:assert/strict";
import test from "node:test";

import { createContributions } from "../../static/yct_map/js/contributions.js";

class Element {
  constructor(document) { this.ownerDocument = document; this.hidden = false; this.disabled = false; this.value = ""; this.textContent = ""; this.children = []; this.listeners = new Map(); }
  addEventListener(type, handler) { this.listeners.set(type, handler); }
  append(child) { this.children.push(child); }
  replaceChildren() { this.children = []; }
  focus() { this.ownerDocument.activeElement = this; }
  reportValidity() { return true; }
  reset() { for (const item of this.ownerDocument.elements.values()) item.value = ""; }
  querySelector(selector) { return this.ownerDocument.elements.get(selector); }
}

function harness(request, options = {}) {
  const document = { cookie: "csrftoken=token", activeElement: null, elements: new Map(), createElement: null };
  document.createElement = () => new Element(document);
  const selectors = ["#contribution-form", "#contribution-form-state", "#contribution-success", "#contribution-type",
    "#contribution-target", "#contribution-target-group", "#contribution-name", "#contribution-name-group",
    "#contribution-category-group", "#contribution-category", "#submit-contribution", "#contribution-error",
    "#contribution-point-status", "#clear-contribution-point", "#pick-contribution-point", "#contribution-context",
    "#contribution-description", "#contribution-website", "#contribution-reference", "#close-contribution",
    "#cancel-contribution", "#finish-contribution", "#new-contribution", "h2"];
  for (const selector of selectors) document.elements.set(selector, new Element(document));
  const panel = new Element(document);
  panel.hidden = true;
  const openButton = new Element(document);
  globalThis.document = document;
  const controller = createContributions({ panel, openButton, endpoint: "/api/contributions/", features: [{ properties: {
    id: "place-1", name: "DEMO — Library",
  } }], request, ...options });
  return { controller, panel, openButton, get: (selector) => document.elements.get(selector) };
}

test("contribution flow opens and adapts required fields", () => {
  const h = harness(async () => {});
  h.openButton.listeners.get("click")();
  assert.equal(h.panel.hidden, false);
  h.get("#contribution-type").value = "ADD_LOCATION";
  h.get("#contribution-type").listeners.get("change")();
  assert.equal(h.get("#contribution-name-group").hidden, false);
  assert.equal(h.get("#contribution-target-group").hidden, true);
});

test("new-place submission sends a narrow CSRF-protected payload and renders success", async () => {
  let sent;
  const h = harness(async (url, options) => { sent = { url, options }; return { ok: true, json: async () => ({ id: "abcdef12-0000", status: "PENDING" }) }; });
  h.get("#contribution-type").value = "ADD_LOCATION";
  h.get("#contribution-type").listeners.get("change")();
  h.get("#contribution-name").value = "Proposed place";
  h.get("#contribution-description").value = "Please review this place.";
  await h.get("#contribution-form").listeners.get("submit")({ preventDefault() {} });
  const body = JSON.parse(sent.options.body);
  assert.equal(sent.url, "/api/contributions/");
  assert.equal(sent.options.headers["X-CSRFToken"], "token");
  assert.equal(body.proposed_name, "Proposed place");
  assert.equal(h.get("#contribution-success").hidden, false);
  assert.equal(h.get("#contribution-reference").textContent, "ABCDEF12");
});

test("recoverable failure retains form data and reuses the request id", async () => {
  const bodies = [];
  let attempt = 0;
  const h = harness(async (_url, options) => { bodies.push(JSON.parse(options.body)); attempt += 1; return attempt === 1
    ? { ok: false, json: async () => ({ error: "Temporarily unavailable." }) }
    : { ok: true, json: async () => ({ id: "12345678-0000" }) }; });
  h.get("#contribution-type").value = "OTHER";
  h.get("#contribution-description").value = "Keep this text";
  await h.get("#contribution-form").listeners.get("submit")({ preventDefault() {} });
  assert.equal(h.get("#contribution-error").hidden, false);
  assert.equal(h.get("#contribution-description").value, "Keep this text");
  await h.get("#contribution-form").listeners.get("submit")({ preventDefault() {} });
  assert.equal(bodies[0].request_id, bodies[1].request_id);
});

test("map point selection is explicit and removable", () => {
  let cleared = 0;
  const h = harness(async () => {});
  const controller = createContributions({ panel: h.panel, openButton: h.openButton, endpoint: "/api/contributions/",
    features: [], onPickPoint: (callback) => callback([3.374, 6.518]), onClearPoint: () => { cleared += 1; }, request: async () => {} });
  controller.setMapAvailable(true);
  h.get("#pick-contribution-point").listeners.get("click")();
  assert.match(h.get("#contribution-point-status").textContent, /selected/);
  h.get("#clear-contribution-point").listeners.get("click")();
  assert.ok(cleared > 0);
});

test("high-precision map point is rounded in the outgoing payload", async () => {
  let body;
  const h = harness(async (_url, options) => {
    body = JSON.parse(options.body);
    return { ok: true, json: async () => ({ id: "87654321-0000" }) };
  }, { onPickPoint: (callback) => callback([3.374987654321, 6.518123456789]) });
  h.controller.setMapAvailable(true);
  h.get("#pick-contribution-point").listeners.get("click")();
  h.get("#contribution-type").value = "OTHER";
  h.get("#contribution-description").value = "Review this selected point.";
  await h.get("#contribution-form").listeners.get("submit")({ preventDefault() {} });
  assert.deepEqual(body.proposed_point, { latitude: 6.518123, longitude: 3.374988 });
  assert.equal(h.get("#contribution-success").hidden, false);
});

test("coordinate failure gives meaningful feedback and retains the point and form", async () => {
  const h = harness(async () => ({ ok: false, json: async () => ({
    code: "INVALID_COORDINATE",
    error: "The selected map point could not be submitted. Please choose the point again.",
  }) }), { onPickPoint: (callback) => callback([3.374987654321, 6.518123456789]) });
  h.controller.setMapAvailable(true);
  h.get("#pick-contribution-point").listeners.get("click")();
  h.get("#contribution-type").value = "OTHER";
  h.get("#contribution-description").value = "Keep this correction text.";
  await h.get("#contribution-form").listeners.get("submit")({ preventDefault() {} });
  assert.match(h.get("#contribution-error").textContent, /selected map point/);
  assert.equal(h.get("#contribution-description").value, "Keep this correction text.");
  assert.match(h.get("#contribution-point-status").textContent, /selected/);
});
