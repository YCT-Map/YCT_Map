const EARTH_RADIUS_METRES = 6_371_008.8;
const EARLIEST_BROWSER_TIMESTAMP_MS = Date.UTC(2000, 0, 1);
export const MAX_BROWSER_SAMPLE_AGE_MS = 5_000;

export const ACCURACY = Object.freeze({
  reasonableMetres: 25,
  lowMetres: 60,
  maximumDisplayMetres: 100,
  maximumPlausibleSpeedMps: 12,
  headingMinimumSpeedMps: 0.8,
});

export const STABILIZATION = Object.freeze({
  windowSize: 12,
  warmupReasonableFixes: 3,
  warmupMinimumSpanMs: 1_500,
  retainedFixMaximumAgeMs: 10_000,
  movementEvidenceRequired: 2,
  stationaryEvidenceRequired: 3,
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

export function assessSample(rawPosition, previousAccepted = null, {
  currentTime = Date.now(), maximumSampleAgeMs = MAX_BROWSER_SAMPLE_AGE_MS,
} = {}) {
  const sample = normalizePosition(rawPosition);
  if (!sample) return { accepted: false, reason: "invalid", sample: null };

  // GeolocationPosition.timestamp is epoch-based in browsers. Synthetic unit
  // traces use small relative timestamps, so freshness is applied only to
  // real browser-shaped values.
  if (sample.timestamp >= EARLIEST_BROWSER_TIMESTAMP_MS &&
      currentTime >= EARLIEST_BROWSER_TIMESTAMP_MS &&
      currentTime - sample.timestamp > maximumSampleAgeMs) {
    return { accepted: false, reason: "stale", sample,
      quality: accuracyState(sample.accuracyMetres) };
  }

  const quality = accuracyState(sample.accuracyMetres);
  if (quality === "unusable") return { accepted: false, reason: "poor-accuracy", sample, quality };
  if (previousAccepted && sample.timestamp <= previousAccepted.timestamp) {
    return { accepted: false, reason: "stale", sample, quality };
  }

  if (previousAccepted) {
    const elapsedSeconds = (sample.timestamp - previousAccepted.timestamp) / 1000;
    const displacement = distanceMetres(previousAccepted, sample);
    const uncertaintyAllowance = (previousAccepted.accuracyMetres + sample.accuracyMetres) * 0.5;
    const credibleDisplacement = Math.max(0, displacement - uncertaintyAllowance);
    const apparentSpeed = elapsedSeconds > 0 ? credibleDisplacement / elapsedSeconds : Infinity;
    const accuracyImproved = sample.accuracyMetres < previousAccepted.accuracyMetres * 0.75;
    const clearlySeparated = displacement > Math.max(35, uncertaintyAllowance * 1.5);
    if (apparentSpeed > ACCURACY.maximumPlausibleSpeedMps && clearlySeparated && !accuracyImproved) {
      return { accepted: false, reason: "implausible-jump", sample, quality, apparentSpeed };
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

export function createLocationStabilizer({
  warmupReasonableFixes = STABILIZATION.warmupReasonableFixes,
  warmupMinimumSpanMs = STABILIZATION.warmupMinimumSpanMs,
  retainedFixMaximumAgeMs = STABILIZATION.retainedFixMaximumAgeMs,
} = {}) {
  let recent = [];
  let stable = null;
  let lastReliableTimestamp = null;
  let motionState = "stationary";
  let movementEvidence = 0;
  let stationaryEvidence = 0;

  function robustEstimate(items) {
    const ordered = [...items].sort((a, b) => a.timestamp - b.timestamp);
    const longitudeMedian = [...ordered].sort((a, b) => a.longitude - b.longitude)[Math.floor(ordered.length / 2)].longitude;
    const latitudeMedian = [...ordered].sort((a, b) => a.latitude - b.latitude)[Math.floor(ordered.length / 2)].latitude;
    const medianPoint = { longitude: longitudeMedian, latitude: latitudeMedian };
    const medianAccuracy = [...ordered].sort((a, b) => a.accuracyMetres - b.accuracyMetres)[Math.floor(ordered.length / 2)].accuracyMetres;
    const plausible = ordered.filter((item) => distanceMetres(medianPoint, item) <= Math.max(12, medianAccuracy * 1.75));
    const candidates = plausible.length >= 2 ? plausible : ordered;
    const newestTimestamp = candidates.at(-1).timestamp;
    const weightFor = (item) => {
      // Accuracy is a radius estimate, not Gaussian variance. Capping the
      // accuracy term prevents one optimistic 2 m claim from owning the fix.
      const cappedAccuracy = Math.max(5, Math.min(30, item.accuracyMetres));
      const ageRatio = Math.min(1, Math.max(0, (newestTimestamp - item.timestamp) / 12_000));
      const recency = 1 - ageRatio * 0.35;
      return recency / cappedAccuracy;
    };
    const totalWeight = candidates.reduce((sum, item) => sum + weightFor(item), 0);
    const longitude = candidates.reduce((sum, item) => sum + item.longitude * weightFor(item), 0) / totalWeight;
    const latitude = candidates.reduce((sum, item) => sum + item.latitude * weightFor(item), 0) / totalWeight;
    const centre = { longitude, latitude };
    const spread = Math.max(...candidates.map((item) => distanceMetres(centre, item)), 0);
    const reported = candidates.reduce((sum, item) => sum + item.accuracyMetres * weightFor(item), 0) / totalWeight;
    return { ...candidates.at(-1), longitude, latitude, accuracyMetres: Math.max(reported, spread),
      observedSpreadMetres: spread, deviceAccuracyMetres: candidates.at(-1).accuracyMetres,
      estimateSourceCount: candidates.length };
  }

  function confidenceFor(estimate) {
    if (estimate.observedSpreadMetres > Math.max(12, estimate.deviceAccuracyMetres * 1.5)) return "unstable";
    if (estimate.deviceAccuracyMetres <= ACCURACY.reasonableMetres && estimate.observedSpreadMetres <= 10) return "stable";
    return "approximate";
  }

  function resultFor(reason, sample, { moved = false, ready = true,
    freshness = "fresh", retainedAgeMs = null } = {}) {
    return { ready, reason, sample,
      quality: sample ? accuracyState(sample.accuracyMetres) : null,
      confidence: sample?.locationConfidence ?? null,
      freshness,
      retainedAgeMs,
      moved,
      motionState };
  }

  function initialise(items, reason) {
    const estimate = robustEstimate(items);
    motionState = "stationary";
    stable = { ...estimate, timestamp: items.at(-1).timestamp, headingDegrees: null,
      motionState, freshness: "fresh", locationConfidence: confidenceFor(estimate) };
    if (stable.deviceAccuracyMetres <= ACCURACY.lowMetres) lastReliableTimestamp = stable.timestamp;
    return resultFor(reason, stable, { moved: true });
  }

  function isConverged() {
    const reasonable = recent.filter((item) => accuracyState(item.accuracyMetres) === "reasonable");
    if (reasonable.length < warmupReasonableFixes) return false;
    const span = reasonable.at(-1).timestamp - reasonable[0].timestamp;
    if (span < warmupMinimumSpanMs) return false;
    const estimate = robustEstimate(reasonable);
    const convergenceRadius = Math.max(6, Math.min(15, estimate.deviceAccuracyMetres * 0.8));
    return estimate.observedSpreadMetres <= convergenceRadius && confidenceFor(estimate) !== "unstable";
  }

  function update(sample, quality) {
    const previousRaw = recent.at(-1) || null;
    recent.push(sample);
    recent = recent.slice(-STABILIZATION.windowSize);
    if (!stable) {
      const reasonable = recent.filter((item) => accuracyState(item.accuracyMetres) === "reasonable");
      if (!isConverged()) {
        return { ready: false, reason: "warming-up", sample: null, quality, motionState };
      }
      return initialise(reasonable, "warmup-complete");
    }

    const materiallyWorse = sample.accuracyMetres >= stable.accuracyMetres * 1.75 &&
      sample.accuracyMetres - stable.accuracyMetres >= 10;
    // `stable.timestamp` belongs to the evidence that supports the displayed
    // coordinate. It must not be refreshed merely because a newer callback was
    // received while that older coordinate remained on screen.
    const reliableAge = Math.max(0, sample.timestamp - stable.timestamp);
    const retentionLimit = motionState === "stationary"
      ? retainedFixMaximumAgeMs : retainedFixMaximumAgeMs * 0.6;

    const estimate = robustEstimate(recent);
    const displacement = distanceMetres(stable, estimate);
    const elapsedSeconds = Math.max(0.001, (sample.timestamp - stable.timestamp) / 1000);
    const rawStep = previousRaw ? distanceMetres(previousRaw, sample) : displacement;
    const rawElapsed = previousRaw ? Math.max(0.001, (sample.timestamp - previousRaw.timestamp) / 1000) : elapsedSeconds;
    const uncertaintyRadius = Math.max(2.5, Math.min(12,
      Math.max(stable.deviceAccuracyMetres ?? stable.accuracyMetres, sample.accuracyMetres) * 0.55));
    const recentShift = recent.slice(-3);
    const sustainedShift = recentShift.length === 3 &&
      recentShift.every((item) => distanceMetres(stable, item) > uncertaintyRadius * 0.75) &&
      distanceMetres(recentShift[0], recentShift.at(-1)) > uncertaintyRadius;
    const coherentPair = recent.length >= 2 && recent.slice(-2).every(
      (item) => distanceMetres(stable, item) > uncertaintyRadius,
    ) && rawStep <= Math.max(12, sample.accuracyMetres * 1.5);
    const reportedMotion = sample.speedMetresPerSecond !== null &&
      sample.speedMetresPerSecond >= ACCURACY.headingMinimumSpeedMps;
    const credibleMovement = (displacement > uncertaintyRadius &&
      (rawStep > uncertaintyRadius * 0.65 || sustainedShift)) ||
      rawStep > uncertaintyRadius * 1.1 || coherentPair ||
      (reportedMotion && (rawStep > 2 || sustainedShift));

    if (credibleMovement) {
      movementEvidence += 1;
      stationaryEvidence = 0;
      if (movementEvidence >= STABILIZATION.movementEvidenceRequired) {
        const credibleSpeed = sample.speedMetresPerSecond ?? rawStep / rawElapsed;
        motionState = credibleSpeed >= ACCURACY.headingMinimumSpeedMps ? "walking" : "slow-walk";
      }
    } else {
      movementEvidence = 0;
      stationaryEvidence += 1;
      if (stationaryEvidence >= STABILIZATION.stationaryEvidenceRequired) motionState = "stationary";
    }

    // Keep one isolated weaker fix from moving the marker, but retain it in
    // `recent` so several coherent fresh fixes can prove that the user moved.
    // While movement is still being confirmed, do not make the old displayed
    // coordinate look fresh by copying the new callback timestamp onto it.
    const movementPending = credibleMovement && motionState === "stationary";
    if (motionState === "stationary" &&
        ((materiallyWorse && reliableAge <= retentionLimit) || movementPending)) {
      stable = { ...stable, freshness: "retained" };
      return resultFor(
        movementPending ? "checking-movement" : "keep-better-position",
        stable,
        { freshness: "retained", retainedAgeMs: reliableAge },
      );
    }

    if (motionState === "stationary") {
      stable = { ...stable, timestamp: sample.timestamp,
        accuracyMetres: estimate.accuracyMetres, deviceAccuracyMetres: sample.accuracyMetres,
        observedSpreadMetres: estimate.observedSpreadMetres, locationConfidence: confidenceFor(estimate),
        headingDegrees: null, speedMetresPerSecond: null, motionState, freshness: "fresh" };
      if (sample.accuracyMetres <= ACCURACY.lowMetres) lastReliableTimestamp = sample.timestamp;
      return resultFor(credibleMovement ? "checking-movement" : "stationary", stable);
    }

    // Once coherent movement wins the hysteresis decision, estimate from the
    // latest coherent fixes instead of allowing an older precise cluster to
    // keep anchoring the user behind their real movement.
    const movementEstimate = credibleMovement
      ? robustEstimate(recent.slice(-3)) : estimate;
    stable = { ...movementEstimate, timestamp: sample.timestamp,
      headingDegrees: credibleMovement ? sample.headingDegrees : null,
      motionState, freshness: "fresh", locationConfidence: confidenceFor(movementEstimate) };
    if (sample.accuracyMetres <= ACCURACY.lowMetres) lastReliableTimestamp = sample.timestamp;
    return resultFor("movement", stable, { moved: true });
  }

  function finalize() {
    if (stable) return resultFor("acquisition-timeout", stable, { moved: true });
    if (!recent.length) return { ready: false, reason: "no-fix", sample: null, motionState };
    if (!isConverged()) {
      return { ready: false, reason: "unconfirmed-fix", sample: null, motionState };
    }
    const reasonable = recent.filter((item) => accuracyState(item.accuracyMetres) === "reasonable");
    return initialise(reasonable, "acquisition-timeout");
  }

  return {
    update,
    finalize,
    isConverged,
    reset() {
      recent = [];
      stable = null;
      lastReliableTimestamp = null;
      motionState = "stationary";
      movementEvidence = 0;
      stationaryEvidence = 0;
    },
    getStable: () => stable,
    getDiagnostics: () => ({ acceptedFixes: recent.length, motionState,
      converged: isConverged(), lastReliableTimestamp }),
  };
}
