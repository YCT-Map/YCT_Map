export const DESTINATION_SOURCE_ID = "demo-destinations";
export const DESTINATION_CLUSTER_LAYER_ID = "destination-clusters";
export const DESTINATION_CLUSTER_COUNT_LAYER_ID = "destination-cluster-counts";
export const DESTINATION_POINT_LAYER_ID = "demo-destination-circles";
export const DESTINATION_LABEL_LAYER_ID = "demo-destination-labels";
export const SELECTED_DESTINATION_SOURCE_ID = "selected-destination";
export const SELECTED_DESTINATION_MARKER_LAYER_ID = "selected-destination-marker";
export const SELECTED_DESTINATION_HALO_LAYER_ID = "selected-destination-halo";
export const DESTINATION_CLUSTER_CONFIG = Object.freeze({
  cluster: true,
  clusterRadius: 50,
  clusterMaxZoom: 16,
});
const CAMPUS_SOURCE_ID = "yabatech-campus-orientation";
const CAMPUS_LABEL_SOURCE_ID = "yabatech-campus-label-point";
const CAMPUS_FILL_LAYER_ID = "yabatech-campus-fill";
const CAMPUS_LINE_LAYER_ID = "yabatech-campus-outline";
const CAMPUS_LABEL_LAYER_ID = "yabatech-campus-label";
const NETWORK_SOURCE_ID = "demo-walkable-network";
const NETWORK_LINE_LAYER_ID = "demo-walkable-network-lines";
const NETWORK_NODE_LAYER_ID = "demo-walkable-network-nodes";
const ROUTE_SOURCE_ID = "calculated-demo-route";
const ROUTE_LAYER_ID = "calculated-demo-route-line";
const USER_ROUTE_SOURCE_ID = "user-demo-route";
const USER_ROUTE_CASING_LAYER_ID = "user-demo-route-casing";
const USER_ROUTE_LAYER_ID = "user-demo-route-line";
const USER_ENDPOINT_SOURCE_ID = "user-route-endpoints";
const USER_ENDPOINT_CIRCLE_LAYER_ID = "user-route-endpoint-circles";
const USER_ENDPOINT_LABEL_LAYER_ID = "user-route-endpoint-labels";
const USER_LOCATION_SOURCE_ID = "live-user-location";
const USER_ACCURACY_SOURCE_ID = "live-user-accuracy";
const USER_ACCURACY_LAYER_ID = "live-user-accuracy-fill";
const USER_LOCATION_DOT_LAYER_ID = "live-user-location-dot";
const USER_LOCATION_CHEVRON_LAYER_ID = "live-user-location-chevron";
const CONTRIBUTION_SOURCE_ID = "pending-contribution-point";
const CONTRIBUTION_LAYER_ID = "pending-contribution-point-circle";
const FOLLOW_CAMERA_THROTTLE_MS = 120;

const DESTINATION_COLOR = [
  "match",
  ["get", "category"],
  "health", "#c25345",
  "food", "#e2a927",
  "hostel", "#7758a6",
  "office", "#397aa8",
  "library", "#208569",
  "#17663c",
];

export const NAVIGATION_FOREGROUND_LAYER_ORDER = Object.freeze([
  ROUTE_LAYER_ID,
  USER_ROUTE_CASING_LAYER_ID,
  USER_ROUTE_LAYER_ID,
  USER_ACCURACY_LAYER_ID,
  SELECTED_DESTINATION_HALO_LAYER_ID,
  SELECTED_DESTINATION_MARKER_LAYER_ID,
  USER_ENDPOINT_CIRCLE_LAYER_ID,
  USER_ENDPOINT_LABEL_LAYER_ID,
  USER_LOCATION_DOT_LAYER_ID,
  USER_LOCATION_CHEVRON_LAYER_ID,
]);

function featureCollection(features = []) {
  return { type: "FeatureCollection", features };
}

export function navigationCameraLayout({ viewportWidth, viewportHeight, routePanelHeight = 0 } = {}) {
  const width = Math.max(320, Number(viewportWidth) || 320);
  const height = Math.max(320, Number(viewportHeight) || 320);
  const panel = Math.max(0, Math.min(Number(routePanelHeight) || 0, height * 0.55));
  const mobile = width < 672;
  const bottom = mobile ? panel + 24 : 32;
  const usableHeight = height - bottom;
  const lookAheadOffset = Math.max(35, Math.min(120, usableHeight * 0.16));
  return {
    padding: { top: 24, right: mobile ? 24 : 320, bottom, left: 24 },
    offset: [mobile ? 0 : -130, lookAheadOffset],
  };
}

