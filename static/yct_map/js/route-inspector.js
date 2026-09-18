export async function createRouteInspector({ element, anchorsUrl, routeUrl, onRoute }) {
  if (!element || !anchorsUrl || !routeUrl) return;
  const response = await fetch(anchorsUrl, { headers: { Accept: "application/json" } });
  if (!response.ok) return;
  const { anchors } = await response.json();
  if (anchors.length < 2) return;

  const origin = element.querySelector("#route-origin");
  const destination = element.querySelector("#route-destination");
  for (const anchor of anchors) {
    for (const select of [origin, destination]) {
      const option = document.createElement("option");
      option.value = anchor.location_id;
      option.textContent = anchor.location_name;
      select.append(option);
    }
  }
  destination.selectedIndex = 1;
  element.hidden = false;

  element.querySelector("form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const result = element.querySelector("#route-result");
    const error = element.querySelector("#route-error");
    error.hidden = true;
    result.hidden = true;
    if (origin.value === destination.value) {
      error.textContent = "Choose two different DEMO destinations for visual inspection.";
      error.hidden = false;
      return;
    }
    const parameters = new URLSearchParams({ origin: origin.value, destination: destination.value });
    const routeResponse = await fetch(`${routeUrl}?${parameters}`, { headers: { Accept: "application/json" } });
    const payload = await routeResponse.json();
    if (!routeResponse.ok) {
      error.textContent = payload.error || "No DEMO route could be calculated.";
      error.hidden = false;
      return;
    }
    const properties = payload.route.properties;
    element.querySelector("#route-distance").textContent = `${Math.round(properties.distance_metres)} m`;
    element.querySelector("#route-eta").textContent = properties.eta_label;
    result.hidden = false;
    onRoute(payload.route);
  });
}
