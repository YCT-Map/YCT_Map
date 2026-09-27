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

export function locationQualityLabel(accuracyMetres) {
  const quality = accuracyState(accuracyMetres);
  if (quality === "reasonable") return "Good";
  if (quality === "low") return "Fair";
  return "Poor";
}

export function createLocationStabilizer({ warmupReasonableFixes = 2 } = {}) {
  let recent = [];
  let stable = null;

  function robustEstimate(items) {
    const longitudeMedian = [...items].sort((a, b) => a.longitude - b.longitude)[Math.floor(items.length / 2)].longitude;
    const latitudeMedian = [...items].sort((a, b) => a.latitude - b.latitude)[Math.floor(items.length / 2)].latitude;
    const medianPoint = { longitude: longitudeMedian, latitude: latitudeMedian };
    const medianAccuracy = [...items].sort((a, b) => a.accuracyMetres - b.accuracyMetres)[Math.floor(items.length / 2)].accuracyMetres;
    const plausible = items.filter((item) => distanceMetres(medianPoint, item) <= Math.max(15, medianAccuracy * 1.5));
    const candidates = plausible.length >= 2 ? plausible : items;
    const totalWeight = candidates.reduce((sum, item) => sum + 1 / Math.max(3, item.accuracyMetres) ** 2, 0);
    const longitude = candidates.reduce((sum, item) => sum + item.longitude / Math.max(3, item.accuracyMetres) ** 2, 0) / totalWeight;
    const latitude = candidates.reduce((sum, item) => sum + item.latitude / Math.max(3, item.accuracyMetres) ** 2, 0) / totalWeight;
    const centre = { longitude, latitude };
    const spread = Math.max(...candidates.map((item) => distanceMetres(centre, item)), 0);
    const reported = candidates.reduce((sum, item) => sum + item.accuracyMetres, 0) / candidates.length;
    return { ...candidates.at(-1), longitude, latitude, accuracyMetres: Math.max(reported, spread),
      observedSpreadMetres: spread, deviceAccuracyMetres: candidates.at(-1).accuracyMetres };
  }

  function confidenceFor(estimate) {
    if (estimate.observedSpreadMetres > Math.max(12, estimate.deviceAccuracyMetres * 1.5)) return "unstable";
    if (estimate.deviceAccuracyMetres <= ACCURACY.reasonableMetres && estimate.observedSpreadMetres <= 10) return "stable";
    return "approximate";
  }

  function update(sample, quality) {
    recent.push(sample);
    recent = recent.slice(-5);
    if (!stable) {
      const reasonable = recent.filter((item) => accuracyState(item.accuracyMetres) === "reasonable");
      if (reasonable.length < warmupReasonableFixes && recent.length < 3) {
        return { ready: false, reason: "warming-up", sample: null, quality };
      }
      const candidates = reasonable.length >= warmupReasonableFixes ? reasonable : recent;
      const estimate = robustEstimate(candidates);
      stable = { ...estimate, timestamp: sample.timestamp, headingDegrees: null,
        locationConfidence: confidenceFor(estimate) };
      return { ready: true, reason: "warmup-complete", sample: stable,
        quality: accuracyState(stable.accuracyMetres), confidence: stable.locationConfidence, moved: true };
    }

    const materiallyWorse = sample.accuracyMetres >= stable.accuracyMetres * 1.75 &&
      sample.accuracyMetres - stable.accuracyMetres >= 10;
    if (materiallyWorse) {
      recent.pop();
      return { ready: true, reason: "keep-better-position", sample: stable,
        quality: accuracyState(stable.accuracyMetres), confidence: stable.locationConfidence, moved: false };
    }

    const estimate = robustEstimate(recent);
    const displacement = distanceMetres(stable, estimate);
    const elapsedSeconds = Math.max(0, (sample.timestamp - stable.timestamp) / 1000);
    const stationaryRadius = Math.max(3, Math.min(10,
      Math.max(stable.accuracyMetres, estimate.accuracyMetres) * 0.6));
    const latestPair = recent.slice(-2);
    const sustainedShift = latestPair.length === 2 &&
      latestPair.every((item) => distanceMetres(stable, item) > stationaryRadius) &&
      distanceMetres(latestPair[0], latestPair[1]) <= Math.max(12,
        Math.max(...latestPair.map((item) => item.accuracyMetres)) * 1.5);
    const credibleMovement = displacement > stationaryRadius ||
      sustainedShift || (sample.speedMetresPerSecond >= ACCURACY.headingMinimumSpeedMps && displacement > 2);
    if (!credibleMovement && elapsedSeconds <= 10) {
      stable = { ...stable, timestamp: sample.timestamp,
        accuracyMetres: estimate.accuracyMetres, deviceAccuracyMetres: sample.accuracyMetres,
        observedSpreadMetres: estimate.observedSpreadMetres, locationConfidence: confidenceFor(estimate),
        headingDegrees: null };
      return { ready: true, reason: "stationary", sample: stable,
        quality: accuracyState(stable.accuracyMetres), confidence: stable.locationConfidence, moved: false };
    }

    stable = { ...estimate, headingDegrees: sample.headingDegrees,
      locationConfidence: confidenceFor(estimate) };
    return { ready: true, reason: "movement", sample: stable,
      quality: accuracyState(stable.accuracyMetres), confidence: stable.locationConfidence, moved: true };
  }

  return { update, reset() { recent = []; stable = null; }, getStable: () => stable };
}
