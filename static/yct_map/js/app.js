import { fetchLocations } from "./api.js?v=p2s3-osm-realism-4";
import { createDestinationPanel } from "./destination-panel.js?v=p2s3-osm-realism-4";
import { createMap } from "./map.js?v=p2s3-osm-realism-4";
import { createSearch } from "./search.js?v=p2s3-osm-realism-4";
import { createRouteInspector } from "./route-inspector.js?v=p2s3-osm-realism-4";
import { createUserNavigation } from "./user-navigation.js?v=p2s3-osm-realism-4";

const shell = document.querySelector(".map-shell");
const status = document.querySelector("#map-status");
const mapError = document.querySelector("#map-error");
let destinationPanel = null;
let navigationController = null;

const config = {
  locationsUrl: shell.dataset.locationsUrl,
  styleUrl: shell.dataset.mapStyleUrl,
  moduleUrl: shell.dataset.maplibreModuleUrl,
  campusBoundaryUrl: shell.dataset.campusBoundaryUrl,
  debugNetworkUrl: shell.dataset.debugNetworkUrl,
  debugRouteAnchorsUrl: shell.dataset.debugRouteAnchorsUrl,
  debugRouteUrl: shell.dataset.debugRouteUrl,
  routeUrl: shell.dataset.routeUrl,
  centre: [Number(shell.dataset.centreLongitude), Number(shell.dataset.centreLatitude)],
};

let mapController = null;

function setInterfaceState(state) {
  shell.dataset.interfaceState = state;
}

function setStatus(message, state = "ready") {
  status.querySelector("span:last-child").textContent = message;
  status.dataset.state = state;
}

function selectDestination(feature) {
  navigationController.reset({ notify: false });
  destinationPanel.show(feature);
  setInterfaceState("destination-selected");
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

    navigationController = createUserNavigation({
      panel: document.querySelector("#user-route-panel"),
      features,
      routeUrl: config.routeUrl,
      onRoute: (route, origin, destination) => mapController?.showUserRoute(route, origin, destination),
      onClear: () => mapController?.clearUserRoute(),
      onBrowse: () => document.querySelector("#location-search")?.focus(),
      onStateChange: setInterfaceState,
      onCancel: (feature) => {
        destinationPanel.show(feature);
        setInterfaceState("destination-selected");
      },
    });

    destinationPanel = createDestinationPanel(document.querySelector("#destination-panel"), {
      onDirections: (feature) => {
        if (navigationController.begin(feature)) {
          destinationPanel.close();
        }
      },
    });

    createSearch({
      features,
      onSelect: selectDestination,
      onFilter: (matches) => mapController?.setVisibleFeatures(matches),
    });
    setInterfaceState("browsing");

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
      await createRouteInspector({
        element: document.querySelector("#route-inspector"),
        anchorsUrl: config.debugRouteAnchorsUrl,
        routeUrl: config.debugRouteUrl,
        onRoute: (route) => mapController.showRoute(route),
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