export function createFollowModeState(onChange = () => {}) {
  let mode = "north-up";
  function change(next) { mode = next; onChange(mode); return mode; }
  return {
    enable: () => change("following"),
    suspendForGesture(originalEvent) {
      if (mode !== "following" || !originalEvent) return mode;
      return change("suspended");
    },
    resume: () => mode === "north-up" ? mode : change("following"),
    northUp: () => change("north-up"),
    isEnabled: () => mode !== "north-up",
    isFollowing: () => mode === "following",
    getMode: () => mode,
  };
}

export function userLocationFeature(position, headingDegrees = null, headingSource = null) {
  const properties = { accuracy: position.accuracyMetres };
  if (Number.isFinite(headingDegrees)) {
    properties.heading = headingDegrees;
    properties.heading_source = headingSource;
  }
  return { type: "Feature", geometry: { type: "Point",
    coordinates: [position.longitude, position.latitude] }, properties };
}

export function destinationSourceDefinition(features = []) {
  return {
    type: "geojson",
    data: featureCollection(features),
    ...DESTINATION_CLUSTER_CONFIG,
  };
}

export function selectedDestinationSourceDefinition() {
  return { type: "geojson", data: featureCollection() };
}

export function destinationLayerDefinitions() {
  const unclustered = ["!", ["has", "point_count"]];
  const clustered = ["has", "point_count"];
  return [
    {
      id: DESTINATION_CLUSTER_LAYER_ID,
      type: "circle",
      source: DESTINATION_SOURCE_ID,
      filter: clustered,
      paint: {
        "circle-radius": ["step", ["get", "point_count"], 20, 10, 24, 25, 28],
        "circle-color": ["step", ["get", "point_count"], "#17663c", 10, "#145733", 25, "#0d442a"],
        "circle-stroke-color": "rgba(255,255,255,.96)",
        "circle-stroke-width": 2.5,
        "circle-opacity": 0.94,
      },
    },
    {
      id: DESTINATION_CLUSTER_COUNT_LAYER_ID,
      type: "symbol",
      source: DESTINATION_SOURCE_ID,
      filter: clustered,
      layout: {
        "text-field": ["get", "point_count_abbreviated"],
        "text-size": ["step", ["get", "point_count"], 12, 10, 13, 25, 14],
        "text-font": ["Noto Sans Regular"],
        "text-allow-overlap": true,
        "text-ignore-placement": true,
      },
      paint: { "text-color": "#ffffff", "text-halo-color": "rgba(13,68,42,.35)", "text-halo-width": 1 },
    },
    {
      id: DESTINATION_POINT_LAYER_ID,
      type: "circle",
      source: DESTINATION_SOURCE_ID,
      filter: unclustered,
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 14, 7, 18, 11],
        "circle-color": DESTINATION_COLOR,
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 3,
        "circle-opacity": 0.96,
      },
    },
    {
      id: DESTINATION_LABEL_LAYER_ID,
      type: "symbol",
      source: DESTINATION_SOURCE_ID,
      filter: unclustered,
      minzoom: 16.3,
      layout: {
        "text-field": ["get", "name"],
        "text-size": 11,
        "text-offset": [0, 1.5],
        "text-anchor": "top",
        "text-font": ["Noto Sans Regular"],
      },
      paint: {
        "text-color": "#163127",
        "text-halo-color": "#ffffff",
        "text-halo-width": 1.5,
      },
    },
  ];
}

export function selectedDestinationLayerDefinitions() {
  return [
    {
      id: SELECTED_DESTINATION_HALO_LAYER_ID,
      type: "circle",
      source: SELECTED_DESTINATION_SOURCE_ID,
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 14, 13, 18, 18],
        "circle-color": "rgba(255, 255, 255, 0)",
        "circle-stroke-color": "#e2b431",
        "circle-stroke-width": 4,
      },
    },
    {
      id: SELECTED_DESTINATION_MARKER_LAYER_ID,
      type: "circle",
      source: SELECTED_DESTINATION_SOURCE_ID,
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 14, 8, 18, 12],
        "circle-color": DESTINATION_COLOR,
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 3,
        "circle-opacity": 1,
      },
    },
  ];
}

