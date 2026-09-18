const EARTH_RADIUS_METRES = 6_371_008.8;

export function distanceMetres(a, b) {
  const toRadians = (value) => value * Math.PI / 180;
  const lat1 = toRadians(a[1]);
  const lat2 = toRadians(b[1]);
  const deltaLatitude = lat2 - lat1;
  const deltaLongitude = toRadians(b[0] - a[0]);
  const haversine = Math.sin(deltaLatitude / 2) ** 2
    + Math.cos(lat1) * Math.cos(lat2) * Math.sin(deltaLongitude / 2) ** 2;
  return 2 * EARTH_RADIUS_METRES * Math.asin(Math.sqrt(haversine));
}

function projectToLeg(point, start, end) {
  const latitudeRadians = point[1] * Math.PI / 180;
  const scaleX = 111_320 * Math.max(Math.cos(latitudeRadians), 0.01);
  const scaleY = 111_320;
  const ax = (start[0] - point[0]) * scaleX;
  const ay = (start[1] - point[1]) * scaleY;
  const bx = (end[0] - point[0]) * scaleX;
  const by = (end[1] - point[1]) * scaleY;
  const lengthSquared = (bx - ax) ** 2 + (by - ay) ** 2;
  const fraction = lengthSquared ? Math.max(0, Math.min(1, -(ax * (bx - ax) + ay * (by - ay)) / lengthSquared)) : 0;
  const projected = [start[0] + (end[0] - start[0]) * fraction, start[1] + (end[1] - start[1]) * fraction];
  return { projected, fraction, distance: distanceMetres(point, projected) };
}

export function projectOntoRoute(point, coordinates) {
  let best = null;
  let completed = 0;
  for (let index = 0; index < coordinates.length - 1; index += 1) {
    const legLength = distanceMetres(coordinates[index], coordinates[index + 1]);
    const candidate = projectToLeg(point, coordinates[index], coordinates[index + 1]);
    candidate.along = completed + legLength * candidate.fraction;
    if (!best || candidate.distance < best.distance) best = candidate;
    completed += legLength;
  }
  return { ...best, routeLength: completed };
}

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
}

export function createLiveRouteTracker(coordinates, totalDistanceMetres) {
  let progress = 0;
  let previous = null;
  let pendingBackward = null;
  let speedSamples = [];
  let stationarySince = null;
  let lastUsefulSpeedAt = null;
  let arrivalCandidateAt = null;

  return {
    update(position) {
      const point = [position.longitude, position.latitude];
      const projection = projectOntoRoute(point, coordinates);
      const threshold = Math.max(20, Math.min(40, position.accuracyMetres));
      let state = "walking";
      if (projection.distance <= threshold) {
        const proposed = projection.along;
        if (proposed + 8 >= progress) {
          progress = Math.max(progress, proposed);
          pendingBackward = null;
        } else if (pendingBackward !== null && Math.abs(pendingBackward - proposed) <= 8) {
          progress = proposed;
          pendingBackward = null;
        } else {
          pendingBackward = proposed;
          state = "position-uncertain";
        }
      } else {
        state = "position-uncertain";
      }

      if (previous) {
        const elapsed = (position.timestamp - previous.timestamp) / 1000;
        const moved = distanceMetres(point, [previous.longitude, previous.latitude]);
        const uncertainty = Math.max(3, (position.accuracyMetres + previous.accuracyMetres) / 2);
        if (elapsed >= 3 && elapsed <= 30 && position.accuracyMetres <= 25 && previous.accuracyMetres <= 25) {
          if (moved <= uncertainty) {
            stationarySince ??= previous.timestamp;
            if (position.timestamp - stationarySince >= 8_000) state = "stationary";
          } else {
            stationarySince = null;
            const speed = moved / elapsed;
            if (speed >= 0.4 && speed <= 3) {
              speedSamples = [...speedSamples.slice(-4), speed];
              lastUsefulSpeedAt = position.timestamp;
            }
          }
        }
      }
      previous = position;

      const remaining = Math.max(0, totalDistanceMetres - Math.min(progress, totalDistanceMetres));
      const speedFresh = lastUsefulSpeedAt && position.timestamp - lastUsefulSpeedAt <= 60_000;
      const speedLimited = lastUsefulSpeedAt && position.timestamp - lastUsefulSpeedAt <= 180_000;
      const personalSpeed = speedSamples.length >= 3 && speedLimited ? median(speedSamples) : null;
      const speed = personalSpeed || 1.35;
      const etaSource = personalSpeed ? (speedFresh ? "live" : "recent") : "fallback";
      const endpointDistance = distanceMetres(point, coordinates.at(-1));
      const arrivalEligible = position.accuracyMetres <= 25 && remaining <= 15 && endpointDistance <= 15;
      let arrived = false;
      if (arrivalEligible) {
        if (arrivalCandidateAt !== null && position.timestamp - arrivalCandidateAt >= 3_000) arrived = true;
        arrivalCandidateAt ??= position.timestamp;
      } else arrivalCandidateAt = null;
      if (arrived) state = "arrived";
      return {
        state,
        remainingDistanceMetres: remaining,
        etaSeconds: remaining / speed,
        etaSource,
        progressMetres: progress,
        matchedDistanceMetres: projection.distance,
      };
    },
  };
}

export function formatEta(seconds) {
  if (seconds <= 30) return "<1 min";
  return `~${Math.max(1, Math.ceil(seconds / 60))} min`;
}
