export async function fetchLocations(url, { signal } = {}) {
  const response = await fetch(url, {
    headers: { Accept: "application/geo+json, application/json" },
    signal,
  });

  if (!response.ok) {
    throw new Error(`Location request failed with status ${response.status}.`);
  }

  const payload = await response.json();
  if (payload.type !== "FeatureCollection" || !Array.isArray(payload.features)) {
    throw new Error("Location service returned an unexpected response.");
  }

  return payload;
}