export function selectedDestinationData(feature) {
  if (!feature || feature.properties?.destination_type === "internal") return featureCollection();
  const geometry = feature.geometry?.type === "Point"
    ? { ...feature.geometry, coordinates: [...feature.geometry.coordinates] }
    : feature.geometry;
  return featureCollection([{ ...feature, geometry, properties: { ...feature.properties } }]);
}

export function setSelectedDestination(map, feature) {
  const source = map.getSource?.(SELECTED_DESTINATION_SOURCE_ID);
  if (!source) return false;
  source.setData(selectedDestinationData(feature));
  return true;
}

export function focusDestination(map, feature) {
  setSelectedDestination(map, feature);
  map.flyTo({ center: feature.geometry.coordinates, zoom: 18, duration: 900, essential: false });
}

export function setVisibleDestinationFeatures(map, features) {
  const source = map.getSource?.(DESTINATION_SOURCE_ID);
  if (!source) return false;
  source.setData(featureCollection(features));
  return true;
}

export async function expandDestinationCluster(map, feature, { warn = console.warn } = {}) {
  const clusterId = Number(feature?.properties?.cluster_id);
  const coordinates = feature?.geometry?.coordinates;
  const source = map.getSource?.(DESTINATION_SOURCE_ID);
  if (!Number.isFinite(clusterId) || !Array.isArray(coordinates) || !source?.getClusterExpansionZoom) return false;
  try {
    const zoom = await source.getClusterExpansionZoom(clusterId);
    if (!Number.isFinite(zoom)) return false;
    map.easeTo({ center: coordinates, zoom, duration: 650, essential: false });
    return true;
  } catch (error) {
    warn("Destination cluster could not expand", error);
    return false;
  }
}

export function bindDestinationInteractions({ map, featureIndex, onSelect }) {
  map.on("click", DESTINATION_CLUSTER_LAYER_ID, (event) => {
    return expandDestinationCluster(map, event.features?.[0]);
  });
  for (const layerId of [DESTINATION_CLUSTER_LAYER_ID, DESTINATION_POINT_LAYER_ID, DESTINATION_LABEL_LAYER_ID]) {
    map.on("mouseenter", layerId, () => { map.getCanvas().style.cursor = "pointer"; });
    map.on("mouseleave", layerId, () => { map.getCanvas().style.cursor = ""; });
  }
  for (const layerId of [DESTINATION_POINT_LAYER_ID, DESTINATION_LABEL_LAYER_ID]) {
    map.on("click", layerId, (event) => {
      const selectedId = String(event.features?.[0]?.id || event.features?.[0]?.properties?.id || "");
      const selected = featureIndex.get(selectedId);
      if (selected) onSelect(selected);
    });
  }
}

export function raiseNavigationLayers(map) {
  for (const layerId of NAVIGATION_FOREGROUND_LAYER_ORDER) {
    if (map.getLayer?.(layerId)) map.moveLayer(layerId);
  }
}

function accuracyPolygon(position, points = 48) {
  const latitudeRadians = position.latitude * Math.PI / 180;
  const latitudeDegreesPerMetre = 1 / 111_320;
  const longitudeDegreesPerMetre = 1 / (111_320 * Math.max(Math.cos(latitudeRadians), 0.01));
  const coordinates = [];
  for (let index = 0; index <= points; index += 1) {
    const angle = index / points * Math.PI * 2;
    coordinates.push([
      position.longitude + Math.cos(angle) * position.accuracyMetres * longitudeDegreesPerMetre,
      position.latitude + Math.sin(angle) * position.accuracyMetres * latitudeDegreesPerMetre,
    ]);
  }
  return { type: "Feature", geometry: { type: "Polygon", coordinates: [coordinates] }, properties: {} };
}

async function loadCampusBoundary(url) {
  try {
    const response = await fetch(url, { headers: { Accept: "application/geo+json, application/json" } });
    if (!response.ok) throw new Error(`Campus boundary request failed with ${response.status}.`);
    const collection = await response.json();
    const geometryType = collection?.features?.[0]?.geometry?.type;
    if (collection?.type !== "FeatureCollection" || !["Polygon", "MultiPolygon"].includes(geometryType)) {
      throw new Error("Campus boundary is not a valid polygon FeatureCollection.");
    }
    return collection;
  } catch (error) {
    console.warn("Campus orientation boundary could not load", error);
    return null;
  }
}

