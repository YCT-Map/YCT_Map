const SOURCE_ID = "demo-destinations";
const CIRCLE_LAYER_ID = "demo-destination-circles";
const SELECTED_LAYER_ID = "demo-destination-selected";
const LABEL_LAYER_ID = "demo-destination-labels";
const CAMPUS_SOURCE_ID = "yabatech-campus-orientation";
const CAMPUS_FILL_LAYER_ID = "yabatech-campus-fill";
const CAMPUS_LINE_LAYER_ID = "yabatech-campus-outline";
const CAMPUS_LABEL_LAYER_ID = "yabatech-campus-label";

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
  const [maplibregl, campusBoundary] = await Promise.all([
    import(config.moduleUrl),
    loadCampusBoundary(config.campusBoundaryUrl),
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
    new maplibregl.AttributionControl({ compact: true, customAttribution: "DEMO data" }),
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
      map.addLayer({
        id: CAMPUS_LABEL_LAYER_ID,
        type: "symbol",
        source: CAMPUS_SOURCE_ID,
        minzoom: 13,
        layout: {
          "text-field": ["get", "name"],
          "text-size": ["interpolate", ["linear"], ["zoom"], 13, 13, 17, 17],
          "text-font": ["Noto Sans Regular"],
          "text-letter-spacing": 0.04,
        },
        paint: {
          "text-color": "#0d442a",
          "text-halo-color": "rgba(255, 255, 252, 0.96)",
          "text-halo-width": 2,
        },
      });
    }

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

  return { focus, focusCampus, setVisibleFeatures, map };
}
