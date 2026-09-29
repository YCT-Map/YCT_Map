import assert from "node:assert/strict";
import test from "node:test";

import {
  DESTINATION_CLUSTER_CONFIG,
  DESTINATION_CLUSTER_COUNT_LAYER_ID,
  DESTINATION_CLUSTER_LAYER_ID,
  DESTINATION_HIT_LAYER_ID,
  DESTINATION_LABEL_LAYER_ID,
  DESTINATION_POINT_LAYER_ID,
  CHECKPOINT_HALO_LAYER_ID,
  CHECKPOINT_LABEL_LAYER_ID,
  DESTINATION_SOURCE_ID,
  NAVIGATION_FOREGROUND_LAYER_ORDER,
  SELECTED_DESTINATION_HALO_LAYER_ID,
  SELECTED_DESTINATION_MARKER_LAYER_ID,
  SELECTED_DESTINATION_SOURCE_ID,
  bindDestinationInteractions,
  destinationLayerDefinitions,
  destinationSourceDefinition,
  expandDestinationCluster,
  focusDestination,
  raiseNavigationLayers,
  selectedDestinationLayerDefinitions,
  setSelectedDestination,
  setVisibleDestinationFeatures,
} from "../../static/yct_map/js/map.js";

function destination(id, coordinates = [3.3742, 6.5185], destinationType = "location", isCheckpoint = false) {
  return {
    type: "Feature",
    id,
    geometry: { type: "Point", coordinates },
    properties: { id, name: `Place ${id}`, category: "library", destination_type: destinationType,
      is_checkpoint: isCheckpoint },
  };
}

test("outdoor destination source uses campus-scale native clustering", () => {
  const feature = destination("one");
  const source = destinationSourceDefinition([feature]);

  assert.equal(source.type, "geojson");
  assert.equal(source.cluster, true);
  assert.ok(source.clusterRadius >= 45 && source.clusterRadius <= 55);
  assert.equal(source.clusterMaxZoom, 16);
  assert.deepEqual(source.data.features, [feature]);
  assert.deepEqual(DESTINATION_CLUSTER_CONFIG, { cluster: true, clusterRadius: 50, clusterMaxZoom: 16 });
});

test("semantic zoom separates clusters, checkpoint landmarks, and close ordinary labels", () => {
  const layers = new Map(destinationLayerDefinitions().map((layer) => [layer.id, layer]));
  const cluster = layers.get(DESTINATION_CLUSTER_LAYER_ID);
  const count = layers.get(DESTINATION_CLUSTER_COUNT_LAYER_ID);
  const point = layers.get(DESTINATION_POINT_LAYER_ID);
  const hit = layers.get(DESTINATION_HIT_LAYER_ID);
  const label = layers.get(DESTINATION_LABEL_LAYER_ID);
  const checkpointLabel = layers.get(CHECKPOINT_LABEL_LAYER_ID);
  const checkpointFilter = ["all", ["!", ["has", "point_count"]], ["==", ["get", "is_checkpoint"], true]];
  const ordinaryFilter = ["all", ["!", ["has", "point_count"]], ["!=", ["get", "is_checkpoint"], true]];

  assert.deepEqual(cluster.filter, ["has", "point_count"]);
  assert.deepEqual(count.filter, ["has", "point_count"]);
  assert.deepEqual(point.filter, checkpointFilter);
  assert.deepEqual(hit.filter, ["!", ["has", "point_count"]]);
  assert.deepEqual(label.filter, ordinaryFilter);
  assert.equal(label.minzoom, 17.2);
  assert.deepEqual(checkpointLabel.filter, checkpointFilter);
  assert.equal(checkpointLabel.minzoom, 15.8);
  assert.equal(label.layout["text-field"][1], "name");
  assert.deepEqual(label.layout["text-size"],
    ["interpolate", ["linear"], ["zoom"], 17.2, 10.5, 20, 12]);
});

test("ordinary destinations have no visible marker while checkpoints and the shared hit target remain", () => {
  const layers = new Map(destinationLayerDefinitions().map((layer) => [layer.id, layer]));
  const point = layers.get(DESTINATION_POINT_LAYER_ID);
  const halo = layers.get(CHECKPOINT_HALO_LAYER_ID);
  const hit = layers.get(DESTINATION_HIT_LAYER_ID);

  assert.notEqual(point.id, hit.id);
  assert.deepEqual(point.paint["circle-radius"],
    ["interpolate", ["linear"], ["zoom"], 15, 8, 20, 9]);
  assert.equal(point.paint["circle-color"], "#17663c");
  assert.equal(point.paint["circle-stroke-width"], 2.5);
  assert.deepEqual(halo.filter, point.filter);
  assert.equal(hit.paint["circle-radius"], 15);
  assert.equal(hit.paint["circle-color"], "rgba(0,0,0,0.01)");
  assert.deepEqual(hit.filter, ["!", ["has", "point_count"]]);
  assert.deepEqual(clusterRadii(layers.get(DESTINATION_CLUSTER_LAYER_ID)), [15, 18, 21]);
});

function clusterRadii(layer) {
  const expression = layer.paint["circle-radius"];
  return [expression[2], expression[4], expression[6]];
}

