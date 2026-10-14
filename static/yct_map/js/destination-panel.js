export function createDestinationPanel(panel, { onDirections } = {}) {
  const name = panel.querySelector("#destination-name");
  const category = panel.querySelector("#destination-category");
  const description = panel.querySelector("#destination-description");
  const closeButton = panel.querySelector("#close-panel");
  const directionsButton = panel.querySelector("#destination-directions");
  const routingReason = panel.querySelector("#destination-routing-reason");
  const insideButton = panel.querySelector("#destination-inside");
  const insideList = panel.querySelector("#destination-inside-list");
  const internalGuidance = panel.querySelector("#destination-internal-guidance");
  const internalParent = panel.querySelector("#destination-internal-parent");
  const internalLocation = panel.querySelector("#destination-internal-location");
  const internalDirection = panel.querySelector("#destination-internal-direction");
  const verification = panel.querySelector("#destination-verification");
  const dataNotice = panel.querySelector("#destination-data-notice");
  const dataNoticeText = panel.querySelector("#destination-data-notice-text");
  let currentFeature = null;

  function show(feature) {
    const properties = feature.properties;
    currentFeature = feature;
    name.textContent = properties.name;
    category.textContent = properties.category_label || properties.internal_type_label || "Campus place";
    description.textContent = properties.description || "No additional description is available.";
    const verificationState = properties.verification_state || "UNVERIFIED";
    if (verification) {
      verification.hidden = verificationState === "FIELD_VERIFIED";
      verification.textContent = verificationState.replace("_", " ");
    }
    if (dataNotice && dataNoticeText) {
      dataNotice.hidden = verificationState === "FIELD_VERIFIED";
      dataNoticeText.textContent = verificationState === "DEMO"
        ? "Synthetic information for product demonstration only. This is not a verified real campus location."
        : "This campus information has not yet been field verified.";
    }
    const isInternal = properties.destination_type === "internal";
    if (internalGuidance) internalGuidance.hidden = !isInternal;
    if (isInternal) {
      internalParent.textContent = properties.parent?.name || "the parent building";
      internalLocation.textContent = [properties.floor?.label, properties.room_code, properties.wing_section]
        .filter(Boolean).join(" · ") || "Indoor location details are incomplete.";
      internalDirection.textContent = properties.direction_note || "No indoor direction note has been recorded.";
    }
    panel.hidden = false;
    panel.classList.add("is-visible");
    const routingAvailable = properties.routing_available === true;
    directionsButton.hidden = false;
    directionsButton.disabled = !routingAvailable;
    directionsButton.textContent = routingAvailable ? "Directions" : "Directions unavailable";
    directionsButton.setAttribute("aria-hidden", "false");
    if (routingReason) {
      routingReason.hidden = routingAvailable;
      routingReason.textContent = routingAvailable ? "" : (properties.routing_unavailable_reason || "Directions are not available for this destination yet.");
    }
    if (insideButton) insideButton.hidden = !properties.places_inside_count;
    if (insideList) { insideList.hidden = true; insideList.replaceChildren(); }
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
  insideButton?.addEventListener("click", async () => {
    if (!currentFeature) return;
    insideButton.disabled = true;
    try {
      const response = await fetch(`/api/locations/${currentFeature.properties.id}/internal-places/`);
      const payload = await response.json();
      for (const floor of payload.floors || []) {
        const heading = document.createElement("strong"); heading.textContent = floor.label; insideList.append(heading);
        const items = document.createElement("ul");
        for (const place of floor.places) { const item = document.createElement("li"); item.textContent = place.room_code ? `${place.name} (${place.room_code})` : place.name; items.append(item); }
        insideList.append(items);
      }
      insideList.hidden = false;
    } catch (_) { insideList.textContent = "Places inside could not be loaded."; insideList.hidden = false; }
    finally { insideButton.disabled = false; }
  });

  return { show, close };
}
