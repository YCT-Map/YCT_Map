const EARTH_RADIUS_METRES = 6_371_008.8;

export const ACCURACY = Object.freeze({
  reasonableMetres: 25,
  lowMetres: 60,
  maximumDisplayMetres: 100,
  maximumPlausibleSpeedMps: 12,
  headingMinimumSpeedMps: 0.8,
});

function finite(value) {
  return typeof value === "number" && Number.isFinite(value);
}

export function normalizePosition(position) {
  const coordinates = position?.coords;
  const timestamp = Number(position?.timestamp);
  const longitude = Number(coordinates?.longitude);
  const latitude = Number(coordinates?.latitude);
  const accuracyMetres = Number(coordinates?.accuracy);

  if (!finite(longitude) || !finite(latitude) || !finite(accuracyMetres) || !finite(timestamp)) return null;
  if (longitude < -180 || longitude > 180 || latitude < -90 || latitude > 90) return null;
  if (accuracyMetres < 0 || timestamp <= 0) return null;

  const speed = coordinates?.speed;
  const heading = coordinates?.heading;
  const speedMetresPerSecond = finite(speed) && speed >= 0 ? speed : null;
  const headingDegrees = finite(heading) && heading >= 0 && heading <= 360 &&
    speedMetresPerSecond !== null && speedMetresPerSecond >= ACCURACY.headingMinimumSpeedMps
    ? heading % 360
    : null;

  return { longitude, latitude, accuracyMetres, timestamp, headingDegrees, speedMetresPerSecond };
}

export function accuracyState(accuracyMetres) {
  if (accuracyMetres <= ACCURACY.reasonableMetres) return "reasonable";
  if (accuracyMetres <= ACCURACY.lowMetres) return "low";
  if (accuracyMetres <= ACCURACY.maximumDisplayMetres) return "provisional";
  return "unusable";
}

export function distanceMetres(from, to) {
  const radians = (degrees) => degrees * Math.PI / 180;
  const latitude1 = radians(from.latitude);
  const latitude2 = radians(to.latitude);
  const latitudeDelta = latitude2 - latitude1;
  const longitudeDelta = radians(to.longitude - from.longitude);
  const haversine = Math.sin(latitudeDelta / 2) ** 2 +
    Math.cos(latitude1) * Math.cos(latitude2) * Math.sin(longitudeDelta / 2) ** 2;
  return 2 * EARTH_RADIUS_METRES * Math.asin(Math.sqrt(haversine));
}

export function assessSample(rawPosition, previousAccepted = null) {
  const sample = normalizePosition(rawPosition);
  if (!sample) return { accepted: false, reason: "invalid", sample: null };

  const quality = accuracyState(sample.accuracyMetres);
  if (quality === "unusable") return { accepted: false, reason: "poor-accuracy", sample, quality };
  if (previousAccepted && sample.timestamp <= previousAccepted.timestamp) {
    return { accepted: false, reason: "stale", sample, quality };
  }

  if (previousAccepted) {
    const elapsedSeconds = (sample.timestamp - previousAccepted.timestamp) / 1000;
    const apparentSpeed = elapsedSeconds > 0 ? distanceMetres(previousAccepted, sample) / elapsedSeconds : Infinity;
    const accuracyImproved = sample.accuracyMetres < previousAccepted.accuracyMetres * 0.75;
    if (apparentSpeed > ACCURACY.maximumPlausibleSpeedMps && !accuracyImproved) {
      return { accepted: false, reason: "implausible-jump", sample, quality, apparentSpeed };
    }
    if (quality === "provisional" && previousAccepted.accuracyMetres <= ACCURACY.lowMetres) {
      return { accepted: false, reason: "keep-better-position", sample, quality };
    }
  }

  return { accepted: true, reason: "accepted", sample, quality };
}
