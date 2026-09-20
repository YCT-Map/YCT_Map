# Architecture — YCT Map

## Status

```
Current phase:         PHASE 3 — LIVE NAVIGATION & CORE PRODUCT SYSTEMS
Application code:      SPRINT 001 LIVE-LOCATION FOUNDATION OWNER ACCEPTED
```

This document records approved architectural decisions and expected system design.

Phase 4 campus-place and editor modeling is governed by [`../phase4/CAMPUS_DATA_AND_EDITOR_SPEC.md`](../phase4/CAMPUS_DATA_AND_EDITOR_SPEC.md). That owner-approved contract supersedes earlier building-only, single-category and single-entrance planning assumptions; implementation has not started.

Sections are clearly marked CURRENT or PLANNED. Nothing is described as implemented unless it is.

---

## System Overview

YCT Map is a web-based application consisting of:

| Layer | Description | Status |
|-------|-------------|--------|
| Frontend | Django templates, CSS and modular JavaScript; map-first interface | CURRENT — Phase 1 |
| Backend API | Location/search and explicit anchored-route endpoints | CURRENT — Phase 2 |
| Database | SQLite locally; locations, aliases, walkable graph and anchors | CURRENT — Phase 2 |
| Authentication | Django auth installed; editor workflows not implemented | FOUNDATION ONLY |
| Map tiles | OpenFreeMap Liberty rendered with MapLibre GL JS | CURRENT |

---

## Frontend

**Status: CURRENT — PHASE 2 ACCEPTED**

**APPROVED direction:**
- Mobile-first web application
- Map is the primary interface
- OpenStreetMap-derived base tiles
- Campus-specific data layer rendered over the base map
- Floating search and map controls
- Bottom-sheet patterns for destination and route panels
- Lightweight — minimize data and battery use

**APPROVED decision (DEC-T01):** Responsive HTML5, CSS, and modular JavaScript with MapLibre GL JS for interactive map rendering.

**CURRENT implementation:** Django-rendered HTML, mobile-first CSS and native ES modules. MapLibre GL JS `6.10.0` is loaded from a pinned CDN URL. Search remains usable when map initialization fails.

Phase 3 Sprint 001 separates browser acquisition (`geolocation.js`), pure validation/filtering (`location-filter.js`), location UI state (`user-location.js`) and MapLibre rendering (`map.js`). Ordinary-user position exists only in browser memory and is not sent to Django or persisted.

There is no location-history model, breadcrumb storage or raw-coordinate analytics. Simulated campus coordinates were used for acceptance evidence; physical-device GPS remains unverified pending an approved HTTPS origin.

---

## Backend

**Status: CURRENT — PHASE 2 SUBSET**

**APPROVED direction:**
- Backend API serving campus data, routing, contributions and editor management

**APPROVED decision (DEC-T02):** Python / Django for business logic, REST APIs, and administrative/editor capabilities.

**CURRENT implementation:** Django `5.2.17` LTS serves the public map, an explicit read-only GeoJSON location collection, narrow route endpoints, DEBUG-only routing inspection and a CSRF-protected anonymous contribution endpoint. Full editor endpoints remain planned.

---

## Database

**Status: CURRENT — LOCAL PHASE 2 SUBSET**

**APPROVED direction:**
- Persistent storage for campus locations, walkable paths, public contributions, editor accounts
- Must support geographic data (coordinates, paths)
- Must clearly separate DEMO data from FIELD VERIFIED data

**APPROVED decision (DEC-T03):** Managed PostgreSQL (Neon preferred; Supabase compatible alternative).

**CURRENT implementation:** SQLite stores local locations, aliases, routing nodes, segments and anchors. Portable Django ORM fields and JSON geometry preserve a clean PostgreSQL migration path. No production database infrastructure exists.

---

## Authentication

**Status: FOUNDATION PRESENT; EDITOR ACCESS NOT IMPLEMENTED**

**APPROVED:**
- Normal users require **no account** for navigation, search or contributions
- Editors and administrators require authenticated access

**APPROVED decision (DEC-T06, DEC-T09):** Django's built-in authentication (`django.contrib.auth`) for admin-provisioned editor accounts.

---

## Map Tiles

**Status: CURRENT**

**APPROVED:**
- OpenStreetMap-derived tiles as the base geographic context
- OSM coverage does not determine YCT Map quality
- YCT Map maintains its own campus data layer independent of OSM

**APPROVED decision (DEC-T04, DEC-T11):** OpenStreetMap-derived tiles via MapLibre GL JS, initially using OpenFreeMap's official Liberty style. The base-map provider must remain reasonably replaceable.

