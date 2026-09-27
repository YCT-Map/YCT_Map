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
    this.dataset = {};
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
  assert.deepEqual(harness.get("#user-route-origin").options.map((option) => option.value), ["", "__live__", "origin-id"]);
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
  assert.equal(harness.panel.dataset.routeState, "active");
  assert.equal(harness.panel.dataset.detailsExpanded, "false");
  assert.equal(harness.get("#user-route-summary-destination").textContent, destination.properties.name);
  harness.get("#toggle-route-details").listeners.get("click")();
  assert.equal(harness.panel.dataset.detailsExpanded, "true");
  harness.get("#toggle-route-details").listeners.get("click")();
  assert.equal(harness.panel.dataset.detailsExpanded, "false");

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
    "#user-route-data-notice", "#user-route-progress-status", "#user-route-eta-source",
    "#change-route-destination", "#clear-user-route", "#close-user-route", "#cancel-user-route", "#retry-reroute",
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

test("accepted live position is offered and sent through the protected live route contract", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const selectors = ["#user-route-form", "#user-route-origin", "#user-route-destination", "#show-user-route",
    "#user-route-error", "#user-route-result", "#user-route-form-state", "#user-route-from", "#user-route-to",
    "#user-route-distance", "#user-route-eta", "#user-route-data-notice", "#user-route-progress-status",
    "#user-route-eta-source", "#change-route-origin", "#change-route-destination", "#clear-user-route",
    "#close-user-route", "#cancel-user-route", "#retry-reroute"];
  const harness = createHarness(selectors);
  let request = null;
  const controller = createUserNavigation({
    panel: harness.panel, features: [destination, origin], routeUrl: "/api/routes/",
    liveRouteUrl: "/api/routes/from-position/", onRoute() {}, onClear() {},
    now: () => 1_000,
    requestRoute: async (url, options) => { request = { url, options }; return { ok: true, json: async () => ({
      route: { type: "Feature", geometry: { type: "LineString", coordinates: [[3.374, 6.518], [3.375, 6.519]] } },
      summary: { origin: { name: "Your location" }, destination: { name: destination.properties.name },
        total_distance_metres: 100, eta_label: "~2 min", verification_state: "UNVERIFIED" },
    }) }; },
  });
  controller.updateLivePosition({ longitude: 3.374, latitude: 6.518, accuracyMetres: 10, timestamp: 1_000 });
  controller.begin(destination);
  harness.get("#user-route-origin").value = "__live__";
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });
  assert.equal(request.url, "/api/routes/from-position/");
  assert.equal(request.options.method, "POST");
  assert.equal(request.options.headers["X-CSRFToken"], "test-token");
  assert.deepEqual(JSON.parse(request.options.body).position, { latitude: 6.518, longitude: 3.374, accuracy_metres: 10 });
});

function navigationSelectors() {
  return ["#user-route-form", "#user-route-origin", "#user-route-destination", "#show-user-route",
    "#user-route-error", "#user-route-result", "#user-route-form-state", "#user-route-from", "#user-route-to",
    "#user-route-distance", "#user-route-eta", "#user-route-data-notice", "#user-route-progress-status",
    "#user-route-eta-source", "#change-route-origin", "#change-route-destination", "#clear-user-route",
    "#close-user-route", "#cancel-user-route", "#retry-reroute", "#toggle-route-details",
    "#user-route-summary-destination"];
}

function routePayload(coordinates = [[3.374, 6.518], [3.375, 6.518]], distance = 110) {
  return { route: { type: "Feature", geometry: { type: "LineString", coordinates } }, summary: {
    origin: { name: "Your location" }, destination: { name: destination.properties.name },
    total_distance_metres: distance, eta_label: "~2 min", verification_state: "UNVERIFIED",
  } };
}