function geometryCoordinates(geometry) {
  if (geometry.type === "Polygon") return geometry.coordinates.flat(1);
  return geometry.coordinates.flat(2);
}

function boundsFor(collection) {
  const coordinates = collection.features.flatMap((feature) => geometryCoordinates(feature.geometry));
  const longitudes = coordinates.map(([longitude]) => longitude);
  const latitudes = coordinates.map(([, latitude]) => latitude);
  return [
    [Math.min(...longitudes), Math.min(...latitudes)],
    [Math.max(...longitudes), Math.max(...latitudes)],
  ];
}

function campusPadding() {
  if (window.matchMedia("(max-width: 41.99rem)").matches) {
    return { top: 190, right: 24, bottom: 96, left: 24 };
  }
  return { top: 112, right: 72, bottom: 72, left: 72 };
}

const CAMPUS_ROUTE_LIMITS = Object.freeze({ minLongitude: 3.20, maxLongitude: 3.55, minLatitude: 6.35, maxLatitude: 6.70 });

export function routeBounds(coordinates) {
  if (!Array.isArray(coordinates) || coordinates.length < 2) {
    throw new Error("Route geometry must contain at least two [longitude, latitude] coordinates.");
  }
  for (const coordinate of coordinates) {
    if (!Array.isArray(coordinate) || coordinate.length !== 2 || !coordinate.every(Number.isFinite)) {
      throw new Error("Route coordinates must be finite [longitude, latitude] pairs.");
    }
    const [longitude, latitude] = coordinate;
    if (longitude < CAMPUS_ROUTE_LIMITS.minLongitude || longitude > CAMPUS_ROUTE_LIMITS.maxLongitude ||
        latitude < CAMPUS_ROUTE_LIMITS.minLatitude || latitude > CAMPUS_ROUTE_LIMITS.maxLatitude) {
      throw new Error("Route geometry is outside the expected YabaTech vicinity; coordinate order may be invalid.");
    }
  }
  const longitudes = coordinates.map(([longitude]) => longitude);
  const latitudes = coordinates.map(([, latitude]) => latitude);
  return [[Math.min(...longitudes), Math.min(...latitudes)], [Math.max(...longitudes), Math.max(...latitudes)]];
}

export function calculateRoutePadding({ mobile, panelHeight, panelWidth, discoveryBottom, viewportHeight }) {
  if (!mobile) return { top: 112, right: Math.ceil(panelWidth) + 48, bottom: 72, left: 72 };
  const top = Math.min(Math.ceil(discoveryBottom) + 16, Math.floor(viewportHeight * 0.30));
  const bottom = Math.min(Math.ceil(panelHeight) + 16, Math.floor(viewportHeight * 0.24));
  return { top: Math.max(64, top), right: 24, bottom: Math.max(72, bottom), left: 24 };
}

function routePadding() {
  const panel = document.querySelector("#user-route-panel");
  const panelHeight = panel?.getBoundingClientRect().height || 300;
  const panelWidth = panel?.getBoundingClientRect().width || 400;
  const discoveryBottom = document.querySelector(".discovery")?.getBoundingClientRect().bottom || 180;
  return calculateRoutePadding({ mobile: window.matchMedia("(max-width: 41.99rem)").matches,
    panelHeight, panelWidth, discoveryBottom, viewportHeight: window.innerHeight });
}

class CampusFocusControl {
  constructor(onFocus) {
    this.onFocus = onFocus;
  }

  onAdd() {
    this.container = document.createElement("div");
    this.container.className = "maplibregl-ctrl maplibregl-ctrl-group";
    this.button = document.createElement("button");
    this.button.type = "button";
    this.button.className = "campus-focus-button";
    this.button.title = "Return to YabaTech campus";
    this.button.setAttribute("aria-label", "Return to YabaTech campus");
    this.button.innerHTML = `
      <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M3 10.5 12 4l9 6.5"></path>
        <path d="M5.5 9.5V20h13V9.5M9 20v-6h6v6"></path>
      </svg>
    `;
    this.button.addEventListener("click", this.onFocus);
    this.container.append(this.button);
    return this.container;
  }

  onRemove() {
    this.button?.removeEventListener("click", this.onFocus);
    this.container?.remove();
  }
}

