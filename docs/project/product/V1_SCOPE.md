# V1 Scope — YCT Map

This document defines what is included and excluded from Version 1.

Product decisions recorded here are authoritative. Do not silently redefine them.

---

## Map Interface

- Map-first interface — no unnecessary landing page before the map.
- Floating search and map controls.
- Bottom-sheet patterns preferred for mobile interaction.
- Mobile-first; desktop must also work correctly.
- OpenStreetMap-derived base tiles provide the underlying geographic context.
- YCT Map maintains its own campus-specific data layer on top of OSM.
- OSM coverage does not determine YCT Map quality or completeness.

---

## Location Types

### Physical Locations

Each navigable physical location uses **one primary arrival point / main entrance** in V1.

Location types include:
- buildings
- schools / faculties
- gates (campus entrances)
- hostels
- libraries
- sports areas
- food locations (cafeterias, tuck shops, etc.)
- medical facilities
- administrative facilities
- other important campus destinations

**Building geometry:** buildings may be irregular polygons. A perfect polygon is not required for V1. A correct destination point and primary entrance take priority over geometric accuracy.

### Internal Locations

Internal locations (departments, offices, classrooms, lecture rooms) require:
- name
- parent building reference
- floor

Internal locations do **not** require independent outdoor GPS coordinates in V1.

---

## Normal Users (No Account Required)

Normal users — students, staff, visitors — may:
- Search campus destinations
- Browse locations by category
- Get a route from current GPS location to a destination
- Choose a starting point manually when GPS is disabled or unavailable
- View route distance and estimated walking time
- Receive basic written / step-by-step route guidance
- Submit campus contributions (new locations or corrections) without an account

---

## Navigation

- Route visualized on the map.
- Route distance and estimated walking time displayed.
- Basic written / step-by-step guidance.
- Live movement tracking when GPS is active.
- Controlled rerouting when a user materially departs the planned route.
- GPS noise must not trigger unnecessary rerouting.
- Path distances are calculated from geographic geometry — not manually entered.
- Routing applies **only within YabaTech campus boundaries**. YCT Map is not a city-wide navigation service.

---

## Public Contributions

- Any user may submit a new location or a correction without creating an account.
- Submissions enter a moderation queue.
- Submissions do **not** directly modify verified public map data.
- Editors review and act on contributions.

---

## Admin / Editor Access (Authenticated)

Editors and administrators require authenticated access.

Editors may:
- Add locations
- Correct locations
- Verify location information
- Review contributions and act: approve / edit+approve / merge duplicates / reject / add missing info / flag for further review
- Maintain aliases and categories
- Identify and update main entrances
- Maintain internal locations
- Represent missing walkable paths within YCT Map

---

## Demonstration Data

- Software is developed and tested using **explicitly labelled demonstration/seed data**.
- Real campus data is populated and verified separately by the project team through field visits.
- Demo data must be clearly distinguishable from verified production campus data in the data model.
- Demo records must be removable or replaceable without damaging the production data model.
- Never assign real YabaTech building names to invented coordinates and mark them verified.

See `docs/project/governance/DEFINITION_OF_DONE.md` for the SOFTWARE VERIFIED vs FIELD VERIFIED distinction.

---

## Not In V1

The following are explicitly deferred:

| Feature | Notes |
|---------|-------|
| Student user accounts | No login required for normal use |
| Navigation outside YabaTech | Campus-only routing |
| Detailed indoor floor plans | Floor referenced by name only |
| Multiple entrances per building | One primary entrance in V1 |
| Location photographs | Deferred |
| Offline maps | Deferred |
| Voice navigation | Deferred |
| Augmented reality | Deferred |
| Photorealistic 3D | Modest 3D/depth effects only; must not delay core features |
| Social features (ratings, comments, reviews) | Deferred |
| City-wide routing | Not in scope |
