# Architecture — YCT Map

## Status

```
Current phase:         PHASE 2 — ROUTING & NAVIGATION (planning)
Application code:      PHASE 1 OWNER ACCEPTED; PHASE 2 NOT STARTED
```

This document records approved architectural decisions and expected system design.

Sections are clearly marked CURRENT or PLANNED. Nothing is described as implemented unless it is.

---

## System Overview

YCT Map is a web-based application consisting of:

| Layer | Description | Status |
|-------|-------------|--------|
| Frontend | Django templates, CSS and modular JavaScript; map-first interface | CURRENT — Phase 1 |
| Backend API | Public location/search GeoJSON endpoint | CURRENT — Phase 1 subset |
| Database | SQLite locally; `Location` and `LocationAlias` models | CURRENT — Phase 1 subset |
| Authentication | Django auth installed; editor workflows not implemented | FOUNDATION ONLY |
| Map tiles | OpenFreeMap Liberty rendered with MapLibre GL JS | CURRENT |

---

## Frontend

**Status: CURRENT — PHASE 1 ACCEPTED**

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

---

## Backend

**Status: CURRENT — PHASE 1 SUBSET**

**APPROVED direction:**
- Backend API serving campus data, routing, contributions and editor management

**APPROVED decision (DEC-T02):** Python / Django for business logic, REST APIs, and administrative/editor capabilities.

**CURRENT implementation:** Django `5.2.17` LTS serves the public map and an explicit read-only GeoJSON location collection. Routing, contributions and editor endpoints remain planned.

---

## Database

**Status: CURRENT — LOCAL PHASE 1 SUBSET**

**APPROVED direction:**
- Persistent storage for campus locations, walkable paths, public contributions, editor accounts
- Must support geographic data (coordinates, paths)
- Must clearly separate DEMO data from FIELD VERIFIED data

**APPROVED decision (DEC-T03):** Managed PostgreSQL (Neon preferred; Supabase compatible alternative).

**CURRENT implementation:** SQLite is used only for Sprint 001 local development. Portable Django ORM fields preserve a clean PostgreSQL migration path. No production database infrastructure exists.

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

**Status: NOT STARTED**

**APPROVED direction:**
- Routing applies only within YabaTech campus boundaries
- Routes use campus walkable path data maintained by YCT Map
- Path distances calculated from geographic geometry, not manually entered
- GPS noise must not trigger unnecessary rerouting

**APPROVED decision (DEC-T05):** Shortest-path network graph algorithm (Dijkstra / A*) operating over YCT Map's connected walkable path linestring geometry.

---

## Storage

**Status: NOT STARTED**

No file storage requirements identified for V1 (no location photographs in V1).

---

## Deployment

**Status: NOT STARTED**

**APPROVED decision (DEC-T07, DEC-T08):** Web application deployed on Render, database hosted on Neon, initial platform subdomain with custom DNS support.

---

## Architecture Diagram (Planned)

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

The browser, Phase 1 frontend, public location endpoint, local database and external map-style connection are implemented. Authentication workflows, routing and production infrastructure remain planned.

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
- Building geometry relies on available data; complex irregular polygons may be simplified initially

---

## Conflicts / Open Questions

No unresolved Sprint 001 architecture decision remains. The exact future spatial/PostGIS representation is deliberately deferred until routing/path requirements require it.