test("selected destination uses an independent source and replaces its single feature", () => {
  const updates = [];
  const map = { getSource(id) {
    assert.equal(id, SELECTED_DESTINATION_SOURCE_ID);
    return { setData(data) { updates.push(data); } };
  } };
  const first = destination("one");
  const second = destination("two", [3.375, 6.519]);

  assert.equal(setSelectedDestination(map, first), true);
  assert.equal(setSelectedDestination(map, second), true);
  assert.equal(updates.length, 2);
  assert.equal(updates[0].features[0].properties.id, "one");
  assert.equal(updates[1].features[0].properties.id, "two");
  assert.notEqual(updates[1].features[0], second);

  const selectedLayers = selectedDestinationLayerDefinitions();
  assert.ok(selectedLayers.every((layer) => layer.source === SELECTED_DESTINATION_SOURCE_ID));
  assert.notEqual(SELECTED_DESTINATION_SOURCE_ID, DESTINATION_SOURCE_ID);

  setSelectedDestination(map, destination("checkpoint", [3.376, 6.52], "location", true));
  assert.equal(updates.at(-1).features[0].properties.is_checkpoint, true);

  setSelectedDestination(map, destination("inside", [3.375, 6.519], "internal"));
  assert.deepEqual(updates.at(-1).features, []);
});

test("search or category selection still focuses an individual destination above clusters", () => {
  const sourceUpdates = [];
  const cameraUpdates = [];
  const map = {
    getSource(id) {
      assert.equal(id, SELECTED_DESTINATION_SOURCE_ID);
      return { setData(data) { sourceUpdates.push(data); } };
    },
    flyTo(options) { cameraUpdates.push(options); },
  };
  const selected = destination("library", [3.375, 6.519]);

  focusDestination(map, selected);

  assert.equal(sourceUpdates[0].features[0].properties.id, "library");
  assert.deepEqual(cameraUpdates, [{
    center: [3.375, 6.519], zoom: 18, duration: 900, essential: false,
  }]);
});

test("category and search filtering replace data on the clustered source", () => {
  const updates = [];
  const map = { getSource(id) {
    assert.equal(id, DESTINATION_SOURCE_ID);
    return { setData(data) { updates.push(data); } };
  } };
  const filtered = [destination("food")];

  assert.equal(setVisibleDestinationFeatures(map, filtered), true);
  assert.deepEqual(updates, [{ type: "FeatureCollection", features: filtered }]);
  assert.equal(destinationSourceDefinition(filtered).cluster, true);
});

test("cluster click requests expansion zoom without selecting a destination", async () => {
  const listeners = new Map();
  const expansionIds = [];
  const cameraUpdates = [];
  const selected = [];
  const map = {
    on(type, layerId, handler) { listeners.set(`${type}:${layerId}`, handler); },
    getCanvas() { return { style: {} }; },
    getSource(id) {
      assert.equal(id, DESTINATION_SOURCE_ID);
      return { async getClusterExpansionZoom(clusterId) { expansionIds.push(clusterId); return 17; } };
    },
    easeTo(options) { cameraUpdates.push(options); },
  };
  const feature = destination("one");
  bindDestinationInteractions({ map, featureIndex: new Map([["one", feature]]), onSelect: (item) => selected.push(item) });

  await listeners.get(`click:${DESTINATION_CLUSTER_LAYER_ID}`)({ features: [{
    type: "Feature", geometry: { type: "Point", coordinates: [3.374, 6.518] },
    properties: { cluster_id: 42, point_count: 8 },
  }] });

  assert.deepEqual(expansionIds, [42]);
  assert.deepEqual(cameraUpdates[0].center, [3.374, 6.518]);
  assert.equal(cameraUpdates[0].zoom, 17);
  assert.equal(selected.length, 0);

  assert.equal(listeners.has(`click:${DESTINATION_POINT_LAYER_ID}`), false);
  listeners.get(`click:${DESTINATION_HIT_LAYER_ID}`)({ features: [feature] });
  assert.deepEqual(selected, [feature]);
});

test("cluster expansion failure is contained and leaves the camera unchanged", async () => {
  const warnings = [];
  let moved = false;
  const map = {
    getSource() { return { async getClusterExpansionZoom() { throw new Error("unavailable"); } }; },
    easeTo() { moved = true; },
  };
  const expanded = await expandDestinationCluster(map, {
    geometry: { type: "Point", coordinates: [3.374, 6.518] }, properties: { cluster_id: 7 },
  }, { warn: (...items) => warnings.push(items) });

  assert.equal(expanded, false);
  assert.equal(moved, false);
  assert.equal(warnings.length, 1);
});

test("route endpoints and live location are raised above destination density layers", () => {
  const destinationLayerIds = [
    DESTINATION_CLUSTER_LAYER_ID,
    DESTINATION_CLUSTER_COUNT_LAYER_ID,
    DESTINATION_POINT_LAYER_ID,
    DESTINATION_LABEL_LAYER_ID,
    SELECTED_DESTINATION_MARKER_LAYER_ID,
    SELECTED_DESTINATION_HALO_LAYER_ID,
  ];
  const layers = [...destinationLayerIds, ...NAVIGATION_FOREGROUND_LAYER_ORDER.filter((id) => !destinationLayerIds.includes(id))];
  const map = {
    getLayer(id) { return layers.includes(id) ? { id } : null; },
    moveLayer(id) { layers.splice(layers.indexOf(id), 1); layers.push(id); },
  };

  raiseNavigationLayers(map);

  assert.deepEqual(layers.slice(-NAVIGATION_FOREGROUND_LAYER_ORDER.length), [...NAVIGATION_FOREGROUND_LAYER_ORDER]);
  assert.ok(layers.indexOf(DESTINATION_CLUSTER_LAYER_ID) < layers.indexOf(NAVIGATION_FOREGROUND_LAYER_ORDER[0]));
  assert.ok(layers.indexOf(SELECTED_DESTINATION_HALO_LAYER_ID) < layers.indexOf(SELECTED_DESTINATION_MARKER_LAYER_ID));
  assert.ok(layers.indexOf(SELECTED_DESTINATION_MARKER_LAYER_ID) < layers.indexOf("user-route-endpoint-circles"));
  assert.ok(layers.indexOf("user-route-endpoint-circles") < layers.indexOf("live-user-location-dot"));
});
