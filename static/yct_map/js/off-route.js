import { distanceMetres, projectOntoRoute } from "./live-route-progress.js?v=checkpoint-flex-nav-1";

export function routeThresholds(accuracyMetres) {
  return {
    onRouteMetres: Math.min(20, Math.max(8, accuracyMetres)),
    offRouteMetres: Math.min(30, Math.max(12, accuracyMetres + 8)),
  };
}

export function createOffRouteDetector({ cooldownMilliseconds = 30_000, stabilizationMilliseconds = 10_000,
  minimumMovementAfterRerouteMetres = 20 } = {}) {
  let state = "following";
  let evidence = [];
  let cooldownUntil = 0;
  let stabilizationUntil = 0;
  let movementAfterReroute = Infinity;
  let previousPosition = null;

  function clearEvidence(nextState = "following") {
    evidence = [];
    state = nextState;
  }

  return {
    evaluate(position, routeCoordinates, { arrived = false } = {}) {
      if (previousPosition && Number.isFinite(movementAfterReroute)) {
        movementAfterReroute += distanceMetres(
          [previousPosition.longitude, previousPosition.latitude], [position.longitude, position.latitude],
        );
      }
      previousPosition = position;
      if (arrived) {
        clearEvidence("arrived");
        return { state, shouldReroute: false };
      }
      if (state === "rerouting") return { state, shouldReroute: false };
      const projection = projectOntoRoute([position.longitude, position.latitude], routeCoordinates);
      if (position.accuracyMetres > 25) {
        clearEvidence("checking-position");
        return { state, shouldReroute: false, reason: "location-uncertain", routeDistanceMetres: projection.distance };
      }
      const thresholds = routeThresholds(position.accuracyMetres);
      if (projection.distance <= thresholds.onRouteMetres) {
        clearEvidence("following");
        return { state, shouldReroute: false, routeDistanceMetres: projection.distance };
      }
      if (projection.distance <= thresholds.offRouteMetres) {
        clearEvidence("checking-position");
        return { state, shouldReroute: false, reason: "route-position-uncertain", routeDistanceMetres: projection.distance };
      }

      evidence.push({ ...position });
      if (evidence.length > 3) evidence.shift();
      state = "checking-position";
      const duration = evidence.length >= 3 ? evidence.at(-1).timestamp - evidence[0].timestamp : 0;
      const displacement = evidence.length >= 3
        ? distanceMetres([evidence[0].longitude, evidence[0].latitude], [evidence.at(-1).longitude, evidence.at(-1).latitude]) : 0;
      const confirmed = evidence.length === 3 && duration >= 8_000 && (displacement >= 8 || duration >= 12_000);
      const stable = position.timestamp >= stabilizationUntil;
      const cooledDown = position.timestamp >= cooldownUntil && movementAfterReroute >= minimumMovementAfterRerouteMetres;
      if (confirmed && stable && cooledDown) {
        state = "off-route-confirmed";
        return { state, shouldReroute: true, routeDistanceMetres: projection.distance };
      }
      return { state, shouldReroute: false, routeDistanceMetres: projection.distance };
    },
    markRerouting() { state = "rerouting"; },
    markSuccess(timestamp) {
      clearEvidence("following");
      stabilizationUntil = timestamp + stabilizationMilliseconds;
      cooldownUntil = timestamp + cooldownMilliseconds;
      movementAfterReroute = 0;
    },
    markFailure() { clearEvidence("reroute-failed"); },
    retry() { clearEvidence("off-route-confirmed"); },
    recover() { clearEvidence("following"); },
    getState: () => state,
  };
}
