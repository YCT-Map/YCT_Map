const element = document.querySelector("#path-overview-map");
if (element) import("https://unpkg.com/maplibre-gl@6.10.0/dist/maplibre-gl.mjs").then((maplibregl) => {
  const data = JSON.parse(document.querySelector("#path-overview-data").textContent);
  const map = new maplibregl.Map({ container: element, style: "https://tiles.openfreemap.org/styles/liberty", center: [3.37424, 6.51857], zoom: 16 });
  map.on("load", () => {
    map.addSource("editor-graph", { type: "geojson", data });
    map.addLayer({ id: "editor-graph-segments", type: "line", source: "editor-graph", filter: ["==", ["get", "kind"], "segment"], paint: { "line-color": ["match", ["get", "source"], "MANUAL", "#d66b21", "#17663c"], "line-width": 4, "line-opacity": .82 } });
    map.addLayer({ id: "editor-graph-nodes", type: "circle", source: "editor-graph", filter: ["==", ["get", "kind"], "node"], paint: { "circle-color": ["match", ["get", "source"], "MANUAL", "#d66b21", "#17663c"], "circle-radius": 5, "circle-stroke-color": "#fff", "circle-stroke-width": 1.5 } });
    const coordinates = data.features.flatMap((feature) => feature.geometry.type === "Point" ? [feature.geometry.coordinates] : feature.geometry.coordinates);
    if (coordinates.length) {
      const bounds = coordinates.reduce((value, point) => value.extend(point), new maplibregl.LngLatBounds(coordinates[0], coordinates[0]));
      map.fitBounds(bounds, { padding: 50, maxZoom: 18, duration: 0 });
    }
    element.dataset.state = "ready"; map.resize();
    document.querySelector("#path-overview-status").textContent = `${data.features.length} active graph features displayed.`;
  });
}).catch(() => { element.dataset.state = "error"; document.querySelector("#path-overview-status").textContent = "The graph overview could not load; the editable lists remain available below."; });
