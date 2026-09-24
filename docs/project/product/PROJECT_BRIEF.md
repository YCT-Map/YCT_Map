# Project Brief — YCT Map

## Product Name

YCT Map

## One-Sentence Definition

A mobile-first, web-based navigation and campus information platform dedicated to Yaba College of Technology.

## Problem Being Solved

YabaTech is a large, complex campus. Students, staff and visitors frequently struggle to locate buildings, departments, offices and facilities. No dedicated digital campus map currently exists. Generic maps (Google Maps, OpenStreetMap) provide incomplete or inaccurate campus coverage and have no awareness of internal campus destinations or walkable paths.

## Target Users

| User | Description |
|------|-------------|
| Students | Primary users — especially new and visiting students unfamiliar with the campus layout |
| Staff | Locating offices, facilities and less-visited buildings |
| Visitors | Finding their way around campus without prior knowledge |
| Editors | Authenticated users who add, correct and verify campus data |
| Administrators | Senior editors with full data management access |

## Primary Use Cases

1. Search for a campus destination and receive a navigable route.
2. Browse campus locations by category (buildings, gates, food, sports, etc.).
3. Navigate from current GPS location — or a manually chosen starting point — to a destination.
4. Submit a campus location correction or a new location without creating an account.
5. (Editor) Add, edit and verify campus locations, entrances and walkable paths.
6. (Editor) Review, approve, reject or merge public contributions.

## Core Value Proposition

A genuinely usable campus navigation tool — accurate to YabaTech, fast on limited mobile data, maintained by the campus community, and trusted because its data is field-verified.

## V1 Scope

See `docs/project/product/V1_SCOPE.md`.

## Explicit Non-Goals for V1

- Student user accounts or profiles
- Navigation outside YabaTech campus boundaries
- Detailed indoor floor plans
- Detailed indoor turn-by-turn navigation between rooms
- Location photographs
- Offline maps
- Voice navigation
- Augmented reality navigation
- Photorealistic 3D rendering
- Social features (ratings, comments, reviews)
- City-wide or inter-campus routing

## Product Constraints

- Target device: ordinary student smartphones (not high-end)
- Target network: limited mobile data — must be lightweight
- Must be battery-sensitive
- Mobile-first; must also function correctly on desktop
- Map is the primary interface — no unnecessary landing page before the map experience

## Approved Technical Foundation

- Frontend: responsive HTML5, CSS and modular JavaScript
- Interactive map: MapLibre GL JS
- Initial base-map style/service: OpenFreeMap Liberty
- Backend: Python / Django with REST APIs
- Database: PostgreSQL, with Neon preferred
- Editor authentication: Django built-in authentication with admin-managed, invite-only accounts
- Routing: campus graph using Dijkstra / A* over YCT Map walkable-path geometry
- Hosting: Render application service with Neon PostgreSQL

## Success Criteria for V1

- A student can search for a destination and receive a route with distance and estimated walking time.
- Basic written route guidance is available.
- A student can optionally enable GPS or manually choose a starting point.
- A student can submit a location contribution without creating an account.
- An editor can log in, review contributions, and manage campus data.
- A demonstration dataset exists for development and testing.
- Real campus data verification process is defined and documented.
- The application is deployable and accessible on a real device.

## Remaining Implementation Details

The foundational owner decisions are resolved in `docs/project/operations/DECISIONS.md`. Low-risk implementation details such as exact linting tools, schema field types and design tokens are selected during the relevant approved sprint and documented afterward. A custom production domain remains an administrative launch decision; the approved initial deployment uses a Render-provided subdomain.
