import assert from "node:assert/strict";
import test from "node:test";

import { createDestinationPanel } from "../../static/yct_map/js/destination-panel.js";
import { createUserNavigation as createUserNavigationImplementation, findNearbyMappedStart,
  isLivePositionRouteUsable, isMeaningfulLiveRouteRetry,
  MAX_LIVE_POSITION_AGE_MS, NEARBY_MAPPED_START_MAX_METRES } from "../../static/yct_map/js/user-navigation.js";

function createUserNavigation(options) {
  const controller = createUserNavigationImplementation(options);
  const updateLivePosition = controller.updateLivePosition;
  controller.updateLivePosition = (position) => updateLivePosition({ navigationReady: true, ...position });
  return controller;
}

class FakeElement {
  constructor(ownerDocument) {
    this.ownerDocument = ownerDocument;
    this.hidden = true;
    this.disabled = false;
    this.selected = false;
    this.value = "";
    this._textContent = "";
    this.textWrites = 0;
    this.dataset = {};
    this.children = [];
    this.listeners = new Map();
    this.attributes = new Map();
    this.classList = { add() {}, remove() {} };
  }

  get textContent() { return this._textContent; }
  set textContent(value) { this._textContent = value; this.textWrites += 1; }

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

function chooseMappedOrigin(harness, value) {
  const label = harness.get("#user-route-mapped-origins").children
    .find((candidate) => candidate.children[0]?.value === value);
  const input = label.children[0];
  input.checked = true;
  input.listeners.get("change")();
}

function chooseLiveOrigin(harness) {
  const input = harness.get("#user-route-origin-live");
  input.checked = true;
  input.listeners.get("change")();
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

test("unanchored destination keeps a visible disabled Directions action with the exact reason", () => {
  const harness = createHarness([
    "#destination-name", "#destination-category", "#destination-description", "#close-panel",
    "#destination-directions", "#destination-routing-reason",
  ]);
  const unavailable = { ...destination, properties: { ...destination.properties,
    routing_available: false,
    routing_unavailable_reason: "The primary entrance is not connected to the walking network.",
  } };
  const controller = createDestinationPanel(harness.panel);

  controller.show(unavailable);

  assert.equal(harness.get("#destination-directions").hidden, false);
  assert.equal(harness.get("#destination-directions").disabled, true);
  assert.equal(harness.get("#destination-directions").textContent, "Directions unavailable");
  assert.equal(harness.get("#destination-routing-reason").hidden, false);
  assert.match(harness.get("#destination-routing-reason").textContent, /primary entrance/i);
});

test("public navigation opens, excludes destination, renders result, and clears", async () => {
  const harness = createHarness(navigationSelectors());
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
  assert.equal(harness.get("#user-route-origin-live").value, "__live__");
  assert.deepEqual(harness.get("#user-route-mapped-origins").children
    .map((label) => label.children[0].value), ["origin-id"]);
  assert.equal(harness.get("#show-user-route").disabled, true);

  chooseMappedOrigin(harness, "origin-id");
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
    "#user-route-form", "#user-route-origin-live", "#user-route-live-status", "#user-route-mapped-origins",
    "#user-route-request-status", "#user-route-destination", "#show-user-route",
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
  const selectors = ["#user-route-form", "#user-route-origin-live", "#user-route-live-status",
    "#user-route-mapped-origins", "#user-route-request-status", "#user-route-destination", "#show-user-route",
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
  chooseLiveOrigin(harness);
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });
  assert.equal(request.url, "/api/routes/from-position/");
  assert.equal(request.options.method, "POST");
  assert.equal(request.options.headers["X-CSRFToken"], "test-token");
  assert.deepEqual(JSON.parse(request.options.body).position, { latitude: 6.518, longitude: 3.374, accuracy_metres: 10 });
});

test("approach-required live route renders an explicit orientation guide and waits to join", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness = createHarness(navigationSelectors());
  const routeCalls = [];
  let approachClears = 0;
  const projection = [3.3744, 6.5182];
  const payload = {
    navigation_state: "APPROACH_REQUIRED",
    route: { type: "Feature", geometry: { type: "LineString",
      coordinates: [projection, [3.375, 6.518]] } },
    summary: {
      origin: { name: "Your location" }, destination: { name: destination.properties.name },
      total_distance_metres: 90, eta_label: "~1 min", verification_state: "FIELD_VERIFIED",
      live_start: { state: "APPROACH_REQUIRED", network_match_distance_metres: 42,
        network_match_coordinate: projection, on_path_corridor_metres: 16 },
    },
  };
  const controller = createUserNavigation({
    panel: harness.panel, features: [destination, origin], routeUrl: "/api/routes/",
    liveRouteUrl: "/api/routes/from-position/", onRoute: (...args) => routeCalls.push(args),
    onClear() {}, onApproachClear: () => { approachClears += 1; }, now: () => 1_000,
    requestRoute: async () => ({ ok: true, json: async () => payload }),
  });
  controller.updateLivePosition({ longitude: 3.374, latitude: 6.518, accuracyMetres: 8, timestamp: 1_000 });
  controller.begin(destination); chooseLiveOrigin(harness);
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });

  assert.equal(routeCalls.length, 1);
  assert.equal(routeCalls[0][3].originType, "live-approach");
  assert.deepEqual(routeCalls[0][3].approachCoordinate, projection);
  assert.match(harness.get("#user-route-progress-status").textContent, /Mapped route begins/);
  assert.match(harness.get("#user-route-eta-source").textContent, /orientation only/);
  assert.match(harness.get("#user-route-data-notice").textContent, /not claimed as a mapped walkway/);

  controller.updateLivePosition({ longitude: projection[0], latitude: projection[1],
    accuracyMetres: 5, timestamp: 5_000 });
  assert.equal(approachClears, 1);
  assert.match(harness.get("#user-route-progress-status").textContent, /Mapped route joined|Following route/);
});

