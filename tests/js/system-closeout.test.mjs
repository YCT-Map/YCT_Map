import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

import { createDestinationPanel } from "../../static/yct_map/js/destination-panel.js";
import { createUserNavigation } from "../../static/yct_map/js/user-navigation.js";

class FakeElement {
  constructor(ownerDocument) {
    this.ownerDocument = ownerDocument;
    this.hidden = true;
    this.disabled = false;
    this.selected = false;
    this.checked = false;
    this.value = "";
    this._textContent = "";
    this.dataset = {};
    this.children = [];
    this.listeners = new Map();
    this.attributes = new Map();
    this.classList = {
      add() {},
      remove() {},
      toggle() {},
    };
  }

  get textContent() { return this._textContent; }
  set textContent(value) { this._textContent = value; }

  get options() { return this.children; }

  querySelector(selector) {
    return this.queries.get(selector) || null;
  }

  querySelectorAll() {
    return [];
  }

  addEventListener(type, listener) {
    this.listeners.set(type, listener);
  }

  append(child) {
    this.children.push(child);
    if (child.selected) this.value = child.value;
  }

  replaceChildren() {
    this.children = [];
    this.value = "";
  }

  setAttribute(name, value) {
    this.attributes.set(name, value);
  }

  focus() {
    this.ownerDocument.activeElement = this;
  }
}

function createHarness(selectors) {
  const ownerDocument = {
    activeElement: null,
    createElement: () => new FakeElement(ownerDocument),
    querySelector: () => null,
  };
  const panel = new FakeElement(ownerDocument);
  panel.queries = new Map(selectors.map((selector) => [selector, new FakeElement(ownerDocument)]));
  return { ownerDocument, panel, get: (selector) => panel.querySelector(selector) };
}

function chooseMappedOrigin(harness, value) {
  const label = harness.get("#user-route-mapped-origins").children
    .find((candidate) => candidate.children[0]?.value === value);
  const input = label.children[0];
  input.checked = true;
  input.listeners.get("change")();
}

test("destination panel hides verification notice and badge for FIELD_VERIFIED places", () => {
  const harness = createHarness([
    "#destination-name",
    "#destination-category",
    "#destination-description",
    "#close-panel",
    "#destination-directions",
    "#destination-routing-reason",
    "#destination-inside",
    "#destination-inside-list",
    "#destination-internal-guidance",
    "#destination-internal-parent",
    "#destination-internal-location",
    "#destination-internal-direction",
    "#destination-verification",
    "#destination-data-notice",
    "#destination-data-notice-text",
  ]);

  const panel = createDestinationPanel(harness.panel, {
    onDirections: () => {},
  });

  // FIELD_VERIFIED place
  panel.show({
    id: "loc-1",
    properties: {
      name: "Engineering Complex",
      category_label: "Academic",
      verification_state: "FIELD_VERIFIED",
    },
  });

  assert.equal(harness.get("#destination-verification").hidden, true);
  assert.equal(harness.get("#destination-data-notice").hidden, true);

  // UNVERIFIED place
  panel.show({
    id: "loc-2",
    properties: {
      name: "Temporary Hall",
      category_label: "Academic",
      verification_state: "UNVERIFIED",
    },
  });

  assert.equal(harness.get("#destination-verification").hidden, false);
  assert.equal(harness.get("#destination-verification").textContent, "UNVERIFIED");
  assert.equal(harness.get("#destination-data-notice").hidden, false);

  // DEMO place
  panel.show({
    id: "loc-3",
    properties: {
      name: "Demo Shed",
      category_label: "Academic",
      verification_state: "DEMO",
    },
  });

  assert.equal(harness.get("#destination-verification").hidden, false);
  assert.equal(harness.get("#destination-verification").textContent, "DEMO");
  assert.equal(harness.get("#destination-data-notice").hidden, false);
});

function navigationSelectors() {
  return [
    "#user-route-form",
    "#user-route-origin-live",
    "#user-route-live-status",
    "#user-route-mapped-origins",
    "#user-route-request-status",
    "#user-route-destination",
    "#show-user-route",
    "#user-route-error",
    "#user-route-result",
    "#user-route-form-state",
    "#user-route-from",
    "#user-route-to",
    "#user-route-distance",
    "#user-route-eta",
    "#user-route-data-notice",
    "#user-route-progress-status",
    "#user-route-eta-source",
    "#change-route-origin",
    "#change-route-destination",
    "#clear-user-route",
    "#close-user-route",
    "#cancel-user-route",
    "#retry-reroute",
    "#toggle-route-details",
    "#user-route-summary-destination",
    "#user-route-badge",
    "#user-route-arrival-prefix",
    "#user-route-summary-handoff",
    "#user-route-internal-handoff",
  ];
}

const mockDestination = {
  id: "dest-1",
  properties: {
    id: "dest-1",
    name: "Engineering Complex",
    routing_available: true,
  },
};

const mockOrigin = {
  id: "orig-1",
  properties: {
    id: "orig-1",
    name: "Main Gate",
    routing_available: true,
  },
};

for (const state of ["FIELD_VERIFIED", "DEMO", "UNVERIFIED"]) {
  test(`user navigation adapts route badge and notice for ${state} routes`, async () => {
    const harness = createHarness(navigationSelectors());
    const controller = createUserNavigation({
      panel: harness.panel,
      features: [mockDestination, mockOrigin],
      routeUrl: "/api/routes/",
      onRoute() {},
      onClear() {},
      requestRoute: async () => ({
        ok: true,
        json: async () => ({
          route: {
            type: "Feature",
            geometry: { type: "LineString", coordinates: [[3.374, 6.518], [3.375, 6.519]] },
          },
          summary: {
            origin: { name: "Main Gate" },
            destination: { name: "Engineering Complex" },
            total_distance_metres: 150,
            eta_label: "~2 min",
            verification_state: state,
          },
        }),
      }),
    });

    controller.begin(mockDestination);
    chooseMappedOrigin(harness, "orig-1");
    await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });

    const badge = harness.get("#user-route-badge");
    const notice = harness.get("#user-route-data-notice");

    if (state === "FIELD_VERIFIED") {
      assert.equal(badge.hidden, true);
      assert.equal(notice.hidden, true);
    } else {
      assert.equal(badge.hidden, false);
      assert.equal(badge.textContent, state === "DEMO" ? "DEMO ROUTE" : "UNVERIFIED ROUTE");
      assert.equal(notice.hidden, false);
    }
  });
}

test("map attribution specifies YCT Map campus data and OSM-derived route data", () => {
  const mapJsPath = path.resolve("static/yct_map/js/map.js");
  const content = fs.readFileSync(mapJsPath, "utf-8");
  assert.match(content, /customAttribution:\s*("YCT Map campus data · OSM-derived route data"|\["YCT Map campus data · OSM-derived route data"\])/);
});
