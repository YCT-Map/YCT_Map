export function createDestinationPanel(panel) {
  const name = panel.querySelector("#destination-name");
  const category = panel.querySelector("#destination-category");
  const description = panel.querySelector("#destination-description");
  const closeButton = panel.querySelector("#close-panel");

  function show(feature) {
    const properties = feature.properties;
    name.textContent = properties.name;
    category.textContent = properties.category_label;
    description.textContent = properties.description || "No additional description is available.";
    panel.hidden = false;
    panel.classList.add("is-visible");
  }

  function close({ restoreFocus = false } = {}) {
    panel.classList.remove("is-visible");
    panel.hidden = true;
    if (restoreFocus) {
      document.querySelector("#location-search")?.focus();
    }
  }

  closeButton.addEventListener("click", () => close({ restoreFocus: true }));

  return { show, close };
}