test("malformed approach response fails visibly instead of pretending the route is active", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness = createHarness(navigationSelectors());
  const controller = createUserNavigation({
    panel: harness.panel, features: [destination, origin], routeUrl: "/api/routes/",
    liveRouteUrl: "/api/routes/from-position/", onRoute() {}, onClear() {}, now: () => 1_000,
    requestRoute: async () => ({ ok: true, json: async () => ({
      navigation_state: "APPROACH_REQUIRED",
      route: { type: "Feature", geometry: { type: "LineString",
        coordinates: [[3.374, 6.518], [3.375, 6.519]] } },
      summary: { origin: { name: "Your location" }, destination: { name: destination.properties.name },
        total_distance_metres: 100, eta_label: "~2 min", verification_state: "FIELD_VERIFIED",
        live_start: { state: "APPROACH_REQUIRED", network_match_distance_metres: 42 } },
    }) }),
  });
  controller.updateLivePosition({ longitude: 3.374, latitude: 6.518,
    accuracyMetres: 5, timestamp: 1_000 });
  controller.begin(destination); chooseLiveOrigin(harness);
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });

  assert.equal(harness.get("#user-route-error").hidden, false);
  assert.match(harness.get("#user-route-error").textContent, /incomplete approach route/);
  assert.equal(harness.get("#user-route-form-state").hidden, false);
  assert.equal(harness.get("#user-route-result").hidden, true);
  assert.equal(harness.get("#show-user-route").disabled, false);
});

test("map rendering failure restores route setup with an actionable error", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness = createHarness(navigationSelectors());
  let clears = 0;
  const controller = createUserNavigation({
    panel: harness.panel, features: [destination, origin], routeUrl: "/api/routes/",
    liveRouteUrl: "/api/routes/from-position/", now: () => 1_000,
    onRoute() { throw new Error("Map renderer unavailable."); },
    onClear() { clears += 1; },
    requestRoute: async () => ({ ok: true, json: async () => routePayload() }),
  });
  controller.updateLivePosition({ longitude: 3.374, latitude: 6.518,
    accuracyMetres: 5, timestamp: 1_000 });
  controller.begin(destination); chooseLiveOrigin(harness);
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });

  assert.equal(harness.get("#user-route-error").hidden, false);
  assert.match(harness.get("#user-route-error").textContent, /Map renderer unavailable/);
  assert.equal(harness.get("#user-route-form-state").hidden, false);
  assert.equal(harness.get("#user-route-result").hidden, true);
  assert.equal(harness.get("#show-user-route").disabled, false);
  assert.ok(clears >= 1);
});

test("arrival needs two stable live responses separated by three seconds", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness = createHarness(navigationSelectors());
  let routeCalls = 0;
  let clears = 0;
  let requests = 0;
  const controller = createUserNavigation({
    panel: harness.panel, features: [destination, origin], routeUrl: "/api/routes/",
    liveRouteUrl: "/api/routes/from-position/", onRoute: () => { routeCalls += 1; },
    onClear: () => { clears += 1; }, now: () => 1_000,
    requestRoute: async () => { requests += 1; return ({ ok: true, json: async () => ({
      navigation_state: "ARRIVAL_CANDIDATE",
      summary: { origin: { name: "Your location", type: "live" },
        destination: { name: destination.properties.name,
          outdoor_arrival: { label: "Library main entrance" } },
        total_distance_metres: 0, remaining_distance_metres: 0,
        eta_label: "Checking arrival", verification_state: "FIELD_VERIFIED" },
    }) }); },
  });
  controller.updateLivePosition({ longitude: 3.374, latitude: 6.518, accuracyMetres: 5, timestamp: 1_000 });
  controller.begin(destination); chooseLiveOrigin(harness);
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });

  assert.equal(requests, 1);
  assert.equal(harness.panel.dataset.routeState, "recovering");
  assert.equal(harness.get("#user-route-result").hidden, true);
  assert.match(harness.get("#user-route-request-status").textContent, /Confirming arrival/);
  controller.updateLivePosition({ longitude: 3.374, latitude: 6.518,
    accuracyMetres: 5, timestamp: 4_000 });
  await new Promise((resolve) => setTimeout(resolve, 0));

  assert.equal(requests, 2);
  assert.equal(routeCalls, 0, "arrival does not fabricate an unrenderable route geometry");
  assert.equal(clears, 1);
  assert.equal(harness.panel.dataset.routeState, "arrived");
  assert.equal(harness.get("#user-route-result").hidden, false);
  assert.equal(harness.get("#user-route-distance").textContent, "0 m");
  assert.equal(harness.get("#user-route-eta").textContent, "Arrived");
  assert.match(harness.get("#user-route-progress-status").textContent, /Library main entrance/);
  assert.match(harness.get("#user-route-eta-source").textContent, /repeated/);
});