export async function createMap({ container, config, features, onSelect, onReady, onError,
  onFollowStateChange = () => {} }) {
  const [maplibregl, campusBoundary, demoNetwork] = await Promise.all([
    import(config.moduleUrl),
    loadCampusBoundary(config.campusBoundaryUrl),
    config.debugNetworkUrl ? fetch(config.debugNetworkUrl).then((response) => response.ok ? response.json() : null).catch(() => null) : null,
  ]);
  const featureIndex = new Map(features.map((feature) => [String(feature.id), feature]));
  const campusBounds = campusBoundary ? boundsFor(campusBoundary) : null;
  let visibleFeatures = features;
  let loaded = false;
  let pendingFocus = null;
  let latestUserPosition = null;
  let displayedHeading = null;
  let displayedHeadingSource = null;
  const followMode = createFollowModeState(onFollowStateChange);
  let followCameraTimer = null;
  let liveRouteActive = false;

  const map = new maplibregl.Map({
    container,
    style: config.styleUrl,
    center: config.centre,
    zoom: 16,
    minZoom: 14,
    maxZoom: 20,
    attributionControl: false,
    cooperativeGestures: false,
  });

  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
  map.addControl(new CampusFocusControl(() => focusCampus()), "bottom-right");
  map.addControl(
    new maplibregl.AttributionControl({ compact: true, customAttribution: "YCT Map campus data · OSM-derived UNVERIFIED route data" }),
    "bottom-right",
  );

  map.on("load", () => {
    loaded = true;
    if (campusBoundary) {
      map.addSource(CAMPUS_SOURCE_ID, { type: "geojson", data: campusBoundary });
      map.addLayer({
        id: CAMPUS_FILL_LAYER_ID,
        type: "fill",
        source: CAMPUS_SOURCE_ID,
        paint: {
          "fill-color": "#17663c",
          "fill-opacity": 0.08,
        },
      });
      map.addLayer({
        id: CAMPUS_LINE_LAYER_ID,
        type: "line",
        source: CAMPUS_SOURCE_ID,
        paint: {
          "line-color": "#17663c",
          "line-opacity": 0.72,
          "line-width": ["interpolate", ["linear"], ["zoom"], 13, 1.5, 17, 2.5],
        },
      });
      map.addSource(CAMPUS_LABEL_SOURCE_ID, { type: "geojson", data: {
        type: "Feature", geometry: { type: "Point", coordinates: config.centre },
        properties: { name: "YabaTech Campus" },
      }});
    }
    if (demoNetwork?.features?.length) {
      map.addSource(NETWORK_SOURCE_ID, { type: "geojson", data: demoNetwork });
      map.addLayer({ id: NETWORK_LINE_LAYER_ID, type: "line", source: NETWORK_SOURCE_ID,
        filter: ["==", ["get", "feature_type"], "segment"],
        layout: { visibility: "none" },
        paint: { "line-color": "#6a4bbc", "line-width": 3, "line-opacity": 0.72, "line-dasharray": [2, 2] } });
      map.addLayer({ id: NETWORK_NODE_LAYER_ID, type: "circle", source: NETWORK_SOURCE_ID,
        filter: ["==", ["get", "feature_type"], "node"],
        layout: { visibility: "none" },
        paint: { "circle-radius": 4, "circle-color": "#6a4bbc", "circle-stroke-color": "#fff", "circle-stroke-width": 1.5 } });
      const inspector = document.querySelector("#network-inspector");
      const toggle = document.querySelector("#toggle-demo-network");
      inspector.hidden = false;
      toggle.addEventListener("click", () => {
        const visible = toggle.getAttribute("aria-pressed") !== "true";
        toggle.setAttribute("aria-pressed", String(visible));
        for (const layer of [NETWORK_LINE_LAYER_ID, NETWORK_NODE_LAYER_ID]) map.setLayoutProperty(layer, "visibility", visible ? "visible" : "none");
      });
    }

    if (config.debugRouteUrl) {
      map.addSource(ROUTE_SOURCE_ID, { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addLayer({
        id: ROUTE_LAYER_ID,
        type: "line",
        source: ROUTE_SOURCE_ID,
        paint: {
          "line-color": "#d9472f",
          "line-width": ["interpolate", ["linear"], ["zoom"], 14, 5, 18, 8],
          "line-opacity": 0.96,
        },
      });
    }

    map.addSource(USER_ROUTE_SOURCE_ID, { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    map.addSource(CONTRIBUTION_SOURCE_ID, { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    map.addLayer({ id: CONTRIBUTION_LAYER_ID, type: "circle", source: CONTRIBUTION_SOURCE_ID,
      paint: { "circle-radius": 11, "circle-color": "#f3b51b", "circle-stroke-color": "#7a4d00", "circle-stroke-width": 3 } });
    map.addLayer({ id: USER_ROUTE_CASING_LAYER_ID, type: "line", source: USER_ROUTE_SOURCE_ID,
      paint: { "line-color": "rgba(255,255,255,.92)", "line-width": ["interpolate", ["linear"], ["zoom"], 14, 8, 18, 12] } });
    map.addLayer({ id: USER_ROUTE_LAYER_ID, type: "line", source: USER_ROUTE_SOURCE_ID,
      paint: { "line-color": "#2563eb", "line-width": ["interpolate", ["linear"], ["zoom"], 14, 5, 18, 8], "line-opacity": .96 } });
    map.addSource(USER_ENDPOINT_SOURCE_ID, { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    map.addLayer({ id: USER_ENDPOINT_CIRCLE_LAYER_ID, type: "circle", source: USER_ENDPOINT_SOURCE_ID,
      paint: { "circle-radius": ["match", ["get", "role"], "destination", 12, "matched", 8, 10],
        "circle-color": ["match", ["get", "role"], "destination", "#d63d32", "matched", "rgba(255,255,255,.2)", "#2563eb"],
        "circle-stroke-color": ["match", ["get", "role"], "matched", "#2563eb", "#fff"], "circle-stroke-width": 3 } });
    map.addLayer({ id: USER_ENDPOINT_LABEL_LAYER_ID, type: "symbol", source: USER_ENDPOINT_SOURCE_ID,
      layout: { "text-field": ["match", ["get", "role"], "destination", "D", "matched", "", "S"], "text-size": 11, "text-font": ["Noto Sans Regular"], "text-allow-overlap": true, "text-ignore-placement": true },
      paint: { "text-color": "#fff" } });

    map.addSource(USER_ACCURACY_SOURCE_ID, { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    map.addLayer({ id: USER_ACCURACY_LAYER_ID, type: "fill", source: USER_ACCURACY_SOURCE_ID,
      paint: { "fill-color": "#1677ff", "fill-opacity": 0.12, "fill-outline-color": "rgba(22,119,255,.42)" } });
    map.addSource(USER_LOCATION_SOURCE_ID, { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    map.addLayer({ id: USER_LOCATION_DOT_LAYER_ID, type: "circle", source: USER_LOCATION_SOURCE_ID,
      filter: ["!", ["has", "heading"]],
      paint: { "circle-radius": 9, "circle-color": "#1677ff", "circle-stroke-color": "#fff", "circle-stroke-width": 3 } });
    map.addLayer({ id: USER_LOCATION_CHEVRON_LAYER_ID, type: "symbol", source: USER_LOCATION_SOURCE_ID,
      filter: ["has", "heading"],
      layout: { "text-field": "▲", "text-size": 22, "text-rotate": ["get", "heading"], "text-rotation-alignment": "map",
        "text-allow-overlap": true, "text-ignore-placement": true },
      paint: { "text-color": "#1677ff", "text-halo-color": "#fff", "text-halo-width": 2 } });

    map.addSource(DESTINATION_SOURCE_ID, destinationSourceDefinition(visibleFeatures));
    map.addSource(SELECTED_DESTINATION_SOURCE_ID, selectedDestinationSourceDefinition());
    for (const layer of destinationLayerDefinitions()) map.addLayer(layer);
    for (const layer of selectedDestinationLayerDefinitions()) map.addLayer(layer);
    if (campusBoundary) {
      map.addLayer({ id: CAMPUS_LABEL_LAYER_ID, type: "symbol", source: CAMPUS_LABEL_SOURCE_ID, minzoom: 13,
        layout: { "text-field": ["get", "name"], "text-size": ["interpolate", ["linear"], ["zoom"], 13, 13, 17, 17], "text-font": ["Noto Sans Regular"], "text-letter-spacing": 0.04 },
        paint: { "text-color": "#0d442a", "text-halo-color": "rgba(255, 255, 252, 0.96)", "text-halo-width": 2 } });
    }
    raiseNavigationLayers(map);
    bindDestinationInteractions({ map, featureIndex, onSelect });

    if (pendingFocus) {
      focus(pendingFocus);
      pendingFocus = null;
    } else {
      focusCampus({ animate: false });
    }
    onReady();
  });

  map.on("error", (event) => {
    if (!loaded) {
      onError(event?.error || new Error("Map style failed to load."));
    }
  });

  for (const eventName of ["dragstart", "rotatestart", "zoomstart"]) {
    map.on(eventName, (event) => {
      followMode.suspendForGesture(event?.originalEvent);
    });
  }

  function focus(feature) {
    if (!loaded) {
      pendingFocus = feature;
      return;
    }
    focusDestination(map, feature);
  }

  function focusCampus({ animate = true } = {}) {
    const duration = animate ? 700 : 0;
    if (campusBounds) {
      map.fitBounds(campusBounds, {
        padding: campusPadding(),
        maxZoom: 16.2,
        duration,
        essential: false,
      });
      return;
    }
    map.flyTo({ center: config.centre, zoom: 16, duration, essential: false });
  }

  function setVisibleFeatures(nextFeatures) {
    visibleFeatures = nextFeatures;
    if (loaded) setVisibleDestinationFeatures(map, visibleFeatures);
  }

  function showRoute(routeFeature) {
    if (!loaded || !map.getSource(ROUTE_SOURCE_ID)) return;
    map.getSource(ROUTE_SOURCE_ID).setData({ type: "FeatureCollection", features: [routeFeature] });
    const coordinates = routeFeature.geometry.coordinates;
    const longitudes = coordinates.map(([longitude]) => longitude);
    const latitudes = coordinates.map(([, latitude]) => latitude);
    map.fitBounds(
      [[Math.min(...longitudes), Math.min(...latitudes)], [Math.max(...longitudes), Math.max(...latitudes)]],
      { padding: campusPadding(), maxZoom: 18, duration: 700, essential: false },
    );
  }

  function showUserRoute(routeFeature, origin, destination, { originType = "manual", replacement = false, arrivalName = "" } = {}) {
    if (!loaded || routeFeature.geometry.type !== "LineString") return;
    const coordinates = routeFeature.geometry.coordinates;
    let bounds;
    try {
      bounds = routeBounds(coordinates);
    } catch (error) {
      console.error("Unsafe route geometry was not rendered", error);
      throw error;
    }
    map.getSource(USER_ROUTE_SOURCE_ID).setData({ type: "FeatureCollection", features: [routeFeature] });
    liveRouteActive = originType === "live";
    setUserRouteStale(false);
    map.getSource(USER_ENDPOINT_SOURCE_ID).setData({ type: "FeatureCollection", features: [
      { type: "Feature", geometry: { type: "Point", coordinates: coordinates[0] }, properties: {
        role: originType === "live" ? "matched" : "start", name: originType === "live" ? "Matched route start" : origin.properties.name,
      } },
      { type: "Feature", geometry: { type: "Point", coordinates: coordinates.at(-1) }, properties: {
        role: "destination", name: arrivalName || destination.properties.name,
      } },
    ] });
    if (!replacement) {
      map.fitBounds(bounds, { padding: routePadding(), maxZoom: 17.5, duration: 700, essential: false });
    }
  }

  function clearUserRoute() {
    liveRouteActive = false;
    map.getSource(USER_ROUTE_SOURCE_ID)?.setData({ type: "FeatureCollection", features: [] });
    map.getSource(USER_ENDPOINT_SOURCE_ID)?.setData({ type: "FeatureCollection", features: [] });
  }

  function setUserRouteStale(stale) {
    if (!loaded) return;
    map.setPaintProperty(USER_ROUTE_LAYER_ID, "line-opacity", stale ? 0.38 : 0.96);
    map.setPaintProperty(USER_ROUTE_CASING_LAYER_ID, "line-opacity", stale ? 0.45 : 1);
  }

  function renderUserLocation() {
    if (!loaded || !latestUserPosition) return;
    map.getSource(USER_LOCATION_SOURCE_ID).setData({ type: "FeatureCollection", features: [
      userLocationFeature(latestUserPosition, displayedHeading, displayedHeadingSource),
    ] });
  }

  function routePanelHeight() {
    if (!liveRouteActive) return 0;
    const panel = document.querySelector("#user-route-panel");
    return panel && !panel.hidden ? panel.getBoundingClientRect().height : 0;
  }

  function applyFollowCamera({ immediate = false } = {}) {
    if (!loaded || !latestUserPosition || !followMode.isFollowing()) return false;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const layout = navigationCameraLayout({ viewportWidth: map.getContainer().clientWidth,
      viewportHeight: map.getContainer().clientHeight, routePanelHeight: routePanelHeight() });
    const options = { center: [latestUserPosition.longitude, latestUserPosition.latitude],
      zoom: Math.max(map.getZoom(), 17), padding: layout.padding, offset: layout.offset,
      duration: reducedMotion || immediate ? 0 : 180, essential: false };
    if (displayedHeading !== null) options.bearing = displayedHeading;
    map.easeTo(options);
    return true;
  }

  function scheduleFollowCamera() {
    if (!followMode.isFollowing() || followCameraTimer !== null) return;
    followCameraTimer = globalThis.setTimeout(() => {
      followCameraTimer = null;
      applyFollowCamera();
    }, FOLLOW_CAMERA_THROTTLE_MS);
  }

  function showUserLocation(position, { focus: shouldFocus = false } = {}) {
    latestUserPosition = position;
    displayedHeading = Number.isFinite(position.displayedHeadingDegrees)
      ? position.displayedHeadingDegrees : Number.isFinite(position.headingDegrees) ? position.headingDegrees : null;
    displayedHeadingSource = position.displayedHeadingSource || (displayedHeading !== null ? "movement" : null);
    if (!loaded) return;
    renderUserLocation();
    map.getSource(USER_ACCURACY_SOURCE_ID).setData({ type: "FeatureCollection", features: [accuracyPolygon(position)] });
    if (followMode.isFollowing()) scheduleFollowCamera();
    else if (shouldFocus) recenterUserLocation();
  }

  function updateUserHeading({ headingDegrees, source }) {
    displayedHeading = Number.isFinite(headingDegrees) ? headingDegrees : null;
    displayedHeadingSource = source || null;
    renderUserLocation();
    scheduleFollowCamera();
  }

  function enableFollowDirection() {
    if (!latestUserPosition) return "north-up";
    followMode.enable();
    applyFollowCamera({ immediate: true });
    return "following";
  }

  function northUp() {
    followMode.northUp();
    if (followCameraTimer !== null) globalThis.clearTimeout(followCameraTimer);
    followCameraTimer = null;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    map.easeTo({ bearing: 0, duration: reducedMotion ? 0 : 350, essential: false });
    return "north-up";
  }

  function recenterUserLocation() {
    if (!loaded || !latestUserPosition) return false;
    if (followMode.isEnabled()) {
      followMode.resume();
      applyFollowCamera({ immediate: true });
      return true;
    }
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    map.easeTo({ center: [latestUserPosition.longitude, latestUserPosition.latitude], zoom: Math.max(map.getZoom(), 17),
      duration: reducedMotion ? 0 : 650, essential: false });
    return true;
  }

  function clearUserLocation() {
    followMode.northUp();
    displayedHeading = null;
    displayedHeadingSource = null;
    if (followCameraTimer !== null) globalThis.clearTimeout(followCameraTimer);
    followCameraTimer = null;
    latestUserPosition = null;
    map.getSource(USER_LOCATION_SOURCE_ID)?.setData({ type: "FeatureCollection", features: [] });
    map.getSource(USER_ACCURACY_SOURCE_ID)?.setData({ type: "FeatureCollection", features: [] });
  }

  function clearContributionPoint() {
    map.getSource(CONTRIBUTION_SOURCE_ID)?.setData({ type: "FeatureCollection", features: [] });
  }

  function pickContributionPoint(callback) {
    if (!loaded) return false;
    map.getCanvas().style.cursor = "crosshair";
    map.once("click", (event) => {
      map.getCanvas().style.cursor = "";
      const coordinates = [event.lngLat.lng, event.lngLat.lat];
      map.getSource(CONTRIBUTION_SOURCE_ID).setData({ type: "FeatureCollection", features: [{
        type: "Feature", geometry: { type: "Point", coordinates }, properties: {},
      }] });
      callback(coordinates);
    });
    return true;
  }

  return { focus, focusCampus, setVisibleFeatures, showRoute, showUserRoute, clearUserRoute, setUserRouteStale,
    showUserLocation, updateUserHeading, enableFollowDirection, northUp, recenterUserLocation, clearUserLocation,
    pickContributionPoint, clearContributionPoint, map };
}
