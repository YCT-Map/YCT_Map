# YCT Map

A mobile-first, web-based navigation and campus information platform for **Yaba College of Technology (YabaTech)**, Lagos, Nigeria.

The map is the primary interface. Students, staff and visitors can search campus destinations, browse categories, and navigate within YabaTech — no account required. Editors and administrators manage campus data through an authenticated interface.

---

## Project Status

**Phase:** PHASE 4 — EDITOR & MAPPING TOOLS (IN PROGRESS)
**Application implementation:** PHASES 1–3 OWNER ACCEPTED; PHASE 4 SPRINTS 001–003 OWNER ACCEPTED; SPRINT 004 PHYSICAL ACCEPTANCE PENDING
**Product definition:** SUBSTANTIALLY COMPLETE
**Documentation / governance:** CURRENT THROUGH PHASE 4 PRE-DEPLOYMENT PREPARATION
**Campus production dataset:** INITIAL OWNER-CONFIRMED LOCATIONS PRESENT; ALL REMAIN UNVERIFIED
**Deployment:** CONFIGURATION PREPARED; NOT DEPLOYED

---

## Local Development

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py import_osm_walkable_network --snapshot routing/data/osm/yabatech_highways_2026-09-18.overpass.json --review routing/data/osm/yabatech_review.json --apply
python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/`.

Trusted editors use `http://127.0.0.1:8000/editor/login/`. Accounts are administrator-provisioned; there is no public registration. Sprint 001 supports metadata-only Draft places, controlled physical types, multiple functional categories and typed aliases. Draft and Archived records do not appear on the public map.

The map uses pinned MapLibre GL JS assets and OpenFreeMap Liberty over the network. The working dataset contains owner-confirmed campus Locations that remain explicitly `UNVERIFIED`. The routing graph is YCT Map-owned, OSM-derived and also `UNVERIFIED`; it is not field-verified campus guidance. DEMO fixtures remain isolated for deterministic automated tests and must not be loaded into a production database.

Live location is optional and transient. Initial matching and confirmed rerouting use a narrow no-store Django request; coordinates are not persisted, logged as history or used for analytics. Normal progress and off-route evidence stay client-side. Simulated rerouting is verified; physical-phone GPS/navigation/rerouting remains pending an approved HTTPS test origin.

Anonymous map suggestions are stored as pending moderation records. They require no account or contact details and never alter the public location dataset automatically. Staff review is available through Django admin; approval is not field verification.

---

## Documentation

All project documentation lives in [`docs/project/`](docs/project/README.md).

If you are a coding agent, read [`AGENTS.md`](AGENTS.md) first.

---

## Quick Links

| Document | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Entry point for all coding agents |
| [`docs/project/README.md`](docs/project/README.md) | Documentation index and authority model |
| [`docs/project/operations/CURRENT_STATE.md`](docs/project/operations/CURRENT_STATE.md) | Current project state |
| [`docs/project/product/PROJECT_BRIEF.md`](docs/project/product/PROJECT_BRIEF.md) | What YCT Map is |
| [`docs/project/product/V1_SCOPE.md`](docs/project/product/V1_SCOPE.md) | V1 scope and non-goals |
| [`docs/project/phase4/CAMPUS_DATA_AND_EDITOR_SPEC.md`](docs/project/phase4/CAMPUS_DATA_AND_EDITOR_SPEC.md) | Owner-approved Phase 4 campus-data and editor contract |
| [`docs/project/governance/ENGINEERING_RULES.md`](docs/project/governance/ENGINEERING_RULES.md) | Implementation rules |