test("route usability separates recent retained position from genuinely stale position", () => {
  const retained = { longitude: 3.374, latitude: 6.518, accuracyMetres: 12,
    timestamp: 1_000, freshness: "retained", navigationReady: true };
  assert.equal(isLivePositionRouteUsable(retained, { now: 26_000 }), true);
  assert.equal(isLivePositionRouteUsable(retained, {
    now: 1_000 + MAX_LIVE_POSITION_AGE_MS + 1,
  }), false);
  assert.equal(isLivePositionRouteUsable({ ...retained, freshness: "stale" }, { now: 2_000 }), false);
  assert.equal(isLivePositionRouteUsable({ ...retained, accuracyMetres: 41 }, { now: 2_000 }), false);
  assert.equal(isLivePositionRouteUsable({ ...retained, supportedAreaValid: false }, { now: 2_000 }), false);
  assert.equal(isLivePositionRouteUsable({ ...retained, navigationReady: false }, { now: 2_000 }), false,
    "an accurate-looking but unconfirmed fix must not become a route origin");
});

test("live-route retries require meaningful movement or a material accuracy improvement", () => {
  const previous = { longitude: 3.374, latitude: 6.518, accuracyMetres: 12, timestamp: 1_000 };
  assert.equal(isMeaningfulLiveRouteRetry({
    longitude: 3.374001, latitude: 6.518001, accuracyMetres: 12, timestamp: 1_500,
  }, previous), false, "rapid stationary jitter must not spend an attempt");
  assert.equal(isMeaningfulLiveRouteRetry({
    longitude: 3.37408, latitude: 6.518, accuracyMetres: 12, timestamp: 2_000,
  }, previous), true, "real movement should trigger a new destination-aware match");
  assert.equal(isMeaningfulLiveRouteRetry({
    longitude: 3.374001, latitude: 6.518001, accuracyMetres: 7, timestamp: 2_000,
  }, previous), true, "a materially better fix should trigger a retry even without movement");
  assert.equal(isMeaningfulLiveRouteRetry({ ...previous, timestamp: 1_000 }, previous), false);
});

test("live directions remain disabled until the location controller confirms readiness", async () => {
  const harness = createHarness(navigationSelectors());
  let requests = 0;
  const controller = createUserNavigationImplementation({
    panel: harness.panel, features: [destination, origin], routeUrl: "/api/routes/",
    liveRouteUrl: "/api/routes/from-position/", onRoute() {}, onClear() {}, now: () => 1_000,
    requestRoute: async () => { requests += 1; return { ok: true, json: async () => routePayload() }; },
  });
  controller.updateLivePosition({ longitude: 3.374, latitude: 6.518, accuracyMetres: 5,
    timestamp: 1_000, navigationReady: false });
  controller.begin(destination);
  assert.equal(harness.get("#user-route-origin-live").disabled, true);
  assert.match(harness.get("#user-route-live-status").textContent, /confirmed|improving/i);
  assert.equal(requests, 0);
});

test("nearby mapped start is bounded, routable, and never substitutes the destination itself", () => {
  const target = { type: "Feature", geometry: { type: "Point", coordinates: [3.3758, 6.5176] },
    properties: { id: "food", destination_key: "location:food", name: "Food Tech New Building",
      routing_available: true } };
  const sports = { type: "Feature", geometry: { type: "Point", coordinates: [3.374192, 6.518525] },
    properties: { id: "sports", destination_key: "location:sports", name: "Sports Complex",
      routing_available: true } };
  const far = { type: "Feature", geometry: { type: "Point", coordinates: [3.38, 6.52] },
    properties: { id: "far", destination_key: "location:far", name: "Far place", routing_available: true } };
  const live = { longitude: 3.3742, latitude: 6.51852 };
  const match = findNearbyMappedStart([target, sports, far], target, live);
  assert.equal(match.feature, sports);
  assert.ok(match.distanceMetres < 5);
  assert.equal(findNearbyMappedStart([target], target, live), null);
  assert.equal(findNearbyMappedStart([target, far], target, live,
    { maxDistanceMetres: NEARBY_MAPPED_START_MAX_METRES }), null);
});

