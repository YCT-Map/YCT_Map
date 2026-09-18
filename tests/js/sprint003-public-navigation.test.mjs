import assert from "node:assert/strict";
import test from "node:test";

import { createDestinationPanel } from "../../static/yct_map/js/destination-panel.js";
import { createUserNavigation } from "../../static/yct_map/js/user-navigation.js";

class FakeElement {
  constructor(ownerDocument) {
    this.ownerDocument = ownerDocument;
    this.hidden = true;
    this.disabled = false;
    this.selected = false;
    this.value = "";
    this.textContent = "";
    this.children = [];
    this.listeners = new Map();
    this.attributes = new Map();
    this.classList = { add() {}, remove() {} };
  }

  get options() {
    return this.children;
  }

  querySelector(selector) {
    return this.queries.get(selector);
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

const destination = {
  id: "destination-id",
  properties: {
    id: "destination-id",
    name: "DEMO — Library",
    category_label: "Libraries",
    description: "Synthetic library.",
    routing_available: true,
  },
};

const origin = {
  id: "origin-id",
  properties: {
    id: "origin-id",
    name: "DEMO — Administration",
    routing_available: true,
  },
};

test("anchored destination exposes Directions and emits the selected feature", () => {
  const harness = createHarness([
    "#destination-name",
    "#destination-category",
    "#destination-description",
    "#close-panel",
    "#destination-directions",
  ]);
  let emitted = null;
  const controller = createDestinationPanel(harness.panel, { onDirections: (feature) => { emitted = feature; } });

  controller.show(destination);

  assert.equal(harness.panel.hidden, false);
  assert.equal(harness.get("#destination-directions").hidden, false);
  harness.get("#destination-directions").listeners.get("click")();
  assert.equal(emitted, destination);
});

test("public navigation opens, excludes destination, renders result, and clears", async () => {
  const harness = createHarness([
    "#user-route-form",
    "#user-route-origin",
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
    "#change-route-origin",
    "#change-route-destination",
    "#clear-user-route",
    "#close-user-route",
    "#cancel-user-route",
  ]);
  const states = [];
  const routeCalls = [];
  const requestedUrls = [];
  let clearCount = 0;
  const controller = createUserNavigation({
    panel: harness.panel,
    features: [destination, origin],
    routeUrl: "/api/routes/",
    onRoute: (...args) => routeCalls.push(args),
    onClear: () => { clearCount += 1; },
    onStateChange: (state) => states.push(state),
    requestRoute: async (url) => {
      requestedUrls.push(url);
      return {
        ok: true,
        json: async () => ({
          route: { type: "Feature", geometry: { type: "LineString", coordinates: [[3.37, 6.51], [3.38, 6.52]] } },
          summary: {
            origin: { name: origin.properties.name },
            destination: { name: destination.properties.name },
            distance_metres: 73,
            eta_label: "~1 min",
            verification_state: "UNVERIFIED",
          },
        }),
      };
    },
  });

  assert.equal(controller.begin(destination), true);
  assert.equal(harness.panel.hidden, false);
  assert.equal(states.at(-1), "choosing-origin");
  assert.deepEqual(harness.get("#user-route-origin").options.map((option) => option.value), ["", "origin-id"]);
  assert.equal(harness.get("#show-user-route").disabled, true);

  harness.get("#user-route-origin").value = "origin-id";
  harness.get("#user-route-origin").listeners.get("change")();
  assert.equal(harness.get("#show-user-route").disabled, false);
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });

  assert.match(requestedUrls[0], /^\/api\/routes\/\?origin=origin-id&destination=destination-id$/);
  assert.equal(routeCalls.length, 1, "the public user-route renderer callback must be invoked once");
  assert.equal(harness.get("#user-route-result").hidden, false);
  assert.equal(harness.get("#user-route-from").textContent, origin.properties.name);
  assert.equal(harness.get("#user-route-to").textContent, destination.properties.name);
  assert.equal(harness.get("#user-route-distance").textContent, "73 m");
  assert.equal(harness.get("#user-route-eta").textContent, "~1 min");
  assert.equal(states.at(-1), "route-available");

  harness.get("#clear-user-route").listeners.get("click")();
  assert.equal(harness.panel.hidden, true);
  assert.equal(clearCount, 1);
  assert.equal(states.at(-1), "browsing");
});

test("Cancel restores the selected destination through the application callback", () => {
  const harness = createHarness([
    "#user-route-form", "#user-route-origin", "#user-route-destination", "#show-user-route",
    "#user-route-error", "#user-route-result", "#user-route-form-state", "#user-route-from",
    "#user-route-to", "#user-route-distance", "#user-route-eta", "#change-route-origin",
    "#user-route-data-notice",
    "#change-route-destination", "#clear-user-route", "#close-user-route", "#cancel-user-route",
  ]);
  let cancelled = null;
  const controller = createUserNavigation({
    panel: harness.panel,
    features: [destination, origin],
    routeUrl: "/api/routes/",
    onRoute() {},
    onClear() {},
    onCancel: (feature) => { cancelled = feature; },
  });

  controller.begin(destination);
  harness.get("#cancel-user-route").listeners.get("click")();

  assert.equal(harness.panel.hidden, true);
  assert.equal(cancelled, destination);
});
