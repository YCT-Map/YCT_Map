function searchableText(feature) {
  const aliases = feature.properties.aliases || [];
  return [feature.properties.name, ...aliases].join(" ").toLocaleLowerCase();
}

export function createSearch({ features, onSelect, onFilter }) {
  const form = document.querySelector("#search-form");
  const input = document.querySelector("#location-search");
  const clearButton = document.querySelector("#clear-search");
  const results = document.querySelector("#search-results");
  const list = document.querySelector("#results-list");
  const summary = document.querySelector("#results-summary");
  const count = document.querySelector("#results-count");
  const categoryButtons = [...document.querySelectorAll("[data-category]")];
  let activeCategory = "";

  const filterFeatures = () => {
    const query = input.value.trim().toLocaleLowerCase();
    return features.filter((feature) => {
      const matchesQuery = !query || searchableText(feature).includes(query);
      const matchesCategory = !activeCategory || feature.properties.category === activeCategory;
      return matchesQuery && matchesCategory;
    });
  };

  const render = ({ reveal = true } = {}) => {
    const matches = filterFeatures();
    list.replaceChildren();
    clearButton.hidden = input.value.length === 0;

    if (matches.length === 0) {
      const empty = document.createElement("div");
      empty.className = "results-empty";
      empty.innerHTML = "<strong>No demo destinations found.</strong><span>Try another name or category.</span>";
      list.append(empty);
      summary.textContent = "No matching destinations";
    } else {
      for (const feature of matches) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "result-item";
        button.innerHTML = `
          <span class="result-marker result-marker--${feature.properties.category}" aria-hidden="true"></span>
          <span class="result-copy">
            <strong></strong>
            <small></small>
          </span>
          <span class="result-arrow" aria-hidden="true">→</span>
        `;
        button.querySelector("strong").textContent = feature.properties.name;
        button.querySelector("small").textContent = `${feature.properties.category_label} · DEMO`;
        button.addEventListener("click", () => {
          onSelect(feature);
          closeResults();
        });
        list.append(button);
      }
      summary.textContent = input.value.trim() ? "Search results" : "Demonstration destinations";
    }

    count.textContent = String(matches.length);
    input.setAttribute("aria-expanded", String(reveal));
    results.hidden = !reveal;
    onFilter(matches);
    return matches;
  };

  const closeResults = () => {
    results.hidden = true;
    input.setAttribute("aria-expanded", "false");
  };

  input.addEventListener("input", () => render());
  input.addEventListener("focus", () => render());
  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeResults();
      input.blur();
    }
    if (event.key === "ArrowDown" && !results.hidden) {
      event.preventDefault();
      list.querySelector("button")?.focus();
    }
  });

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const matches = render();
    if (matches.length === 1) {
      onSelect(matches[0]);
      closeResults();
    }
  });

  clearButton.addEventListener("click", () => {
    input.value = "";
    input.focus();
    render();
  });

  for (const button of categoryButtons) {
    button.addEventListener("click", () => {
      activeCategory = button.dataset.category;
      for (const candidate of categoryButtons) {
        const isActive = candidate === button;
        candidate.classList.toggle("is-active", isActive);
        candidate.setAttribute("aria-pressed", String(isActive));
      }
      render({ reveal: true });
    });
  }

  document.addEventListener("pointerdown", (event) => {
    if (!event.target.closest(".discovery")) {
      closeResults();
    }
  });

  return { render, closeResults };
}