test("unsafe live match falls back to a nearby place entrance and waits there before tracking", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness = createHarness(navigationSelectors());
  const target = { type: "Feature", geometry: { type: "Point", coordinates: [3.375797, 6.517573] },
    properties: { id: "food", destination_key: "location:food", name: "Food Tech New Building",
      routing_available: true } };
  const sports = { type: "Feature", geometry: { type: "Point", coordinates: [3.374192, 6.518525] },
    properties: { id: "sports", destination_key: "location:sports", name: "Sports Complex",
      routing_available: true } };
  const routeCalls = [];
  const requested = [];
  let deadline;
  const gate = [3.373512, 6.518877];
  const responsePayload = {
    route: { type: "Feature", geometry: { type: "LineString", coordinates: [gate, [3.374, 6.518], [3.375772, 6.517637]] } },
    summary: { origin: { name: "Sports Complex", outdoor_arrival: { label: "Sports Complex — Gate 1" } },
      destination: { name: "Food Tech New Building", outdoor_arrival: { label: "Food Tech New Building — Main Entrance" } },
      total_distance_metres: 492, eta_label: "~7 min", verification_state: "UNVERIFIED" },
  };
  const controller = createUserNavigation({ panel: harness.panel, features: [target, sports],
    routeUrl: "/api/routes/", liveRouteUrl: "/api/routes/from-position/",
    onRoute: (...args) => routeCalls.push(args), onClear() {}, now: () => 2_000,
    setDeadline: (callback) => { deadline = callback; return 1; }, clearDeadline() {}, requestRoute: async (url) => {
      requested.push(url);
      return requested.length === 1
        ? { ok: false, json: async () => ({ code: "NO_SAFE_NETWORK_MATCH", error: "Unsafe match." }) }
        : { ok: true, json: async () => responsePayload };
    } });
  controller.updateLivePosition({ longitude: 3.374192, latitude: 6.518525,
    accuracyMetres: 3, timestamp: 1_000, freshness: "fresh" });
  controller.begin(target); chooseLiveOrigin(harness);
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });
  assert.equal(requested.length, 1, "fallback waits for the bounded live-match window");
  deadline();
  await new Promise((resolve) => setTimeout(resolve, 0));
  await new Promise((resolve) => setTimeout(resolve, 0));

  assert.equal(requested.length, 2);
  assert.equal(requested[0], "/api/routes/from-position/");
  assert.equal(requested[1], "/api/routes/?origin=location%3Asports&destination=location%3Afood");
  assert.equal(routeCalls.length, 1);
  assert.equal(routeCalls[0][1], sports);
  assert.equal(routeCalls[0][3].originType, "live-mapped-start");
  assert.equal(harness.get("#user-route-from").textContent, "Sports Complex — Gate 1");
  assert.match(harness.get("#user-route-progress-status").textContent, /Walk to Sports Complex — Gate 1/);
  assert.match(harness.get("#user-route-data-notice").textContent, /no route from your dot/);
  assert.match(harness.get("#user-route-eta-source").textContent, /begin at Sports Complex — Gate 1/);

  controller.updateLivePosition({ longitude: 3.374192, latitude: 6.518525,
    accuracyMetres: 3, timestamp: 3_000, freshness: "fresh" });
  assert.match(harness.get("#user-route-progress-status").textContent, /join the mapped route/);
  controller.updateLivePosition({ longitude: gate[0], latitude: gate[1],
    accuracyMetres: 3, timestamp: 7_000, freshness: "fresh" });
  assert.doesNotMatch(harness.get("#user-route-progress-status").textContent, /join the mapped route/);
});

