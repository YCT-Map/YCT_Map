import { createEntrancePointSelector } from "./entrance-point-selector.js";

export function accuracyQuality(accuracy) {
  if (!Number.isFinite(accuracy) || accuracy > 100) return "rejected";
  if (accuracy <= 30) return "good";
  if (accuracy <= 60) return "fair";
  return "low";
}

function geolocationErrorMessage(error) {
  if (error?.code === 1) return "Location permission was denied. Allow location access or pick the point manually.";
  if (error?.code === 2) return "Your current location is unavailable. Try again or pick the point manually.";
  if (error?.code === 3) return "The location request timed out. Try again or pick the point manually.";
  return "The browser could not obtain your location. Try again or pick the point manually.";
}

export function createPlaceCaptureController({ button, statusElement, navigatorObject = globalThis.navigator, onPoint }) {
  function capture() {
    statusElement.textContent = "Requesting location permission…";
    button.disabled = true;
    button.textContent = "Requesting location…";
    if (!navigatorObject?.geolocation) {
      statusElement.textContent = "Current location is unavailable in this browser. Pick the point manually.";
      button.disabled = false; button.textContent = "Retry current location"; return;
    }
    navigatorObject.geolocation.getCurrentPosition(({ coords }) => {
      button.disabled = false; button.textContent = "Retry current location";
      const quality = accuracyQuality(coords.accuracy);
      if (quality === "rejected") {
        statusElement.textContent = `Accuracy is about ${Math.round(coords.accuracy)} m, which is too poor to capture safely. Retry or pick manually.`;
        return;
      }
      onPoint({ lng: coords.longitude, lat: coords.latitude });
      statusElement.textContent = `${quality[0].toUpperCase()}${quality.slice(1)} accuracy (about ${Math.round(coords.accuracy)} m). Provisional UNVERIFIED point selected; adjust it on the map if needed.`;
    }, (error) => {
      button.disabled = false; button.textContent = "Retry current location";
      statusElement.textContent = geolocationErrorMessage(error);
    }, { enableHighAccuracy: true, maximumAge: 0, timeout: 12000 });
  }
  button.addEventListener("click", capture);
  return { capture };
}

const element = typeof document === "undefined" ? null : document.querySelector("#place-map");
if (element) {
  const latitudeInput = document.querySelector("#id_representative_latitude");
  const longitudeInput = document.querySelector("#id_representative_longitude");
  const statusElement = document.querySelector("#place-location-status");
  let selector = null;
  let pendingPoint = null;
  createPlaceCaptureController({
    button: document.querySelector("#capture-current-location"), statusElement,
    onPoint(point) { pendingPoint = point; if (selector) { selector.setPoint(point); pendingPoint = null; } },
  });
  import("https://unpkg.com/maplibre-gl@6.10.0/dist/maplibre-gl.mjs").then((maplibregl) => {
    selector = createEntrancePointSelector({ element, latitudeInput, longitudeInput, statusElement, maplibregl });
    if (pendingPoint) { selector.setPoint(pendingPoint); pendingPoint = null; }
  }).catch(() => {
    element.dataset.state = "error";
    statusElement.textContent = "The map could not load. Current-location capture can still report a result; retry the map by refreshing.";
  });
}