The style URL and MapLibre module URL are passed to the frontend as explicit configuration rather than coupled to campus records.

Sprint 002 adds a version-controlled orientation-only GeoJSON snapshot derived from OpenStreetMap way `671850885`. It provides a subtle campus fill, outline, label and geometry-derived framing. Its source metadata is retained with the file. It does not verify individual buildings, entrances, paths or destinations.

YCT Map data and OpenStreetMap remain separate systems. Local destination, alias, entrance, internal-location, path, verification and editor changes do not write back to OSM. Any future OSM contribution requires a separate deliberate editing workflow (DEC-T15).

---

## Routing

**Status: CURRENT — PHASE 2 SPRINT 003**

**APPROVED direction:**
- Routing applies only within YabaTech campus boundaries
- Routes use campus walkable path data maintained by YCT Map
- Path distances calculated from geographic geometry, not manually entered
- GPS noise must not trigger unnecessary rerouting

**APPROVED decision (DEC-T05):** Shortest-path network graph algorithm (Dijkstra / A*) operating over YCT Map's connected walkable path linestring geometry.

**CURRENT implementation:** Active Django network rows become an immutable adjacency graph. A* uses geometry-derived metres plus an admissible Haversine heuristic, reconstructs traversal-oriented geometry and returns an explicit immutable result. A routing-owned anchor connects locations to graph nodes. The browser's user route flow calls a narrow public endpoint, renders a cased blue route with static labelled endpoints, and keeps DEBUG topology tools separate.

The primary development graph is imported from a reviewed OSM/Overpass snapshot into YCT Map-owned records with source references and `UNVERIFIED` state. The import is not a live OSM dependency, does not write back, and does not confer field verification.

---

## Storage

**Status: NOT STARTED**

No file storage requirements identified for V1 (no location photographs in V1).

---

## Deployment

**Status: NOT STARTED**

**APPROVED decision (DEC-T07, DEC-T08):** Web application deployed on Render, database hosted on Neon, initial platform subdomain with custom DNS support.

---

## Architecture Diagram

```
[User Browser / Mobile Device]
           |
           v
   [Frontend Web App]  <----[Map Tile Provider]
           |
           v
     [Backend API]
      |         |
      v         v
[Database]   [Auth Service]
```

The browser frontend, public location and route endpoints, local database, routing services, transient live-location pipeline, live-route progress, controlled rerouting, pending contribution queue and external map-style connection are implemented. Full editor workflows and production infrastructure remain planned.

## Contribution Moderation Foundation

Sprint 004 adds a separate `contributions` application. Anonymous users submit a bounded report through `POST /api/contributions/`; Django validates controlled enums, active location references, coordinate ranges and required fields before saving a `PENDING` record. A request UUID provides retry idempotency. A three-success session quota is separate from the broader hashed-IP abuse ceiling, so ordinary validation mistakes do not consume accepted-submission capacity.

Django staff administration is the only moderation interface in this sprint. `APPROVED`, `REJECTED` and `MERGED` decisions record the moderator and review time. Approval means accepted input for later editor action; it neither changes `Location` data nor grants `FIELD_VERIFIED` status.

Phase 3 is OWNER ACCEPTED / COMPLETE. Live positions, route progress and rerouting evidence remain transient; contribution records persist only intentionally submitted report data. Physical-phone GPS/navigation/rerouting and all field verification remain outside the accepted boundary.

---

## Known Architectural Principles

- Mobile-first and lightweight
- Map is the primary interface
- No user accounts required for normal use
- Demo data must be structurally separate from verified campus data
- Routing is campus-only
- Real YabaTech facts must never be invented — use demo data or field verification

---

## Known Limitations

- Indoor mapping is not in V1
- Routing uses paths maintained in YCT Map data — quality depends on field verification
- Current OSM-derived routing paths and anchors are `UNVERIFIED`; service-road access and exact entrances require later review and field survey
- Browser live-location acquisition/display and live-origin route progress exist; rerouting does not
- Browser live-location display is implemented, but physical-phone GPS remains unverified until an approved HTTPS test origin is available
- Live locations are matched transiently to the routing graph; matched coordinates and progress remain unpersisted
- Building geometry relies on available data; complex irregular polygons may be simplified initially

---

## Conflicts / Open Questions

No unresolved Sprint 001 architecture decision remains. The exact future spatial/PostGIS representation is deliberately deferred until routing/path requirements require it.