test("mapped-start fallback tries the next nearby connected destination", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness = createHarness(navigationSelectors());
  const target = { type: "Feature", geometry: { type: "Point", coordinates: [3.3758, 6.5176] },
    properties: { id: "target", destination_key: "location:target", name: "Target", routing_available: true } };
  const closest = { type: "Feature", geometry: { type: "Point", coordinates: [3.37401, 6.518] },
    properties: { id: "closest", destination_key: "location:closest", name: "Closest", routing_available: true } };
  const connected = { type: "Feature", geometry: { type: "Point", coordinates: [3.3742, 6.518] },
    properties: { id: "connected", destination_key: "location:connected", name: "Connected", routing_available: true } };
  let deadline;
  const requested = [];
  const controller = createUserNavigation({ panel: harness.panel,
    features: [target, closest, connected], routeUrl: "/api/routes/",
    liveRouteUrl: "/api/routes/from-position/", onRoute() {}, onClear() {}, now: () => 2_000,
    setDeadline: (callback) => { deadline = callback; return 1; }, clearDeadline() {},
    requestRoute: async (url) => {
      requested.push(url);
      if (requested.length === 1) return { ok: false,
        json: async () => ({ code: "NO_SAFE_NETWORK_MATCH", error: "Unsafe match." }) };
      if (requested.length === 2) return { ok: false,
        json: async () => ({ code: "NO_ROUTE", error: "Closest is disconnected." }) };
      return { ok: true, json: async () => ({
        route: { type: "Feature", geometry: { type: "LineString",
          coordinates: [[3.3742, 6.518], [3.3758, 6.5176]] } },
        summary: { origin: { name: "Connected" }, destination: { name: "Target" },
          total_distance_metres: 180, eta_label: "~3 min", verification_state: "FIELD_VERIFIED" },
      }) };
    } });
  controller.updateLivePosition({ longitude: 3.374, latitude: 6.518,
    accuracyMetres: 5, timestamp: 1_000 });
  controller.begin(target); chooseLiveOrigin(harness);
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });
  deadline();
  await new Promise((resolve) => setTimeout(resolve, 0));
  await new Promise((resolve) => setTimeout(resolve, 0));

  assert.equal(requested.length, 3);
  assert.match(requested[1], /origin=location%3Aclosest/);
  assert.match(requested[2], /origin=location%3Aconnected/);
  assert.equal(harness.get("#user-route-result").hidden, false);
  assert.equal(harness.get("#user-route-from").textContent, "Connected");
});

test("passive location expiry cannot abort an active route-origin snapshot", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness = createHarness(navigationSelectors());
  let resolveResponse;
  let requestOptions;
  const routeCalls = [];
  const responsePromise = new Promise((resolve) => { resolveResponse = resolve; });
  const controller = createUserNavigation({
    panel: harness.panel, features: [destination, origin], routeUrl: "/api/routes/",
    liveRouteUrl: "/api/routes/from-position/", onRoute: (...args) => routeCalls.push(args), onClear() {},
    now: () => 2_000, setDeadline: () => 1, clearDeadline() {},
    requestRoute: async (_url, options) => { requestOptions = options; return responsePromise; },
  });
  const position = { longitude: 3.374, latitude: 6.518, accuracyMetres: 8,
    timestamp: 1_000, freshness: "fresh" };
  controller.updateLivePosition(position);
  controller.begin(destination);
  chooseLiveOrigin(harness);
  const submission = harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });
  await Promise.resolve();

  controller.clearLivePosition({ reason: "stale", reacquiring: true });
  assert.equal(requestOptions.signal.aborted, false);
  assert.equal(harness.get("#user-route-origin-live").checked, true);
  assert.equal(harness.get("#user-route-live-status").textContent, "Refreshing current location");
  assert.deepEqual(JSON.parse(requestOptions.body).position,
    { latitude: 6.518, longitude: 3.374, accuracy_metres: 8 });

  resolveResponse({ ok: true, json: async () => routePayload() });
  await submission;
  assert.equal(routeCalls.length, 1);
  assert.equal(harness.get("#user-route-result").hidden, false);
});

test("only trustworthy tracker progress is emitted for progressive route presentation", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness = createHarness(navigationSelectors());
  const progressUpdates = [];
  const controller = createUserNavigation({
    panel: harness.panel, features: [destination, origin], routeUrl: "/api/routes/",
    liveRouteUrl: "/api/routes/from-position/", onRoute() {}, onClear() {},
    onRouteProgress: (progress) => progressUpdates.push(progress), now: () => 1_000,
    requestRoute: async () => ({ ok: true, json: async () => routePayload(
      [[3.374, 6.518], [3.375, 6.518]], 110,
    ) }),
  });
  controller.updateLivePosition({ longitude: 3.374, latitude: 6.518, accuracyMetres: 5, timestamp: 1_000 });
  controller.begin(destination);
  chooseLiveOrigin(harness);
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });

  controller.updateLivePosition({ longitude: 3.3742, latitude: 6.518, accuracyMetres: 5, timestamp: 5_000 });
  assert.equal(progressUpdates.length, 1);
  assert.equal(progressUpdates[0].state, "walking");
  const trustworthyProgress = progressUpdates[0].progressMetres;

  controller.updateLivePosition({ longitude: 3.3743, latitude: 6.518, accuracyMetres: 80, timestamp: 9_000 });
  assert.equal(progressUpdates.length, 1, "uncertain GPS must freeze route presentation");
  controller.updateLivePosition({ longitude: 3.3740, latitude: 6.518, accuracyMetres: 5, timestamp: 13_000 });
  assert.equal(progressUpdates.length, 1, "one backward anomaly must not move the rendered route");
  controller.updateLivePosition({ longitude: 3.37401, latitude: 6.518, accuracyMetres: 5, timestamp: 17_000 });
  assert.equal(progressUpdates.length, 2, "confirmed backtracking follows tracker-authoritative progress");
  assert.ok(progressUpdates[1].progressMetres < trustworthyProgress);
});

