const DEFAULT_CENTRE = [3.37424, 6.51857];

function finiteCoordinate(value) {
  if (value === "" || value === null || value === undefined) return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

export function createEntrancePointSelector({
  element, latitudeInput, longitudeInput, statusElement, maplibregl,
  styleUrl = "https://tiles.openfreemap.org/styles/liberty",
}) {
  const savedLatitude = finiteCoordinate(element.dataset.latitude);
  const savedLongitude = finiteCoordinate(element.dataset.longitude);
  const hasSavedPoint = savedLatitude !== null && savedLongitude !== null;
  const initial = hasSavedPoint ? [savedLongitude, savedLatitude] : DEFAULT_CENTRE;
  const map = new maplibregl.Map({ container: element, style: styleUrl, center: initial, zoom: 16 });
  let marker = null;
  let pointSelectionEnabled = true;

  function setPoint({ lng, lat }) {
    longitudeInput.value = Number(lng).toFixed(6);
    latitudeInput.value = Number(lat).toFixed(6);
    marker?.remove();
    marker = new maplibregl.Marker({ color: "#17663c" }).setLngLat([Number(lng), Number(lat)]).addTo(map);
    element.dataset.state = "selected";
    statusElement.textContent = "Entrance point selected. Click or tap elsewhere on the map to reposition it.";
    if (typeof element.dispatchEvent === "function" && typeof CustomEvent === "function") {
      element.dispatchEvent(new CustomEvent("entrancepointchange", { detail: { lng: Number(lng), lat: Number(lat) } }));
    }
  }

  if (hasSavedPoint) setPoint({ lng: savedLongitude, lat: savedLatitude });
  map.on("click", ({ lngLat }) => {
    if (pointSelectionEnabled) setPoint(lngLat);
  });
  map.on("load", () => {
    element.dataset.state = marker ? "selected" : "ready";
    map.resize();
  });
  if (globalThis.requestAnimationFrame) globalThis.requestAnimationFrame(() => map.resize());

  return {
    map,
    setPoint,
    getMarker: () => marker,
    setPointSelectionEnabled: (enabled) => { pointSelectionEnabled = Boolean(enabled); },
  };
}
