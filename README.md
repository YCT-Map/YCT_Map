# YCT Map

A mobile-first, web-based navigation and campus information platform for **Yaba College of Technology (YabaTech)**, Lagos, Nigeria.

The map is the primary interface. Students, staff and visitors can search campus destinations, browse categories, and navigate within YabaTech — no account required. Editors and administrators manage campus data through an authenticated interface.

---

## Project Status

**Phase:** PHASE 4 — POST-CLOSEOUT LIVE-ROUTING STABILITY REVIEW
**Application implementation:** PHASES 1–3 OWNER ACCEPTED; PHASE 4 SPRINTS 001–003 OWNER ACCEPTED; SPRINT 004 PHYSICAL ACCEPTANCE PENDING
**Product definition:** SUBSTANTIALLY COMPLETE
**Documentation / governance:** CURRENT THROUGH LOCAL LIVE-ROUTING STABILITY CORRECTION
**Campus dataset:** CURRENT ELIGIBLE LOCAL BASELINE OWNER-ATTESTED AND `FIELD_VERIFIED`; FUTURE/EDITED/DEMO RECORDS RETAIN NORMAL VERIFICATION RULES
**Deployment:** EXISTING PRODUCTION SERVICE UNCHANGED; CURRENT CORRECTION IS LOCAL AND AWAITS OWNER RETEST

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

The map uses pinned MapLibre GL JS assets and OpenFreeMap Liberty over the network. The current eligible retained local campus baseline—published Locations/InternalPlaces, active Entrances, active graph records and eligible anchors—has been owner-attested and reconciled to `FIELD_VERIFIED`. This does not weaken the verification model: new/imported records default to `UNVERIFIED`, material edits can demote the affected record, and DEMO fixtures remain explicitly DEMO and isolated for deterministic automated tests.

Live location is optional and transient. The public map waits for a fresh, coherent set of browser fixes before displaying a route-ready position; one cached or accurate-looking callback is not enough. Live-route matching is destination-aware and reports `ON_NETWORK`, `APPROACH_REQUIRED` or `ARRIVAL_CANDIDATE`. A campus-scoped dashed approach line is orientation-only—not a mapped walkway—and is excluded from route distance and ETA. Arrival requires repeated position evidence. Temporary GPS failures retain bounded recovery behavior, coordinates are not persisted or logged as history, and route-setup failures return the mobile UI to an actionable state. Browser accuracy still depends on the device, OS, radio visibility and browser, so physical-phone GPS/navigation/rerouting remains an owner field-test concern.

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