function navigationSelectors() {
  return ["#user-route-form", "#user-route-origin-live", "#user-route-live-status", "#user-route-mapped-origins",
    "#user-route-request-status", "#user-route-destination", "#show-user-route",
    "#user-route-error", "#user-route-result", "#user-route-form-state", "#user-route-from", "#user-route-to",
    "#user-route-distance", "#user-route-eta", "#user-route-data-notice", "#user-route-progress-status",
    "#user-route-eta-source", "#change-route-origin", "#change-route-destination", "#clear-user-route",
    "#close-user-route", "#cancel-user-route", "#retry-reroute", "#toggle-route-details",
    "#user-route-summary-destination", "#user-route-guidance"];
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
  chooseLiveOrigin(harness);
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
  const position = { longitude: 3.374, latitude: 6.518, accuracyMetres: 5,
    timestamp: 1_000, navigationReady: true };
  controller.updateLivePosition(position);
  controller.begin(destination);
  chooseLiveOrigin(harness);
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });
  assert.equal(await controller.performReroute({ ...position, timestamp: 5_000 }), false);
  assert.equal(staleStates.at(-1), true);
  assert.equal(harness.get("#retry-reroute").hidden, false);
  assert.match(harness.get("#user-route-progress-status").textContent, /Unable to safely reroute/);
});

test("a stale live route origin waits for reacquisition and then routes from the fresh fix", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness=createHarness(navigationSelectors()); let requests=0; let clock=1_000; let refreshes=0;
  const controller=createUserNavigation({panel:harness.panel,features:[destination,origin],routeUrl:"/api/routes/",
    liveRouteUrl:"/api/routes/from-position/",onRoute(){},onClear(){},now:()=>clock,
    onFreshLocationRequired(){refreshes+=1;return true;},setDeadline:()=>1,clearDeadline(){},
    requestRoute:async()=>{requests+=1;return {ok:true,json:async()=>routePayload()};}});
  controller.updateLivePosition({longitude:3.374,latitude:6.518,accuracyMetres:5,timestamp:1_000});
  controller.begin(destination);
  chooseLiveOrigin(harness);
  clock=32_001;
  await harness.get("#user-route-form").listeners.get("submit")({preventDefault(){}});
  assert.equal(requests,0);
  assert.equal(refreshes,1);
  assert.match(harness.get("#user-route-request-status").textContent,/Refreshing your location/);
  controller.updateLivePosition({longitude:3.3742,latitude:6.5181,accuracyMetres:8,
    timestamp:32_001,freshness:"fresh"});
  await new Promise((resolve)=>setTimeout(resolve,0));
  assert.equal(requests,1);
  assert.equal(harness.get("#user-route-result").hidden,false);
});

