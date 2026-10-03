import { createEntrancePointSelector } from "./entrance-point-selector.js?v=final-web-closeout-1";

const element = document.querySelector("#node-map");
if (element) import("https://unpkg.com/maplibre-gl@6.10.0/dist/maplibre-gl.mjs").then((maplibregl) => {
  const locked = document.querySelector(".editor-warning")?.textContent.includes("point is locked");
  const selector = createEntrancePointSelector({ element, latitudeInput: document.querySelector("#id_latitude"), longitudeInput: document.querySelector("#id_longitude"), statusElement: document.querySelector("#node-map-status"), maplibregl });
  if (locked) selector.map.off("click");
}).catch(() => { element.dataset.state = "error"; document.querySelector("#node-map-status").textContent = "The routing map could not load."; });
