import { createEntrancePointSelector } from "./entrance-point-selector.js?v=system-closeout-3";
import { bindLocationCapture } from "./location-capture.js?v=system-closeout-3";
import { loadSupportedLocationArea } from "./supported-area.js?v=system-closeout-3";

const element = typeof document === "undefined" ? null : document.querySelector("#place-map");
if (element) {
  const latitudeInput = document.querySelector("#id_representative_latitude");
  const longitudeInput = document.querySelector("#id_representative_longitude");
  const statusElement = document.querySelector("#place-location-status");
  const button = document.querySelector("#capture-current-location");
  const supportedAreaPromise = loadSupportedLocationArea(element.dataset.campusBoundaryUrl);
  let selector = null;
  let pendingPoint = null;

  bindLocationCapture({
    button,
    statusElement,
    supportedAreaPromise,
    onPoint(point) {
      longitudeInput.value = point.lng.toFixed(6);
      latitudeInput.value = point.lat.toFixed(6);
      pendingPoint = point;
      if (selector) { selector.setPoint(point); pendingPoint = null; }
    },
  });

  import("https://unpkg.com/maplibre-gl@6.10.0/dist/maplibre-gl.mjs").then((maplibregl) => {
    selector = createEntrancePointSelector({ element, latitudeInput, longitudeInput, statusElement, maplibregl });
    if (pendingPoint) { selector.setPoint(pendingPoint); pendingPoint = null; }
  }).catch(() => {
    element.dataset.state = "error";
    statusElement.textContent = "The map could not load. Current-location capture remains available; refresh to restore manual adjustment.";
  });
}
