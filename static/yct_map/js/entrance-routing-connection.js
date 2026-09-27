const SOURCE_ID = "entrance-routing-candidates";
const SEGMENT_LAYER_ID = "entrance-routing-segments";
const NODE_LAYER_ID = "entrance-routing-nodes";
const LINK_SOURCE_ID = "entrance-routing-link";
const LINK_LAYER_ID = "entrance-routing-link-line";
const CURRENT_SOURCE_ID = "entrance-current-anchor";
const CURRENT_LAYER_ID = "entrance-current-anchor-node";

export function proposedConnectionLine(entrance, candidate) {
  return {
    type: "Feature",
    properties: {},
    geometry: {
      type: "LineString",
      coordinates: [[Number(candidate.longitude), Number(candidate.latitude)], [Number(entrance.longitude), Number(entrance.latitude)]],
    },
  };
}

function distanceMetres(a, b) {
  const radians = (value) => value * Math.PI / 180;
  const lat1 = radians(a[1]);
  const lat2 = radians(b[1]);
  const deltaLatitude = lat2 - lat1;
  const deltaLongitude = radians(b[0] - a[0]);
  const value = Math.sin(deltaLatitude / 2) ** 2
    + Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLongitude / 2) ** 2;
  return 2 * 6_371_008.8 * Math.asin(Math.sqrt(value));
}

export function connectorDistanceMetres(geometry) {
  return geometry.geometry.coordinates.slice(1).reduce(
    (total, point, index) => total + distanceMetres(geometry.geometry.coordinates[index], point), 0,
  );
}

export function candidateSummary(candidate) {
  return `${candidate.display_label || candidate.label} · ${candidate.distance_label}`;
}

function removeIfPresent(map, kind, id) {
  const getter = kind === "layer" ? "getLayer" : "getSource";
  const remover = kind === "layer" ? "removeLayer" : "removeSource";
  if (map[getter]?.(id)) map[remover](id);
}

function fitConnectionMap(map, maplibregl, entrance, candidates) {
  const coordinates = [[Number(entrance.longitude), Number(entrance.latitude)], ...candidates.map((item) => [Number(item.longitude), Number(item.latitude)])];
  if (!coordinates.length || !maplibregl?.LngLatBounds) return;
  const bounds = coordinates.reduce((value, point) => value.extend(point), new maplibregl.LngLatBounds(coordinates[0], coordinates[0]));
  map.fitBounds(bounds, { padding: 70, maxZoom: 19, duration: 0 });
}

