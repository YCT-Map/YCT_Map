import { fetchLocations } from "./api.js?v=navigation-orientation-1";
import { createContributions } from "./contributions.js?v=navigation-orientation-1";
import { createDestinationPanel } from "./destination-panel.js?v=navigation-orientation-1";
import { createMap } from "./map.js?v=navigation-orientation-1";
import { createSearch } from "./search.js?v=navigation-orientation-1";
import { createRouteInspector } from "./route-inspector.js?v=navigation-orientation-1";
import { createUserLocation } from "./user-location.js?v=navigation-orientation-1";
import { createUserNavigation } from "./user-navigation.js?v=navigation-orientation-1";
import { createDisclosureMenu } from "./disclosure-menu.js?v=navigation-orientation-1";

const shell = document.querySelector(".map-shell");
const status = document.querySelector("#map-status");
const mapError = document.querySelector("#map-error");
let destinationPanel = null;
let navigationController = null;

const config = {
  locationsUrl: shell.dataset.locationsUrl,
  searchUrl: shell.dataset.searchUrl,
  styleUrl: shell.dataset.mapStyleUrl,
  moduleUrl: shell.dataset.maplibreModuleUrl,
  campusBoundaryUrl: shell.dataset.campusBoundaryUrl,
  debugNetworkUrl: shell.dataset.debugNetworkUrl,
  debugRouteAnchorsUrl: shell.dataset.debugRouteAnchorsUrl,
  debugRouteUrl: shell.dataset.debugRouteUrl,
  routeUrl: shell.dataset.routeUrl,
  liveRouteUrl: shell.dataset.liveRouteUrl,
  contributionUrl: shell.dataset.contributionUrl,
  centre: [Number(shell.dataset.centreLongitude), Number(shell.dataset.centreLatitude)],
};

let mapController = null;
let userLocationController = null;
createDisclosureMenu({ element: document.querySelector(".team-menu") });

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
      setStatus("No campus destinations are loaded yet.", "warning");
    } else {
      setStatus(`${features.length} campus destinations ready`, "ready");
    }

    navigationController = createUserNavigation({
      panel: document.querySelector("#user-route-panel"),
      features,
      routeUrl: config.routeUrl,
      liveRouteUrl: config.liveRouteUrl,
      onRoute: (route, origin, destination, options) => mapController?.showUserRoute(route, origin, destination, options),
      onClear: () => mapController?.clearUserRoute(),
      onRouteStale: (stale) => mapController?.setUserRouteStale(stale),
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

    const contributionController = createContributions({
      panel: document.querySelector("#contribution-panel"),
      openButton: document.querySelector("#open-contribution"),
      features,
      endpoint: config.contributionUrl,
      onOpen: () => {
        navigationController.suspend();
        destinationPanel.close();
        setInterfaceState("contributing");
      },
      onClose: () => setInterfaceState(navigationController.resume() ? "route-available" : "browsing"),
      onPickPoint: (callback) => mapController?.pickContributionPoint(callback),
      onClearPoint: () => mapController?.clearContributionPoint(),
    });

    createSearch({
      features,
      searchUrl: config.searchUrl,
      onSelect: selectDestination,
      onFilter: (matches) => mapController?.setVisibleFeatures(matches),
    });
    userLocationController = createUserLocation({
      element: document.querySelector("#user-location-controls"),
      onPosition: (position, options) => {
        mapController?.showUserLocation(position, options);
        navigationController?.updateLivePosition(position);
      },
      onClear: () => {
        mapController?.clearUserLocation();
        navigationController?.clearLivePosition();
      },
      onRecenter: () => mapController?.recenterUserLocation(),
      onHeading: (heading) => mapController?.updateUserHeading(heading),
      onFollowDirection: () => mapController?.enableFollowDirection() || "north-up",
      onNorthUp: () => mapController?.northUp(),
    });
    setInterfaceState("browsing");

    try {
      mapController = await createMap({
        container: "map",
        config,
        features,
        onSelect: selectDestination,
        onFollowStateChange: (state) => userLocationController?.setFollowState(state),
        onReady: () => setStatus(`${features.length} campus destinations · YabaTech area`, "ready"),
        onError: () => {
          mapError.hidden = false;
          setStatus("Campus destinations ready · map unavailable", "warning");
        },
      });
      const existingPosition = userLocationController.getAcceptedPosition();
      if (existingPosition) mapController.showUserLocation(existingPosition, { focus: true });
      contributionController.setMapAvailable(true);
      await createRouteInspector({
        element: document.querySelector("#route-inspector"),
        anchorsUrl: config.debugRouteAnchorsUrl,
        routeUrl: config.debugRouteUrl,
        onRoute: (route) => mapController.showRoute(route),
      });
    } catch (error) {
      console.error("Map initialization failed", error);
      mapError.hidden = false;
      setStatus("Campus destinations ready · map unavailable", "warning");
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
