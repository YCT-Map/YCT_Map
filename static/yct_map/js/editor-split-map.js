import { createEntrancePointSelector } from "./entrance-point-selector.js?v=system-closeout-4";
const element = document.querySelector("#split-map");
if (element) import("https://unpkg.com/maplibre-gl@6.10.0/dist/maplibre-gl.mjs").then((maplibregl) => {
  const geometry = JSON.parse(document.querySelector("#split-geometry").textContent);
  const selector = createEntrancePointSelector({ element, latitudeInput: document.querySelector("#id_latitude"), longitudeInput: document.querySelector("#id_longitude"), statusElement: document.querySelector("#split-map-status"), maplibregl });
  selector.map.on("load", () => { selector.map.addSource("segment-to-split", { type: "geojson", data: { type: "Feature", properties: {}, geometry } }); selector.map.addLayer({ id: "segment-to-split", type: "line", source: "segment-to-split", paint: { "line-color": "#e44832", "line-width": 7 } }); const bounds = geometry.coordinates.reduce((b, p) => b.extend(p), new maplibregl.LngLatBounds(geometry.coordinates[0], geometry.coordinates[0])); selector.map.fitBounds(bounds, { padding: 60, maxZoom: 19 }); });
});
