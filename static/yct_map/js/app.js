import { fetchLocations } from "./api.js";
import { createDestinationPanel } from "./destination-panel.js";
import { createMap } from "./map.js";
import { createSearch } from "./search.js";

const shell = document.querySelector(".map-shell");
const status = document.querySelector("#map-status");
const mapError = document.querySelector("#map-error");
const panel = createDestinationPanel(document.querySelector("#destination-panel"));

const config = {
  locationsUrl: shell.dataset.locationsUrl,
  styleUrl: shell.dataset.mapStyleUrl,
  moduleUrl: shell.dataset.maplibreModuleUrl,
  campusBoundaryUrl: shell.dataset.campusBoundaryUrl,
  centre: [Number(shell.dataset.centreLongitude), Number(shell.dataset.centreLatitude)],
};

let mapController = null;

function setStatus(message, state = "ready") {
  status.querySelector("span:last-child").textContent = message;
  status.dataset.state = state;
}

function selectDestination(feature) {
  panel.show(feature);
  mapController?.focus(feature);
}

async function start() {
  try {
    const collection = await fetchLocations(config.locationsUrl);
    const features = collection.features;

    if (features.length === 0) {
      setStatus("No demonstration destinations are loaded yet.", "warning");
    } else {
      setStatus(`${features.length} demo destinations ready`, "ready");
    }

    createSearch({
      features,
      onSelect: selectDestination,
      onFilter: (matches) => mapController?.setVisibleFeatures(matches),
    });

    try {
      mapController = await createMap({
        container: "map",
        config,
        features,
        onSelect: selectDestination,
        onReady: () => setStatus(`${features.length} demo destinations · YabaTech area`, "ready"),
        onError: () => {
          mapError.hidden = false;
          setStatus("Demo destinations ready · map unavailable", "warning");
        },
      });
    } catch (error) {
      console.error("Map initialization failed", error);
      mapError.hidden = false;
      setStatus("Demo destinations ready · map unavailable", "warning");
    }
  } catch (error) {
    console.error("YCT Map could not load destination data", error);
    setStatus("Destination data could not load. Please refresh and try again.", "error");
    mapError.hidden = false;
    mapError.querySelector("strong").textContent = "Destination data could not load.";
    mapError.querySelector("span").textContent = "Please refresh the page and try again.";
  }
}

start();