test("a recent retained coordinate remains route-usable on a stationary phone", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness=createHarness(navigationSelectors()); let requests=0; let refreshes=0;
  const controller=createUserNavigation({panel:harness.panel,features:[destination,origin],routeUrl:"/api/routes/",
    liveRouteUrl:"/api/routes/from-position/",onRoute(){},onClear(){},now:()=>26_000,
    onFreshLocationRequired(){refreshes+=1;return true;},setDeadline:()=>1,clearDeadline(){},
    requestRoute:async()=>{requests+=1;return {ok:true,json:async()=>routePayload()};}});
  controller.updateLivePosition({longitude:3.374,latitude:6.518,accuracyMetres:5,
    timestamp:1_000,freshness:"retained"});
  controller.begin(destination);
  chooseLiveOrigin(harness);
  await harness.get("#user-route-form").listeners.get("submit")({preventDefault(){}});
  assert.equal(requests,1);
  assert.equal(refreshes,0);
  assert.match(harness.get("#user-route-live-status").textContent,/Recent stable position/);
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

test("origin cards keep live first, filter mapped starts, and avoid GPS-driven rebuilding", () => {
  const harness = createHarness(navigationSelectors());
  const unroutable = { id: "no-anchor", properties: { id: "no-anchor", name: "No anchor", routing_available: false } };
  let clock = 1_000;
  const controller = createUserNavigation({ panel: harness.panel,
    features: [destination, origin, unroutable], routeUrl: "/api/routes/", onRoute() {}, onClear() {}, now: () => clock });

  controller.begin(destination);
  assert.equal(harness.get("#user-route-origin-live").value, "__live__");
  assert.deepEqual(harness.get("#user-route-mapped-origins").children.map((label) => label.children[0].value), ["origin-id"]);
  assert.equal(harness.get("#user-route-live-status").textContent, "Locate first");
  const mappedCards = harness.get("#user-route-mapped-origins").children;

  controller.updateLivePosition({ longitude: 3.374, latitude: 6.518, accuracyMetres: 5, timestamp: 1_000 });
  const statusWrites = harness.get("#user-route-live-status").textWrites;
  clock = 1_100;
  controller.updateLivePosition({ longitude: 3.37401, latitude: 6.51801, accuracyMetres: 5, timestamp: 1_100 });
  assert.equal(harness.get("#user-route-mapped-origins").children, mappedCards);
  assert.equal(harness.get("#user-route-live-status").textWrites, statusWrites);
  assert.equal(harness.get("#user-route-origin-live").disabled, false);
  assert.match(harness.get("#user-route-live-status").textContent, /Live location ready/);

  clock = 40_001;
  controller.updateLivePosition({ longitude: 3.37401, latitude: 6.51801, accuracyMetres: 5, timestamp: 1_100 });
  assert.equal(harness.get("#user-route-origin-live").disabled, true);
  assert.equal(harness.get("#user-route-live-status").textContent, "Current location needs refreshing");
});

test("transient live-start failure waits for a newer accepted position and then succeeds", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness = createHarness(navigationSelectors());
  const timestamps = [];
  let inFlight = 0;
  let maxInFlight = 0;
  let calls = 0;
  const controller = createUserNavigation({ panel: harness.panel, features: [destination, origin],
    routeUrl: "/api/routes/", liveRouteUrl: "/api/routes/from-position/", onRoute() {}, onClear() {},
    now: () => 2_000, setDeadline: () => 1, clearDeadline() {},
    requestRoute: async (_url, options) => {
      inFlight += 1; maxInFlight = Math.max(maxInFlight, inFlight); calls += 1;
      timestamps.push(JSON.parse(options.body).position.latitude);
      await Promise.resolve(); inFlight -= 1;
      return calls === 1
        ? { ok: false, json: async () => ({ code: "NO_SAFE_NETWORK_MATCH", error: "Unsafe match." }) }
        : { ok: true, json: async () => routePayload() };
    } });
  controller.updateLivePosition({ longitude: 3.374, latitude: 6.518, accuracyMetres: 6, timestamp: 1_000 });
  controller.begin(destination); chooseLiveOrigin(harness);
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });
  controller.updateLivePosition({ longitude: 3.3741, latitude: 6.5181, accuracyMetres: 5, timestamp: 1_000 });
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(calls, 1, "the same timestamp must not trigger a retry");
  controller.updateLivePosition({ longitude: 3.3742, latitude: 6.5182, accuracyMetres: 5, timestamp: 1_500 });
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(calls, 2);
  assert.equal(maxInFlight, 1);
  assert.deepEqual(timestamps, [6.518, 6.5182]);
  assert.equal(harness.get("#user-route-result").hidden, false);
});

test("stationary high-frequency fixes do not exhaust live-route attempts and end honestly", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness = createHarness(navigationSelectors());
  let calls = 0;
  let deadline;
  const controller = createUserNavigation({ panel: harness.panel, features: [destination, origin],
    routeUrl: "/api/routes/", liveRouteUrl: "/api/routes/from-position/", onRoute() {}, onClear() {},
    now: () => 2_000, setDeadline: (callback) => { deadline = callback; return 1; }, clearDeadline() {},
    requestRoute: async () => { calls += 1; return { ok: false,
      json: async () => ({ code: "INSUFFICIENT_ACCURACY", error: "Try again." }) }; } });
  controller.updateLivePosition({ longitude: 3.374, latitude: 6.518, accuracyMetres: 10, timestamp: 1_000 });
  controller.begin(destination); chooseLiveOrigin(harness);
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });
  for (const timestamp of [1_200, 1_400, 1_600]) {
    controller.updateLivePosition({ longitude: 3.374, latitude: 6.518, accuracyMetres: 10, timestamp });
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
  assert.equal(calls, 1, "timestamp-only stationary jitter must not trigger route requests");
  assert.equal(harness.get("#show-user-route").disabled, true);
  assert.equal(harness.get("#show-user-route").textContent, "Matching location…");
  deadline();
  await new Promise((resolve) => setTimeout(resolve, 0));
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(calls, 1, "without a valid nearby mapped start, timeout must not invent another request");
  assert.match(harness.get("#user-route-error").textContent, /cannot yet be safely connected/);
  assert.equal(harness.get("#show-user-route").disabled, false);
  assert.equal(harness.get("#show-user-route").textContent, "Show route");
});

