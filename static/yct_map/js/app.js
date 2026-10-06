import { fetchLocations } from "./api.js?v=system-closeout-3";
import { createContributions } from "./contributions.js?v=system-closeout-3";
import { createDestinationPanel } from "./destination-panel.js?v=system-closeout-3";
import { createMap } from "./map.js?v=system-closeout-3";
import { createSearch } from "./search.js?v=system-closeout-3";
import { createRouteInspector } from "./route-inspector.js?v=system-closeout-3";
import { createUserLocation } from "./user-location.js?v=system-closeout-3";
import { createUserNavigation } from "./user-navigation.js?v=system-closeout-3";
import { createDisclosureMenu } from "./disclosure-menu.js?v=system-closeout-3";
import { loadSupportedLocationArea } from "./supported-area.js?v=system-closeout-3";

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
  headingDiagnosticsAvailable: shell.dataset.headingDiagnostics === "true",
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
    const [collection, loadedSupportedArea] = await Promise.all([
      fetchLocations(config.locationsUrl),
      loadSupportedLocationArea(config.campusBoundaryUrl).catch((error) => {
        console.warn("Supported YCT location area could not load", error);
        // Location must fail closed when the authoritative campus/context
        // boundary is unavailable. The map itself can still be browsed.
        return { contains: () => false };
      }),
    ]);
    const supportedArea = loadedSupportedArea?.contains
      ? loadedSupportedArea : { contains: () => false };
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
      onRouteProgress: (progress) => mapController?.updateUserRouteProgress(progress),
      onClear: () => mapController?.clearUserRoute(),
      onRouteStale: (stale) => mapController?.setUserRouteStale(stale),
      onFreshLocationRequired: () => userLocationController?.refresh?.() ?? false,
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
      onClear: (details) => {
        mapController?.clearUserLocation();
        navigationController?.clearLivePosition(details);
      },
      onRecenter: () => mapController?.recenterUserLocation(),
      onHeading: (heading) => mapController?.updateUserHeading(heading),
      supportedArea,
      getMapBearing: () => mapController?.getBearing?.() || 0,
    });
    if (config.headingDiagnosticsAvailable && new URLSearchParams(window.location.search).get("headingDebug") === "1") {
      window.yctHeadingDiagnostic = () => {
        const snapshot = userLocationController.getHeadingDiagnostic();
        console.table(snapshot);
        return snapshot;
      };
      console.info("YCT heading diagnostics enabled. Run yctHeadingDiagnostic() in the console.");
    }
    setInterfaceState("browsing");

    try {
      mapController = await createMap({
        container: "map",
        config,
        features,
        onSelect: selectDestination,
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
