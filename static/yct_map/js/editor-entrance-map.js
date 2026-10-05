import { createEntrancePointSelector } from "./entrance-point-selector.js?v=system-closeout-2";
import { createEntranceRoutingConnection } from "./entrance-routing-connection.js?v=system-closeout-2";
import { bindLocationCapture } from "./location-capture.js?v=system-closeout-2";
import { loadSupportedLocationArea } from "./supported-area.js?v=system-closeout-2";

const element = document.querySelector("#entrance-map");
const latitudeInput = document.querySelector("#id_latitude");
const longitudeInput = document.querySelector("#id_longitude");
const statusElement = document.querySelector("#entrance-map-status");
const routingRoot = document.querySelector("#entrance-routing-connection");

async function start() {
  if (!element || !latitudeInput || !longitudeInput || !statusElement) return;
  let selector = null;
  let pendingPoint = null;
  bindLocationCapture({
    button: document.querySelector("#capture-entrance-location"),
    statusElement,
    supportedAreaPromise: loadSupportedLocationArea(element.dataset.campusBoundaryUrl),
    onPoint(point) {
      longitudeInput.value = point.lng.toFixed(6);
      latitudeInput.value = point.lat.toFixed(6);
      pendingPoint = point;
      if (selector) { selector.setPoint(point); pendingPoint = null; }
    },
  });
  try {
    const maplibregl = await import("https://unpkg.com/maplibre-gl@6.10.0/dist/maplibre-gl.mjs");
    selector = createEntrancePointSelector({ element, latitudeInput, longitudeInput, statusElement, maplibregl });
    if (pendingPoint) { selector.setPoint(pendingPoint); pendingPoint = null; }
    createEntranceRoutingConnection({ root: routingRoot, selector, maplibregl });
  } catch (error) {
    console.error("Entrance map selector failed to initialize", error);
    element.dataset.state = "error";
    statusElement.textContent = "The entrance map could not load. Current-location capture remains available; refresh to restore manual adjustment.";
    statusElement.setAttribute("role", "alert");
    createEntranceRoutingConnection({ root: routingRoot });
  }
}

start();