test("confirmed deviation performs one controlled route replacement", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness = createHarness(navigationSelectors());
  const routeCalls = [];
  let requests = 0;
  const controller = createUserNavigation({
    panel: harness.panel, features: [destination, origin], routeUrl: "/api/routes/",
    liveRouteUrl: "/api/routes/from-position/", onRoute: (...args) => routeCalls.push(args), onClear() {},
    now: () => 1_000,
    requestRoute: async () => ({ ok: true, json: async () => routePayload(
      requests++ === 0 ? [[3.374, 6.518], [3.375, 6.518]] : [[3.3743, 6.5182], [3.375, 6.518]],
      requests === 1 ? 110 : 90,
    ) }),
  });
  controller.updateLivePosition({ longitude: 3.374, latitude: 6.518, accuracyMetres: 5, timestamp: 1_000 });
  controller.begin(destination);
  harness.get("#user-route-origin").value = "__live__";
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });
  for (const [longitude, timestamp] of [[3.3741, 5_000], [3.3742, 9_000], [3.3743, 13_000]]) {
    controller.updateLivePosition({ longitude, latitude: 6.5182, accuracyMetres: 5, timestamp });
  }
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(requests, 2);
  assert.equal(routeCalls.length, 2);
  assert.equal(routeCalls[1][3].replacement, true);
  assert.match(harness.get("#user-route-progress-status").textContent, /Route updated/);
});

test("failed reroute retains guidance and exposes a retry action", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness = createHarness(navigationSelectors());
  const staleStates = [];
  let requests = 0;
  const controller = createUserNavigation({
    panel: harness.panel, features: [destination, origin], routeUrl: "/api/routes/",
    liveRouteUrl: "/api/routes/from-position/", onRoute() {}, onClear() {},
    now: () => 1_000,
    onRouteStale: (value) => staleStates.push(value), requestRoute: async () => {
      requests += 1;
      if (requests === 1) return { ok: true, json: async () => routePayload() };
      return { ok: false, json: async () => ({ error: "No safe network match.", code: "NO_SAFE_NETWORK_MATCH" }) };
    },
  });
  const position = { longitude: 3.374, latitude: 6.518, accuracyMetres: 5, timestamp: 1_000 };
  controller.updateLivePosition(position);
  controller.begin(destination);
  harness.get("#user-route-origin").value = "__live__";
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });
  assert.equal(await controller.performReroute({ ...position, timestamp: 5_000 }), false);
  assert.equal(staleStates.at(-1), true);
  assert.equal(harness.get("#retry-reroute").hidden, false);
  assert.match(harness.get("#user-route-progress-status").textContent, /Unable to safely reroute/);
});

test("a stale live position cannot be reused as a new route origin", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness=createHarness(navigationSelectors()); let requests=0;
  const controller=createUserNavigation({panel:harness.panel,features:[destination,origin],routeUrl:"/api/routes/",
    liveRouteUrl:"/api/routes/from-position/",onRoute(){},onClear(){},now:()=>40_001,
    requestRoute:async()=>{requests+=1;return {ok:true,json:async()=>routePayload()};}});
  controller.updateLivePosition({longitude:3.374,latitude:6.518,accuracyMetres:5,timestamp:1_000});
  controller.begin(destination);
  harness.get("#user-route-origin").value="__live__";
  await harness.get("#user-route-form").listeners.get("submit")({preventDefault(){}});
  assert.equal(requests,0);
  assert.match(harness.get("#user-route-error").textContent,/no longer current/);
});

test("foreground suspension hides and restores a route without resetting it", () => {
  const harness = createHarness(navigationSelectors());
  let clears = 0;
  const controller = createUserNavigation({
    panel: harness.panel, features: [destination, origin], routeUrl: "/api/routes/",
    onRoute() {}, onClear: () => { clears += 1; },
  });
  controller.begin(destination);
  assert.equal(controller.suspend(), true);
  assert.equal(harness.panel.hidden, true);
  assert.equal(clears, 0);
  assert.equal(controller.resume(), true);
  assert.equal(harness.panel.hidden, false);
  assert.equal(harness.get("#user-route-destination").textContent, destination.properties.name);
  assert.equal(clears, 0);
});
