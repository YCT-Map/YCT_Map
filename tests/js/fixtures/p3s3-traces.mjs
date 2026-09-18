export const offRouteTrace = Object.freeze({
  provenance: "Derived from the active OSM-derived graph and the School Building to Hostel A* route",
  destinationId: "10000000-0000-4000-8000-000000000005",
  destinationName: "DEMO — Hostel",
  accuracyMetres: 3,
  start: [3.3737271230, 6.5189768280],
  initialRoute: [
    [3.3737271230, 6.5189768280], [3.3738703, 6.5190779], [3.373995, 6.5191765],
    [3.3740768, 6.5192351], [3.3741559, 6.5192604], [3.3742793, 6.5193004],
    [3.3744362, 6.5193483], [3.3745958, 6.5193617], [3.3747245, 6.5193603],
    [3.3748238, 6.5193523], [3.3749351, 6.5193323], [3.3751041, 6.5192964],
    [3.3752449, 6.5192391], [3.3753602, 6.5191365], [3.3753951, 6.5190499],
  ],
  normal: [
    [3.3737713959, 6.5190080813],
    [3.3738156689, 6.5190393346],
  ],
  oneNoisySample: [3.3738156689, 6.5191893346],
  recovery: [3.3738599418, 6.5190705879],
  deviationOnWay1335008711: [
    [3.3754112, 6.5187075],
    [3.37548385, 6.51876935],
    [3.3755565, 6.5188312],
  ],
  replacementRoutePoint: [3.3754112, 6.5187075],
  arrival: [3.3753951, 6.5190499],
});

export const poorAccuracyTrace = Object.freeze({
  onRoute: [3.3738156689, 6.5190393346],
  uncertain: [3.3738156689, 6.5191893346],
  accuracyMetres: 60,
  recoveryAccuracyMetres: 3,
});
