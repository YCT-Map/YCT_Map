import assert from "node:assert/strict";
import test from "node:test";

import { createEntrancePointSelector } from "../../static/yct_map/js/entrance-point-selector.js";

class FakeMap {
  constructor(options) {
    this.options = options;
    this.listeners = new Map();
    this.resizeCount = 0;
  }
  on(event, listener) { this.listeners.set(event, listener); }
  resize() { this.resizeCount += 1; }
  emit(event, payload = {}) { this.listeners.get(event)?.(payload); }
}

class FakeMarker {
  static instances = [];
  constructor(options) { this.options = options; this.removed = false; FakeMarker.instances.push(this); }
  setLngLat(coordinates) { this.coordinates = coordinates; return this; }
  addTo(map) { this.map = map; return this; }
  remove() { this.removed = true; }
}

function harness(dataset = {latitude: "", longitude: ""}) {
  FakeMarker.instances = [];
  const element = {dataset: {...dataset}};
  const latitudeInput = {value: ""};
  const longitudeInput = {value: ""};
  const statusElement = {textContent: ""};
  const controller = createEntrancePointSelector({
    element, latitudeInput, longitudeInput, statusElement,
    maplibregl: {Map: FakeMap, Marker: FakeMarker}, styleUrl: "test-style",
  });
  return {element, latitudeInput, longitudeInput, statusElement, controller};
}

test("map click selects hidden coordinates and a later click repositions the marker", () => {
  const state = harness();
  assert.deepEqual(state.controller.map.options.center, [3.37424, 6.51857]);
  assert.equal(FakeMarker.instances.length, 0);

  state.controller.map.emit("click", {lngLat: {lng: 3.3746544, lat: 6.5183214}});
  assert.equal(state.longitudeInput.value, "3.374654");
  assert.equal(state.latitudeInput.value, "6.518321");
  assert.deepEqual(FakeMarker.instances[0].coordinates, [3.3746544, 6.5183214]);
  assert.equal(state.element.dataset.state, "selected");

  state.controller.map.emit("click", {lngLat: {lng: 3.375, lat: 6.519}});
  assert.equal(FakeMarker.instances[0].removed, true);
  assert.deepEqual(FakeMarker.instances[1].coordinates, [3.375, 6.519]);
  assert.equal(state.longitudeInput.value, "3.375000");
  assert.equal(state.latitudeInput.value, "6.519000");
});

test("saved entrance point initializes the map and visible marker", () => {
  const state = harness({latitude: "6.518321", longitude: "3.374654"});
  assert.deepEqual(state.controller.map.options.center, [3.374654, 6.518321]);
  assert.equal(state.longitudeInput.value, "3.374654");
  assert.equal(state.latitudeInput.value, "6.518321");
  assert.deepEqual(FakeMarker.instances[0].coordinates, [3.374654, 6.518321]);
  state.controller.map.emit("load");
  assert.equal(state.controller.map.resizeCount, 1);
});
