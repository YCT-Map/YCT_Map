const element = document.querySelector("#path-overview-map");
if (element) import("https://unpkg.com/maplibre-gl@6.10.0/dist/maplibre-gl.mjs").then((maplibregl) => {
  const data = JSON.parse(document.querySelector("#path-overview-data").textContent);
  const map = new maplibregl.Map({ container: element, style: "https://tiles.openfreemap.org/styles/liberty", center: [3.37424, 6.51857], zoom: 16 });
  map.on("load", () => {
    map.addSource("editor-graph", { type: "geojson", data });
    map.addLayer({
      id: "editor-graph-segments",
      type: "line",
      source: "editor-graph",
      filter: ["==", ["get", "kind"], "segment"],
      paint: {
        "line-color": ["match", ["get", "source"], "MANUAL", "#d66b21", "#17663c"],
        "line-width": ["interpolate", ["linear"], ["zoom"], 15, 3.5, 17, 5, 19, 6.5],
        "line-opacity": 0.85,
      },
    });
    map.addLayer({
      id: "editor-graph-segments-label",
      type: "symbol",
      source: "editor-graph",
      filter: ["==", ["get", "kind"], "segment"],
      minzoom: 16.5,
      layout: {
        "symbol-placement": "line-center",
        "text-field": ["to-string", ["coalesce", ["get", "label"], ""]],
        "text-font": ["Noto Sans Bold"],
        "text-size": ["interpolate", ["linear"], ["zoom"], 16.5, 9.5, 18, 11, 20, 12.5],
        "text-keep-upright": true,
        "text-allow-overlap": false,
        "text-padding": 4,
        "text-max-angle": 360,
      },
      paint: {
        "text-color": ["match", ["get", "source"], "MANUAL", "#8c3b0f", "#093a20"],
        "text-halo-color": "#ffffff",
        "text-halo-width": 2.25,
        "text-halo-blur": 0.5,
      },
    });
    map.addLayer({
      id: "editor-graph-nodes",
      type: "circle",
      source: "editor-graph",
      filter: ["==", ["get", "kind"], "node"],
      paint: {
        "circle-color": ["match", ["get", "source"], "MANUAL", "#d66b21", "#17663c"],
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 15, 4.5, 16.5, 6, 17.5, 8.5, 18.5, 10.5, 20, 12.5],
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 15, 1.25, 17.5, 1.75, 20, 2.25],
      },
    });
    map.addLayer({
      id: "editor-graph-nodes-label",
      type: "symbol",
      source: "editor-graph",
      filter: ["==", ["get", "kind"], "node"],
      minzoom: 16.5,
      layout: {
        "text-field": ["to-string", ["coalesce", ["get", "label"], ""]],
        "text-font": ["Noto Sans Bold"],
        "text-size": ["interpolate", ["linear"], ["zoom"], 16.5, 8, 17.5, 9.5, 18.5, 11, 20, 12.5],
        "text-anchor": "center",
        "text-allow-overlap": true,
        "text-ignore-placement": true,
      },
      paint: {
        "text-color": "#ffffff",
      },
    });
    const focusLatitude = Number(element.dataset.focusLatitude);
    const focusLongitude = Number(element.dataset.focusLongitude);
    const hasFocus = element.dataset.focusLatitude !== undefined && element.dataset.focusLongitude !== undefined
      && Number.isFinite(focusLatitude) && Number.isFinite(focusLongitude);
    const coordinates = data.features.flatMap((feature) => feature.geometry.type === "Point" ? [feature.geometry.coordinates] : feature.geometry.coordinates);
    if (hasFocus) {
      map.jumpTo({ center: [focusLongitude, focusLatitude], zoom: 18 });
      new maplibregl.Marker({ color: "#1565c0" }).setLngLat([focusLongitude, focusLatitude]).addTo(map);
    } else if (coordinates.length) {
      const bounds = coordinates.reduce((value, point) => value.extend(point), new maplibregl.LngLatBounds(coordinates[0], coordinates[0]));
      map.fitBounds(bounds, { padding: 50, maxZoom: 18, duration: 0 });
    }
    element.dataset.state = "ready"; map.resize();
    document.querySelector("#path-overview-status").textContent = `${data.features.length} active graph features displayed.`;
  });
}).catch(() => { element.dataset.state = "error"; document.querySelector("#path-overview-status").textContent = "The graph overview could not load; the editable lists remain available below."; });

