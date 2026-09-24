const element = document.querySelector("#segment-map");
if (element) import("https://unpkg.com/maplibre-gl@6.10.0/dist/maplibre-gl.mjs").then((maplibregl) => {
  const nodes = JSON.parse(document.querySelector("#routing-nodes").textContent);
  const byId = new Map(nodes.map((node) => [String(node.id), [Number(node.longitude), Number(node.latitude)]]));
  const start = document.querySelector("#id_start_node");
  const end = document.querySelector("#id_end_node");
  const input = document.querySelector("#id_geometry");
  const status = document.querySelector("#segment-map-status");
  let geometry;
  try { geometry = JSON.parse(input.value); } catch { geometry = { type: "LineString", coordinates: [] }; }
  const map = new maplibregl.Map({ container: element, style: "https://tiles.openfreemap.org/styles/liberty", center: [3.37424, 6.51857], zoom: 16 });
  function endpoints() { return [byId.get(start.value), byId.get(end.value)]; }
  function reset() {
    const [a, b] = endpoints(); geometry = { type: "LineString", coordinates: a && b ? [a, b] : [] }; update();
  }
  function update() {
    input.value = JSON.stringify(geometry);
    if (map.getSource("edited-segment")) map.getSource("edited-segment").setData({ type: "Feature", geometry, properties: {} });
    status.textContent = geometry.coordinates.length >= 2 ? `${geometry.coordinates.length} geometry points. Click to add a bend before the destination.` : "Choose two different active endpoint nodes.";
  }
  map.on("load", () => { map.addSource("edited-segment", { type: "geojson", data: { type: "Feature", geometry, properties: {} } }); map.addLayer({ id: "edited-segment", type: "line", source: "edited-segment", paint: { "line-color": "#e44832", "line-width": 6 } }); element.dataset.state = "ready"; update(); map.resize(); });
  map.on("click", ({ lngLat }) => { const [a, b] = endpoints(); if (!a || !b) return; if (geometry.coordinates.length < 2) reset(); geometry.coordinates.splice(-1, 0, [Number(lngLat.lng.toFixed(6)), Number(lngLat.lat.toFixed(6))]); update(); });
  start.addEventListener("change", reset); end.addEventListener("change", reset); document.querySelector("#reset-segment-geometry").addEventListener("click", reset);
}).catch(() => { element.dataset.state = "error"; document.querySelector("#segment-map-status").textContent = "The path map could not load."; });
