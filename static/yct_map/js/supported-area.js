const METRES_PER_LATITUDE_DEGREE = 111_320;

function geometryCoordinates(geometry) {
  if (geometry?.type === "Polygon") return geometry.coordinates.flat(1);
  if (geometry?.type === "MultiPolygon") return geometry.coordinates.flat(2);
  return [];
}

export function boundsForGeoJSON(collection) {
  const coordinates = collection?.features?.flatMap((feature) => geometryCoordinates(feature.geometry)) || [];
  if (!coordinates.length) return null;
  const longitudes = coordinates.map(([longitude]) => Number(longitude)).filter(Number.isFinite);
  const latitudes = coordinates.map(([, latitude]) => Number(latitude)).filter(Number.isFinite);
  if (!longitudes.length || !latitudes.length) return null;
  return [[Math.min(...longitudes), Math.min(...latitudes)],
    [Math.max(...longitudes), Math.max(...latitudes)]];
}

export function bufferBoundsMetres(bounds, bufferMetres = 400) {
  if (!bounds || bounds.length !== 2 || !Number.isFinite(bufferMetres) || bufferMetres < 0) return null;
  const [[west, south], [east, north]] = bounds;
  const latitude = (south + north) / 2;
  const latitudeDelta = bufferMetres / METRES_PER_LATITUDE_DEGREE;
  const longitudeDelta = bufferMetres /
    (METRES_PER_LATITUDE_DEGREE * Math.max(Math.cos(latitude * Math.PI / 180), 0.01));
  return [[west - longitudeDelta, south - latitudeDelta],
    [east + longitudeDelta, north + latitudeDelta]];
}

export function createSupportedLocationArea(campusGeoJSON, contextMetres = 400) {
  const campusBounds = boundsForGeoJSON(campusGeoJSON);
  const bounds = bufferBoundsMetres(campusBounds, contextMetres);
  if (!bounds) return null;
  return {
    bounds,
    contextMetres,
    contains(position) {
      const longitude = Number(position?.longitude ?? position?.lng);
      const latitude = Number(position?.latitude ?? position?.lat);
      return Number.isFinite(longitude) && Number.isFinite(latitude) &&
        longitude >= bounds[0][0] && longitude <= bounds[1][0] &&
        latitude >= bounds[0][1] && latitude <= bounds[1][1];
    },
  };
}

export async function loadSupportedLocationArea(url, {
  fetchImplementation = globalThis.fetch,
  contextMetres = 400,
} = {}) {
  if (!url || typeof fetchImplementation !== "function") return null;
  const response = await fetchImplementation(url, {
    headers: { Accept: "application/geo+json, application/json" },
  });
  if (!response.ok) throw new Error(`Campus boundary request failed with ${response.status}.`);
  const collection = await response.json();
  const area = createSupportedLocationArea(collection, contextMetres);
  if (!area) throw new Error("Campus boundary could not define the supported location area.");
  return area;
}
