const SOURCE_ID = "demo-destinations";
const CIRCLE_LAYER_ID = "demo-destination-circles";
const LABEL_LAYER_ID = "demo-destination-labels";

export async function createMap({ container, config, features, onSelect, onReady, onError }) {
  const maplibregl = await import(config.moduleUrl);
  const featureIndex = new Map(features.map((feature) => [String(feature.id), feature]));
  let visibleFeatures = features;
  let loaded = false;
  let pendingFocus = null;

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
  map.addControl(
    new maplibregl.AttributionControl({ compact: true, customAttribution: "DEMO data" }),
    "bottom-right",
  );

  map.on("load", () => {
    loaded = true;
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
    }
    onReady();
  });

  map.on("error", (event) => {
    if (!loaded) {
      onError(event?.error || new Error("Map style failed to load."));
    }
  });

  function focus(feature) {
    if (!loaded) {
      pendingFocus = feature;
      return;
    }
    map.flyTo({ center: feature.geometry.coordinates, zoom: 18, duration: 900, essential: false });
  }

  function setVisibleFeatures(nextFeatures) {
    visibleFeatures = nextFeatures;
    const source = loaded ? map.getSource(SOURCE_ID) : null;
    source?.setData({ type: "FeatureCollection", features: visibleFeatures });
  }

  return { focus, setVisibleFeatures, map };
}
