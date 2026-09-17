# Architecture — YCT Map

## Status

```
Current phase:         PRE-BUILD / FOUNDATION
Application code:      NOT STARTED
```

This document records approved architectural decisions and expected system design.

Sections are clearly marked CURRENT or PLANNED. Nothing is described as implemented unless it is.

---

## System Overview

YCT Map is a web-based application consisting of:

| Layer | Description | Status |
|-------|-------------|--------|
| Frontend | Mobile-first web application; map-first interface | PLANNED |
| Backend API | Serves campus data, handles contributions, editor management | PLANNED |
| Database | Stores locations, paths, contributions, editor accounts | PLANNED |
| Authentication | Editors and administrators only; normal users are unauthenticated | PLANNED |
| Map tiles | Base geographic tiles from an external provider | PLANNED |

---

## Frontend

**Status: NOT STARTED**

**APPROVED direction:**
- Mobile-first web application
- Map is the primary interface
- OpenStreetMap-derived base tiles
- Campus-specific data layer rendered over the base map
- Floating search and map controls
- Bottom-sheet patterns for destination and route panels
- Lightweight — minimize data and battery use

**APPROVED decision (DEC-T01):** Responsive HTML5, CSS, and modular JavaScript with MapLibre GL JS for interactive map rendering.

---

## Backend

**Status: NOT STARTED**

**APPROVED direction:**
- Backend API serving campus data, routing, contributions and editor management

**APPROVED decision (DEC-T02):** Python / Django for business logic, REST APIs, and administrative/editor capabilities.

---

## Database

**Status: NOT STARTED**

**APPROVED direction:**
- Persistent storage for campus locations, walkable paths, public contributions, editor accounts
- Must support geographic data (coordinates, paths)
- Must clearly separate DEMO data from FIELD VERIFIED data

**APPROVED decision (DEC-T03):** Managed PostgreSQL (Neon preferred; Supabase compatible alternative).

---

## Authentication

**Status: NOT STARTED**

**APPROVED:**
- Normal users require **no account** for navigation, search or contributions
- Editors and administrators require authenticated access

**APPROVED decision (DEC-T06, DEC-T09):** Django's built-in authentication (`django.contrib.auth`) for admin-provisioned editor accounts.

---

## Map Tiles

**Status: NOT STARTED**

**APPROVED:**
- OpenStreetMap-derived tiles as the base geographic context
- OSM coverage does not determine YCT Map quality
- YCT Map maintains its own campus data layer independent of OSM

**APPROVED decision (DEC-T04, DEC-T11):** OpenStreetMap-derived tiles via MapLibre GL JS, initially using OpenFreeMap's official Liberty style. The base-map provider must remain reasonably replaceable.

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

This represents planned architecture. None of these layers are currently implemented.

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

No unresolved pre-build architecture decisions currently block Phase 1. Implementation-specific details must be recorded as the application is built.
