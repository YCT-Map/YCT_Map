# YabaTech OSM-derived routing snapshot

This directory contains the reviewed OpenStreetMap source snapshot used to build YCT Map's development walkable network.

- Campus selection boundary: OpenStreetMap way `671850885`
- Source mechanism: Overpass API
- OSM database timestamp: `2026-09-18T06:32:00Z`
- Snapshot SHA-256: `C7E0DA9912CEBA941F9C711CC23856E7ED0CDEE6131B48E5FFD71692DB8DCCA9`
- Review manifest: `yabatech_review.json`
- Imported verification state: `UNVERIFIED`

The snapshot is OpenStreetMap data made available under the Open Database License (ODbL). Copyright belongs to OpenStreetMap contributors. See <https://www.openstreetmap.org/copyright>.

The review manifest is an explicit development allowlist. Inclusion means only that the geometry is plausible enough for product review; it does not establish pedestrian access, safety or field verification. YCT Map does not write changes back to OpenStreetMap automatically.

The raw query was:

```overpass
[out:json][timeout:60];
way(671850885);
map_to_area->.campus;
way(area.campus)[highway];
out meta geom;
```

Dry-run import:

```powershell
python manage.py import_osm_walkable_network `
  --snapshot routing/data/osm/yabatech_highways_2026-09-18.overpass.json `
  --review routing/data/osm/yabatech_review.json
```

Add `--apply` only after reviewing the reported topology. Applying replaces the current local routing network and anchors inside one database transaction.
