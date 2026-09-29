import assert from "node:assert/strict";
import test from "node:test";

import { createUserNavigation } from "../../static/yct_map/js/user-navigation.js";
import { createDestinationPanel } from "../../static/yct_map/js/destination-panel.js";

class FakeElement {
  constructor(ownerDocument) {
    this.ownerDocument = ownerDocument;
    this.hidden = true;
    this.disabled = false;
    this.selected = false;
    this.value = "";
    this.textContent = "";
    this.dataset = {};
    this.children = [];
    this.listeners = new Map();
    this.attributes = new Map();
    this.classList = { add() {}, remove() {} };
  }
  get options() { return this.children; }
  querySelector(selector) { return this.queries.get(selector); }
  addEventListener(type, listener) { this.listeners.set(type, listener); }
  append(child) { this.children.push(child); if (child.selected) this.value = child.value; }
  replaceChildren() { this.children = []; this.value = ""; }
  setAttribute(name, value) { this.attributes.set(name, value); }
  focus() { this.ownerDocument.activeElement = this; }
}

const selectors = [
  "#user-route-form", "#user-route-origin-live", "#user-route-live-status", "#user-route-mapped-origins",
  "#user-route-request-status", "#user-route-destination", "#show-user-route",
  "#user-route-error", "#user-route-result", "#user-route-form-state", "#user-route-from",
  "#user-route-to", "#user-route-distance", "#user-route-eta", "#user-route-data-notice",
  "#user-route-progress-status", "#user-route-eta-source", "#change-route-origin",
  "#change-route-destination", "#clear-user-route", "#close-user-route", "#cancel-user-route",
  "#retry-reroute", "#toggle-route-details", "#user-route-summary-destination",
  "#user-route-summary-handoff", "#user-route-arrival-prefix", "#user-route-internal-handoff",
  "#user-route-internal-name", "#user-route-internal-location", "#user-route-internal-direction",
];

function harness() {
  const ownerDocument = { activeElement: null, createElement: () => new FakeElement(ownerDocument) };
  const panel = new FakeElement(ownerDocument);
  panel.queries = new Map(selectors.map((selector) => [selector, new FakeElement(ownerDocument)]));
  return { panel, get: (selector) => panel.querySelector(selector) };
}

function chooseMappedOrigin(state, value) {
  const label = state.get("#user-route-mapped-origins").children
    .find((candidate) => candidate.children[0]?.value === value);
  const input = label.children[0];
  input.checked = true;
  input.listeners.get("change")();
}

function chooseLiveOrigin(state) {
  const input = state.get("#user-route-origin-live");
  input.checked = true;
  input.listeners.get("change")();
}

const origin = { properties: { id: "origin", name: "Administration", routing_available: true } };
const internal = { properties: {
  id: "lr3", destination_key: "internal:lr3", destination_type: "internal",
  name: "Lecture Room 3", routing_available: true,
} };
const destinationSummary = {
  name: "Lecture Room 3", type: "internal", routing_scope: "OUTDOOR_TO_ENTRANCE",
  outdoor_arrival: { label: "New Building — Main Entrance", exact_connector: true },
  indoor_handoff: {
    name: "Lecture Room 3", floor: "First Floor", room_code: "LR3", wing_section: "East Wing",
    direction_note: "Take the first staircase and turn right.",
  },
};

function payload() {
  return {
    route: { type: "Feature", geometry: { type: "LineString", coordinates: [[3.374, 6.518], [3.3746, 6.518]] } },
    summary: {
      origin: { name: "Administration" }, destination: destinationSummary,
      distance_metres: 67, total_distance_metres: 67, eta_label: "~1 min",
    },
  };
}

test("internal destination details keep direction note distinct before Directions starts", () => {
  const state = harness();
  for (const selector of ["#destination-name", "#destination-category", "#destination-description",
    "#close-panel", "#destination-directions", "#destination-routing-reason", "#destination-inside",
    "#destination-inside-list", "#destination-internal-guidance", "#destination-internal-parent",
    "#destination-internal-location", "#destination-internal-direction"]) {
    state.panel.queries.set(selector, new FakeElement(state.panel.ownerDocument));
  }
  const controller = createDestinationPanel(state.panel);
  controller.show({ properties: {
    ...internal.properties, internal_type_label: "Classroom", description: "Internal destination inside New Building.",
    parent: { name: "New Building" }, floor: { label: "First Floor" }, room_code: "LR3",
    wing_section: "East Wing", direction_note: "Take the first staircase and turn right.",
  } });
  assert.equal(state.get("#destination-description").textContent, "Internal destination inside New Building.");
  assert.equal(state.get("#destination-internal-location").textContent, "First Floor · LR3 · East Wing");
  assert.equal(state.get("#destination-internal-direction").textContent, "Take the first staircase and turn right.");
});

test("manual route retains compact and expanded internal-place handoff without claiming indoor routing", async () => {
  const state = harness();
  const routeCalls = [];
  const controller = createUserNavigation({
    panel: state.panel, features: [origin], routeUrl: "/api/routes/", onClear() {},
    onRoute: (...args) => routeCalls.push(args),
    requestRoute: async () => ({ ok: true, json: async () => payload() }),
  });
  controller.begin(internal);
  chooseMappedOrigin(state, "origin");
  await state.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });
  assert.equal(state.get("#user-route-summary-destination").textContent, "Lecture Room 3");
  assert.equal(state.get("#user-route-to").textContent, "New Building — Main Entrance");
  assert.equal(state.get("#user-route-arrival-prefix").textContent, "Outdoor arrival:");
  assert.equal(state.get("#user-route-summary-handoff").textContent, "Inside: First Floor · LR3 · East Wing");
  assert.equal(state.get("#user-route-internal-direction").textContent, "Take the first staircase and turn right.");
  assert.equal(routeCalls[0][3].arrivalName, "New Building — Main Entrance");
});

test("stable accuracy-qualified live arrival announces the entrance and exposes the indoor handoff", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const state = harness();
  const controller = createUserNavigation({
    panel: state.panel, features: [origin], routeUrl: "/api/routes/", liveRouteUrl: "/api/routes/from-position/",
    onRoute() {}, onClear() {}, now: () => 1_000,
    requestRoute: async () => ({ ok: true, json: async () => payload() }),
  });
  controller.updateLivePosition({ longitude: 3.374, latitude: 6.518, accuracyMetres: 8, timestamp: 1_000 });
  controller.begin(internal);
  chooseLiveOrigin(state);
  await state.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });
  controller.updateLivePosition({ longitude: 3.3746, latitude: 6.518, accuracyMetres: 8, timestamp: 5_000 });
  controller.updateLivePosition({ longitude: 3.3746, latitude: 6.518, accuracyMetres: 8, timestamp: 9_000 });
  assert.equal(state.panel.dataset.routeState, "arrived");
  assert.match(state.get("#user-route-progress-status").textContent, /reached New Building — Main Entrance/);
  assert.equal(state.get("#user-route-internal-name").textContent, "Lecture Room 3");
  assert.doesNotMatch(state.get("#user-route-progress-status").textContent, /reached Lecture Room 3/);
});
