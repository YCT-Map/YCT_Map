function searchableText(feature) {
  const aliases = feature.properties.aliases || [];
  return [feature.properties.name, ...aliases].join(" ").toLocaleLowerCase();
}

export function createSearch({ features, onSelect, onFilter, searchUrl = "", requestSearch = fetch }) {
  const form = document.querySelector("#search-form");
  const input = document.querySelector("#location-search");
  const clearButton = document.querySelector("#clear-search");
  const results = document.querySelector("#search-results");
  const list = document.querySelector("#results-list");
  const summary = document.querySelector("#results-summary");
  const count = document.querySelector("#results-count");
  const categoryButtons = [...document.querySelectorAll("[data-category]")];
  let activeCategory = "";
  let remoteResults = [];
  let sequence = 0;

  const localFeatures = () => {
    const query = input.value.trim().toLocaleLowerCase();
    return features.filter((feature) => (!query || searchableText(feature).includes(query)) &&
      (!activeCategory || feature.properties.category === activeCategory));
  };
  const internalFeatures = () => remoteResults.map((item) => {
    const parent = features.find((feature) => feature.properties.id === item.parent?.id);
    return {type: "Feature", id: item.id, geometry: parent?.geometry || null, properties: {
      ...item, category_label: item.internal_type_label,
      description: [item.parent?.name && `Inside ${item.parent.name}`, item.floor?.label,
        item.room_code, item.direction_note].filter(Boolean).join(" · "),
    }};
  });

  function closeResults() { results.hidden = true; input.setAttribute("aria-expanded", "false"); }
  function render({reveal = true} = {}) {
    const local = localFeatures();
    const matches = [...local, ...internalFeatures()];
    list.replaceChildren();
    clearButton.hidden = input.value.length === 0;
    if (!matches.length) {
      const empty = document.createElement("div");
      empty.className = "results-empty";
      empty.innerHTML = "<strong>No destinations found.</strong><span>Try another name, room code, or category.</span>";
      list.append(empty);
      summary.textContent = "No matching destinations";
    } else {
      for (const feature of matches) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "result-item";
        button.innerHTML = '<span class="result-marker" aria-hidden="true"></span><span class="result-copy"><strong></strong><small></small></span><span class="result-arrow" aria-hidden="true">→</span>';
        button.querySelector("strong").textContent = feature.properties.name;
        button.querySelector("small").textContent = feature.properties.destination_type === "internal"
          ? feature.properties.subtitle : `${feature.properties.category_label} · ${feature.properties.verification_label || "Campus place"}`;
        button.addEventListener("click", () => { onSelect(feature); closeResults(); });
        list.append(button);
      }
      summary.textContent = input.value.trim() ? "Search results" : "Campus destinations";
    }
    count.textContent = String(matches.length);
    input.setAttribute("aria-expanded", String(reveal));
    results.hidden = !reveal;
    onFilter(local);
    return matches;
  }

  async function updateSearch() {
    const current = ++sequence;
    const query = input.value.trim();
    remoteResults = [];
    render();
    if (!searchUrl || !query) return;
    try {
      const response = await requestSearch(`${searchUrl}?q=${encodeURIComponent(query)}`, {headers: {Accept: "application/json"}});
      const payload = await response.json();
      if (response.ok && current === sequence) {
        remoteResults = (payload.results || []).filter((item) => item.destination_type === "internal");
        render();
      }
    } catch (_) { /* Outdoor search remains usable when this endpoint is unavailable. */ }
  }
  input.addEventListener("input", updateSearch);
  input.addEventListener("focus", () => render());
  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape") { closeResults(); input.blur(); }
    if (event.key === "ArrowDown" && !results.hidden) { event.preventDefault(); list.querySelector("button")?.focus(); }
  });
  form.addEventListener("submit", (event) => { event.preventDefault(); const matches = render(); if (matches.length === 1) { onSelect(matches[0]); closeResults(); } });
  clearButton.addEventListener("click", () => { input.value = ""; remoteResults = []; input.focus(); render(); });
  for (const button of categoryButtons) button.addEventListener("click", () => {
    activeCategory = button.dataset.category;
    for (const candidate of categoryButtons) { const active = candidate === button; candidate.classList.toggle("is-active", active); candidate.setAttribute("aria-pressed", String(active)); }
    render({reveal: true});
  });
  document.addEventListener("pointerdown", (event) => { if (!event.target.closest(".discovery")) closeResults(); });
  return {render, closeResults};
}