export function createEntranceRoutingConnection({ root, selector = null, maplibregl = null }) {
  if (!root?.dataset?.candidatesUrl) return null;
  const findButton = root.querySelector("#find-routing-candidates");
  const editPointButton = root.querySelector("#edit-entrance-point");
  const status = root.querySelector("#routing-candidate-status");
  const list = root.querySelector("#routing-candidate-list");
  const proposal = root.querySelector("#routing-connection-proposal");
  const noCandidates = root.querySelector("#routing-no-candidates");
  const nodeInput = root.querySelector("#routing-node-id");
  const proposalLabel = root.querySelector("[data-proposal-label]");
  const proposalDistance = root.querySelector("[data-proposal-distance]");
  const connectorDistance = root.querySelector("[data-connector-distance]");
  const proposalWarning = root.querySelector("[data-proposal-warning]");
  const chooseAnother = root.querySelector("#choose-another-routing-node");
  const connectorInput = root.querySelector("#routing-connector-geometry");
  const undoBend = root.querySelector("#undo-connector-bend");
  const resetConnector = root.querySelector("#reset-connector");
  const map = selector?.map || null;
  let payload = null;
  let selected = null;
  let mapHandlersBound = false;

  function withLoadedStyle(callback) {
    if (!map) return;
    if (map.isStyleLoaded?.()) callback();
    else map.once("load", callback);
  }

  function setLink(data) {
    if (!map) return;
    const source = map.getSource(LINK_SOURCE_ID);
    if (source) source.setData(data);
    else {
      map.addSource(LINK_SOURCE_ID, { type: "geojson", data });
      map.addLayer({
        id: LINK_LAYER_ID, type: "line", source: LINK_SOURCE_ID,
        paint: { "line-color": "#1565c0", "line-width": 4, "line-dasharray": [1.5, 1.5] },
      });
    }
  }

  function updateConnector() {
    if (!selected?.connector) return;
    connectorInput.value = JSON.stringify(selected.connector.geometry);
    connectorDistance.textContent = `${connectorDistanceMetres(selected.connector).toFixed(1)} m`;
    setLink(selected.connector);
  }

  function updateCandidateSource() {
    if (!map || !payload) return;
    const data = structuredClone(payload.map);
    for (const feature of data.features) {
      if (feature.properties.kind === "candidate") feature.properties.selected = feature.properties.id === selected?.id;
    }
    map.getSource(SOURCE_ID)?.setData(data);
  }

  function choose(candidate) {
    const current = payload.current_connection;
    const stored = current?.node_id === candidate.id && current.connector_geometry
      ? { type: "Feature", properties: {}, geometry: structuredClone(current.connector_geometry) }
      : proposedConnectionLine(payload.entrance, candidate);
    selected = { ...candidate, connector: stored };
    nodeInput.value = candidate.id;
    proposalLabel.textContent = candidate.display_label || candidate.label;
    proposalDistance.textContent = candidate.distance_label;
    proposalWarning.hidden = candidate.distance_band !== "questionable";
    proposal.hidden = false;
    status.textContent = `Proposed ${candidateSummary(candidate)}. Confirm below to save this connection.`;
    updateCandidateSource();
    updateConnector();
    proposal.scrollIntoView?.({ block: "nearest", behavior: "smooth" });
  }

  function renderCandidateList(candidates) {
    list.replaceChildren();
    for (const candidate of candidates) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `routing-candidate routing-candidate--${candidate.distance_band}`;
      const title = document.createElement("strong");
      title.textContent = candidate.display_label || candidate.label;
      const detail = document.createElement("span");
      detail.textContent = `${candidate.distance_label} · ${candidate.distance_band === "nearby" ? "Nearby" : "Questionable distance"}`;
      button.append(title, detail);
      button.addEventListener("click", () => choose(candidate));
      list.append(button);
    }
  }

  function renderMap() {
    if (!map || !payload) return;
    removeIfPresent(map, "layer", LINK_LAYER_ID);
    removeIfPresent(map, "source", LINK_SOURCE_ID);
    removeIfPresent(map, "layer", NODE_LAYER_ID);
    removeIfPresent(map, "layer", SEGMENT_LAYER_ID);
    removeIfPresent(map, "source", SOURCE_ID);
    map.addSource(SOURCE_ID, { type: "geojson", data: payload.map });
    map.addLayer({
      id: SEGMENT_LAYER_ID, type: "line", source: SOURCE_ID,
      filter: ["==", ["get", "kind"], "segment"],
      paint: { "line-color": "#7957c8", "line-width": 5, "line-opacity": .72 },
    });
    map.addLayer({
      id: NODE_LAYER_ID, type: "circle", source: SOURCE_ID,
      filter: ["==", ["get", "kind"], "candidate"],
      paint: {
        "circle-color": ["case", ["==", ["get", "selected"], true], "#1565c0", ["==", ["get", "distance_band"], "nearby"], "#17663c", "#c46b13"],
        "circle-radius": ["case", ["==", ["get", "selected"], true], 11, 9],
        "circle-stroke-color": "#ffffff", "circle-stroke-width": 3,
      },
    });
    if (!mapHandlersBound) {
      map.on("click", NODE_LAYER_ID, (event) => {
        const id = event.features?.[0]?.properties?.id;
        const candidate = payload.candidates.find((item) => item.id === id);
        if (candidate) choose(candidate);
      });
      map.on("mouseenter", NODE_LAYER_ID, () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", NODE_LAYER_ID, () => { map.getCanvas().style.cursor = ""; });
      map.on("click", (event) => {
        if (!selected || !map.getLayer(NODE_LAYER_ID)) return;
        const candidateHit = map.queryRenderedFeatures(event.point, { layers: [NODE_LAYER_ID] }).length > 0;
        if (candidateHit) return;
        const points = selected.connector.geometry.coordinates;
        points.splice(points.length - 1, 0, [Number(event.lngLat.lng.toFixed(6)), Number(event.lngLat.lat.toFixed(6))]);
        updateConnector();
        status.textContent = "Connector bend added. Confirm only if the line follows an actually walkable arrival approach.";
      });
      mapHandlersBound = true;
    }
    fitConnectionMap(map, maplibregl, payload.entrance, payload.candidates);
  }

  async function findCandidates() {
    selector?.setPointSelectionEnabled(false);
    findButton.disabled = true;
    editPointButton.hidden = false;
    proposal.hidden = true;
    noCandidates.hidden = true;
    status.textContent = "Finding active walkable-network nodes near the saved entrance point…";
    try {
      const response = await fetch(root.dataset.candidatesUrl, { headers: { Accept: "application/json" }, credentials: "same-origin" });
      if (!response.ok) throw new Error(`Candidate request failed (${response.status})`);
      payload = await response.json();
      renderCandidateList(payload.candidates);
      if (!payload.candidates.length) {
        noCandidates.hidden = false;
        status.textContent = "No suitable active connected node was found within 75 m.";
      } else {
        status.textContent = `${payload.candidates.length} candidate${payload.candidates.length === 1 ? "" : "s"} found, ordered nearest first. Select a marker or list item to inspect it.`;
        withLoadedStyle(renderMap);
      }
    } catch (error) {
      console.error("Routing candidates could not be loaded", error);
      status.textContent = "Nearby routing candidates could not be loaded. No connection was changed.";
      status.setAttribute("role", "alert");
    } finally {
      findButton.disabled = false;
    }
  }

  function returnToPointEditing() {
    selector?.setPointSelectionEnabled(true);
    editPointButton.hidden = true;
    proposal.hidden = true;
    noCandidates.hidden = true;
    list.replaceChildren();
    selected = null;
    nodeInput.value = "";
    connectorInput.value = "";
    status.textContent = "Entrance-point editing restored. Save any coordinate change before finding routing candidates.";
    if (map) {
      removeIfPresent(map, "layer", LINK_LAYER_ID);
      removeIfPresent(map, "source", LINK_SOURCE_ID);
      removeIfPresent(map, "layer", NODE_LAYER_ID);
      removeIfPresent(map, "layer", SEGMENT_LAYER_ID);
      removeIfPresent(map, "source", SOURCE_ID);
    }
  }

  findButton?.addEventListener("click", findCandidates);
  editPointButton?.addEventListener("click", returnToPointEditing);
  chooseAnother?.addEventListener("click", () => {
    selected = null;
    nodeInput.value = "";
    connectorInput.value = "";
    proposal.hidden = true;
    status.textContent = "Choose another candidate marker or list item.";
    updateCandidateSource();
    if (map) {
      removeIfPresent(map, "layer", LINK_LAYER_ID);
      removeIfPresent(map, "source", LINK_SOURCE_ID);
    }
  });
  undoBend?.addEventListener("click", () => {
    if (!selected || selected.connector.geometry.coordinates.length <= 2) return;
    selected.connector.geometry.coordinates.splice(-2, 1);
    updateConnector();
  });
  resetConnector?.addEventListener("click", () => {
    if (!selected) return;
    selected.connector = proposedConnectionLine(payload.entrance, selected);
    updateConnector();
  });
  root.closest("main")?.querySelector("#entrance-map")?.addEventListener("entrancepointchange", () => {
    findButton.disabled = true;
    returnToPointEditing();
    findButton.disabled = true;
    status.textContent = "The entrance point changed. Save the entrance before finding connections for its new position.";
  });

  if (map && root.dataset.currentNodeId) {
    withLoadedStyle(() => {
      const point = {
        type: "Feature", properties: { id: root.dataset.currentNodeId },
        geometry: { type: "Point", coordinates: [Number(root.dataset.currentNodeLongitude), Number(root.dataset.currentNodeLatitude)] },
      };
      map.addSource(CURRENT_SOURCE_ID, { type: "geojson", data: point });
      map.addLayer({
        id: CURRENT_LAYER_ID, type: "circle", source: CURRENT_SOURCE_ID,
        paint: { "circle-color": "#1565c0", "circle-radius": 9, "circle-stroke-color": "#fff", "circle-stroke-width": 3 },
      });
    });
  }

  return { findCandidates, choose, returnToPointEditing };
}
