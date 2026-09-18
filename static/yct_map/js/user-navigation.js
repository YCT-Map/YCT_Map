export function createUserNavigation({
  panel,
  features,
  routeUrl,
  onRoute,
  onClear,
  onBrowse,
  onCancel,
  onStateChange,
  requestRoute = fetch,
}) {
  const form = panel.querySelector("#user-route-form");
  const originSelect = panel.querySelector("#user-route-origin");
  const destinationName = panel.querySelector("#user-route-destination");
  const submitButton = panel.querySelector("#show-user-route");
  const error = panel.querySelector("#user-route-error");
  const result = panel.querySelector("#user-route-result");
  const formState = panel.querySelector("#user-route-form-state");
  let destination = null;

  function resetMessages() {
    error.hidden = true;
    result.hidden = true;
  }

  function begin(feature) {
    if (feature?.properties?.routing_available !== true) return false;
    destination = feature;
    destinationName.textContent = feature.properties.name;
    originSelect.replaceChildren();
    const placeholder = originSelect.ownerDocument.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Select starting point";
    placeholder.disabled = true;
    placeholder.selected = true;
    originSelect.append(placeholder);
    for (const candidate of features.filter(
      (item) => item.properties.routing_available === true && item.properties.id !== feature.properties.id,
    )) {
      const option = originSelect.ownerDocument.createElement("option");
      option.value = candidate.properties.id;
      option.textContent = candidate.properties.name;
      originSelect.append(option);
    }
    resetMessages();
    formState.hidden = false;
    panel.hidden = false;
    submitButton.disabled = true;
    if (originSelect.options.length === 1) {
      error.textContent = "No other DEMO starting point is connected to the walkable network.";
      error.hidden = false;
    }
    originSelect.focus();
    onStateChange?.("choosing-origin");
    return true;
  }

  async function calculate(event) {
    event.preventDefault();
    if (!destination || !originSelect.value) {
      error.textContent = "Choose a DEMO starting point.";
      error.hidden = false;
      return;
    }
    resetMessages();
    submitButton.disabled = true;
    submitButton.textContent = "Calculating…";
    const parameters = new URLSearchParams({ origin: originSelect.value, destination: destination.properties.id });
    try {
      const response = await requestRoute(`${routeUrl}?${parameters}`, { headers: { Accept: "application/json" } });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "No route is available.");
      const origin = features.find((item) => item.properties.id === originSelect.value);
      panel.querySelector("#user-route-from").textContent = payload.summary.origin.name;
      panel.querySelector("#user-route-to").textContent = payload.summary.destination.name;
      panel.querySelector("#user-route-distance").textContent = `${Math.round(payload.summary.distance_metres)} m`;
      panel.querySelector("#user-route-eta").textContent = payload.summary.eta_label;
      panel.querySelector("#user-route-data-notice").textContent = payload.summary.verification_state === "UNVERIFIED"
        ? "DEMO destinations with OSM-derived UNVERIFIED route geometry — not field-verified campus navigation."
        : "Synthetic DEMO route — not verified campus navigation.";
      formState.hidden = true;
      result.hidden = false;
      onRoute(payload.route, origin, destination);
      onStateChange?.("route-available");
    } catch (routeError) {
      error.textContent = routeError.message;
      error.hidden = false;
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Show route";
    }
  }

  function reset({ browse = false, notify = true } = {}) {
    destination = null;
    panel.hidden = true;
    resetMessages();
    onClear();
    if (notify) onStateChange?.("browsing");
    if (browse) onBrowse?.();
  }

  form.addEventListener("submit", calculate);
  originSelect.addEventListener("change", () => {
    submitButton.disabled = !originSelect.value;
  });
  panel.querySelector("#change-route-origin").addEventListener("click", () => {
    result.hidden = true;
    formState.hidden = false;
    originSelect.focus();
  });
  panel.querySelector("#change-route-destination").addEventListener("click", () => reset({ browse: true }));
  panel.querySelector("#clear-user-route").addEventListener("click", () => reset());
  panel.querySelector("#close-user-route").addEventListener("click", () => reset());
  panel.querySelector("#cancel-user-route").addEventListener("click", () => {
    const cancelledDestination = destination;
    reset({ notify: false });
    if (cancelledDestination) onCancel?.(cancelledDestination);
  });

  return { begin, reset };
}