test("non-retryable live errors stop immediately and changing origin clears the error", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness = createHarness(navigationSelectors());
  let calls = 0;
  const controller = createUserNavigation({ panel: harness.panel, features: [destination, origin],
    routeUrl: "/api/routes/", liveRouteUrl: "/api/routes/from-position/", onRoute() {}, onClear() {},
    now: () => 1_000, setDeadline: () => 1, clearDeadline() {}, requestRoute: async () => {
      calls += 1; return { ok: false, json: async () => ({ code: "NO_ROUTE", error: "No route." }) };
    } });
  controller.updateLivePosition({ longitude: 3.374, latitude: 6.518, accuracyMetres: 8, timestamp: 1_000 });
  controller.begin(destination); chooseLiveOrigin(harness);
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });
  controller.updateLivePosition({ longitude: 3.375, latitude: 6.519, accuracyMetres: 5, timestamp: 1_100 });
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(calls, 1);
  assert.equal(harness.get("#user-route-error").hidden, false);
  chooseMappedOrigin(harness, "origin-id");
  assert.equal(harness.get("#user-route-error").hidden, true);
  assert.equal(harness.get("#show-user-route").disabled, false);
});

test("cancel aborts pending live recovery and prevents later GPS retries", async () => {
  globalThis.document = { cookie: "csrftoken=test-token" };
  const harness = createHarness(navigationSelectors());
  let calls = 0;
  const controller = createUserNavigation({ panel: harness.panel, features: [destination, origin],
    routeUrl: "/api/routes/", liveRouteUrl: "/api/routes/from-position/", onRoute() {}, onClear() {},
    now: () => 1_000, setDeadline: () => 1, clearDeadline() {}, requestRoute: async () => {
      calls += 1; return { ok: false,
        json: async () => ({ code: "NO_SAFE_NETWORK_MATCH", error: "Unsafe match." }) };
    } });
  controller.updateLivePosition({ longitude: 3.374, latitude: 6.518, accuracyMetres: 8, timestamp: 1_000 });
  controller.begin(destination); chooseLiveOrigin(harness);
  await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });
  harness.get("#cancel-user-route").listeners.get("click")();
  controller.updateLivePosition({ longitude: 3.375, latitude: 6.519, accuracyMetres: 5, timestamp: 1_100 });
  await new Promise((resolve) => setTimeout(resolve, 0));
  assert.equal(calls, 1);
  assert.equal(harness.panel.hidden, true);
});

for (const action of ["mapped origin", "close", "change destination"]) {
  test(`${action} cancels pending live recovery`, async () => {
    globalThis.document = { cookie: "csrftoken=test-token" };
    const harness = createHarness(navigationSelectors());
    let calls = 0;
    const controller = createUserNavigation({ panel: harness.panel, features: [destination, origin],
      routeUrl: "/api/routes/", liveRouteUrl: "/api/routes/from-position/", onRoute() {}, onClear() {},
      now: () => 1_000, setDeadline: () => 1, clearDeadline() {}, requestRoute: async () => {
        calls += 1; return { ok: false,
          json: async () => ({ code: "NO_SAFE_NETWORK_MATCH", error: "Unsafe match." }) };
      } });
    controller.updateLivePosition({ longitude: 3.374, latitude: 6.518, accuracyMetres: 8, timestamp: 1_000 });
    controller.begin(destination); chooseLiveOrigin(harness);
    await harness.get("#user-route-form").listeners.get("submit")({ preventDefault() {} });
    if (action === "mapped origin") chooseMappedOrigin(harness, "origin-id");
    else harness.get(action === "close" ? "#close-user-route" : "#change-route-destination").listeners.get("click")();
    controller.updateLivePosition({ longitude: 3.375, latitude: 6.519, accuracyMetres: 5, timestamp: 1_100 });
    await new Promise((resolve) => setTimeout(resolve, 0));
    assert.equal(calls, 1);
  });
}

test("route setup disables duplicate submission and restores the button after failure", async () => {
  const harness = createHarness(navigationSelectors());
  let calls = 0;
  let finishRequest;
  const pending = new Promise((resolve) => { finishRequest = resolve; });
  const controller = createUserNavigation({ panel: harness.panel, features: [destination, origin],
    routeUrl: "/api/routes/", onRoute() {}, onClear() {}, requestRoute: async () => {
      calls += 1; await pending; return { ok: false, json: async () => ({ code: "NO_ROUTE", error: "No route." }) };
    } });
  controller.begin(destination); chooseMappedOrigin(harness, "origin-id");
  const submit = harness.get("#user-route-form").listeners.get("submit");
  const first = submit({ preventDefault() {} });
  const duplicate = submit({ preventDefault() {} });
  assert.equal(calls, 1);
  assert.equal(harness.get("#show-user-route").disabled, true);
  assert.match(harness.get("#user-route-request-status").textContent, /Calculating route/);
  finishRequest();
  await Promise.all([first, duplicate]);
  assert.equal(harness.get("#show-user-route").disabled, false);
  assert.equal(harness.get("#show-user-route").textContent, "Show route");
  assert.equal(harness.get("#user-route-error").textContent, "No route.");
});
