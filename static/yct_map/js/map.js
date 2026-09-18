const SOURCE_ID = "demo-destinations";
const CIRCLE_LAYER_ID = "demo-destination-circles";
const SELECTED_LAYER_ID = "demo-destination-selected";
const LABEL_LAYER_ID = "demo-destination-labels";
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

function routePadding() {
  const panel = document.querySelector("#user-route-panel");
  const panelHeight = panel?.getBoundingClientRect().height || 300;
  const panelWidth = panel?.getBoundingClientRect().width || 400;
  if (window.matchMedia("(max-width: 41.99rem)").matches) {
    const discoveryBottom = document.querySelector(".discovery")?.getBoundingClientRect().bottom || 180;
    return { top: Math.ceil(discoveryBottom) + 24, right: 28, bottom: Math.ceil(panelHeight) + 24, left: 28 };
  }
  return { top: 112, right: Math.ceil(panelWidth) + 48, bottom: 72, left: 72 };
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

export async function createMap({ container, config, features, onSelect, onReady, onError }) {
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
  let selectedFeatureId = "";

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
    new maplibregl.AttributionControl({ compact: true, customAttribution: "DEMO destinations · OSM-derived UNVERIFIED route data" }),
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
    map.addLayer({ id: USER_ROUTE_CASING_LAYER_ID, type: "line", source: USER_ROUTE_SOURCE_ID,
      paint: { "line-color": "rgba(255,255,255,.92)", "line-width": ["interpolate", ["linear"], ["zoom"], 14, 8, 18, 12] } });
    map.addLayer({ id: USER_ROUTE_LAYER_ID, type: "line", source: USER_ROUTE_SOURCE_ID,
      paint: { "line-color": "#2563eb", "line-width": ["interpolate", ["linear"], ["zoom"], 14, 5, 18, 8], "line-opacity": .96 } });
    map.addSource(USER_ENDPOINT_SOURCE_ID, { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    map.addLayer({ id: USER_ENDPOINT_CIRCLE_LAYER_ID, type: "circle", source: USER_ENDPOINT_SOURCE_ID,
      paint: { "circle-radius": ["match", ["get", "role"], "destination", 12, 10],
        "circle-color": ["match", ["get", "role"], "destination", "#d63d32", "#2563eb"],
        "circle-stroke-color": "#fff", "circle-stroke-width": 3 } });
    map.addLayer({ id: USER_ENDPOINT_LABEL_LAYER_ID, type: "symbol", source: USER_ENDPOINT_SOURCE_ID,
      layout: { "text-field": ["match", ["get", "role"], "destination", "D", "S"], "text-size": 11, "text-font": ["Noto Sans Regular"], "text-allow-overlap": true, "text-ignore-placement": true },
      paint: { "text-color": "#fff" } });

    map.addSource(SOURCE_ID, {
      type: "geojson",
      data: { type: "FeatureCollection", features: visibleFeatures },
    });
    map.addLayer({
      id: CIRCLE_LAYER_ID,
      type: "circle",
      source: SOURCE_ID,
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 14, 7, 18, 11],
        "circle-color": [
          "match",
          ["get", "category"],
          "health", "#c25345",
          "food", "#e2a927",
          "hostel", "#7758a6",
          "office", "#397aa8",
          "library", "#208569",
          "#17663c",
        ],
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 3,
        "circle-opacity": 0.96,
      },
    });
    map.addLayer({
      id: SELECTED_LAYER_ID,
      type: "circle",
      source: SOURCE_ID,
      filter: ["==", ["get", "id"], ""],
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 14, 11, 18, 16],
        "circle-color": "rgba(255, 255, 255, 0)",
        "circle-stroke-color": "#e2b431",
        "circle-stroke-width": 4,
      },
    });
    map.addLayer({
      id: LABEL_LAYER_ID,
      type: "symbol",
      source: SOURCE_ID,
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
    });
    if (campusBoundary) {
      map.addLayer({ id: CAMPUS_LABEL_LAYER_ID, type: "symbol", source: CAMPUS_LABEL_SOURCE_ID, minzoom: 13,
        layout: { "text-field": ["get", "name"], "text-size": ["interpolate", ["linear"], ["zoom"], 13, 13, 17, 17], "text-font": ["Noto Sans Regular"], "text-letter-spacing": 0.04 },
        paint: { "text-color": "#0d442a", "text-halo-color": "rgba(255, 255, 252, 0.96)", "text-halo-width": 2 } });
    }
    map.moveLayer(USER_ENDPOINT_CIRCLE_LAYER_ID);
    map.moveLayer(USER_ENDPOINT_LABEL_LAYER_ID);

    for (const layerId of [CIRCLE_LAYER_ID, LABEL_LAYER_ID]) {
      map.on("click", layerId, (event) => {
        const selectedId = String(event.features?.[0]?.id || event.features?.[0]?.properties?.id || "");
        const selected = featureIndex.get(selectedId);
        if (selected) onSelect(selected);
      });
      map.on("mouseenter", layerId, () => {
        map.getCanvas().style.cursor = "pointer";
      });
      map.on("mouseleave", layerId, () => {
        map.getCanvas().style.cursor = "";
      });
    }

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

  function focus(feature) {
    selectedFeatureId = String(feature.properties.id);
    if (!loaded) {
      pendingFocus = feature;
      return;
    }
    map.setFilter(SELECTED_LAYER_ID, ["==", ["get", "id"], selectedFeatureId]);
    map.flyTo({ center: feature.geometry.coordinates, zoom: 18, duration: 900, essential: false });
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
    const source = loaded ? map.getSource(SOURCE_ID) : null;
    source?.setData({ type: "FeatureCollection", features: visibleFeatures });
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

  function showUserRoute(routeFeature, origin, destination) {
    if (!loaded || routeFeature.geometry.type !== "LineString") return;
    const coordinates = routeFeature.geometry.coordinates;
    map.getSource(USER_ROUTE_SOURCE_ID).setData({ type: "FeatureCollection", features: [routeFeature] });
    map.getSource(USER_ENDPOINT_SOURCE_ID).setData({ type: "FeatureCollection", features: [
      { type: "Feature", geometry: { type: "Point", coordinates: coordinates[0] }, properties: { role: "start", name: origin.properties.name } },
      { type: "Feature", geometry: { type: "Point", coordinates: coordinates.at(-1) }, properties: { role: "destination", name: destination.properties.name } },
    ] });
    const longitudes = coordinates.map(([longitude]) => longitude);
    const latitudes = coordinates.map(([, latitude]) => latitude);
    map.fitBounds([[Math.min(...longitudes), Math.min(...latitudes)], [Math.max(...longitudes), Math.max(...latitudes)]],
      { padding: routePadding(), maxZoom: 17.5, duration: 700, essential: false });
  }

  function clearUserRoute() {
    map.getSource(USER_ROUTE_SOURCE_ID)?.setData({ type: "FeatureCollection", features: [] });
    map.getSource(USER_ENDPOINT_SOURCE_ID)?.setData({ type: "FeatureCollection", features: [] });
  }

  return { focus, focusCampus, setVisibleFeatures, showRoute, showUserRoute, clearUserRoute, map };
}
