export function createDestinationPanel(panel, { onDirections } = {}) {
  const name = panel.querySelector("#destination-name");
  const category = panel.querySelector("#destination-category");
  const description = panel.querySelector("#destination-description");
  const closeButton = panel.querySelector("#close-panel");
  const directionsButton = panel.querySelector("#destination-directions");
  let currentFeature = null;

  function show(feature) {
    const properties = feature.properties;
    currentFeature = feature;
    name.textContent = properties.name;
    category.textContent = properties.category_label;
    description.textContent = properties.description || "No additional description is available.";
    panel.hidden = false;
    panel.classList.add("is-visible");
    const routingAvailable = properties.routing_available === true;
    directionsButton.hidden = !routingAvailable;
    directionsButton.disabled = !routingAvailable;
    directionsButton.setAttribute("aria-hidden", String(!routingAvailable));
  }

  function close({ restoreFocus = false } = {}) {
    panel.classList.remove("is-visible");
    panel.hidden = true;
    if (restoreFocus) {
      document.querySelector("#location-search")?.focus();
    }
  }

  closeButton.addEventListener("click", () => close({ restoreFocus: true }));
  directionsButton.addEventListener("click", () => currentFeature && onDirections?.(currentFeature));

  return { show, close };
}
