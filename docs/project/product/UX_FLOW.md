# UX Flow — YCT Map

This document traces the actual user journey through the YCT Map application.

Implementation has not yet started. This document records **approved intended flows** based on the product specification.

Sections are marked:
- APPROVED INTENT — decided and not to be changed without owner approval
- OPEN — awaiting detailed design decision

---

## 1. First Visit (Unauthenticated User)

**APPROVED INTENT**

The user opens YCT Map. The map is the primary interface — there is no unnecessary landing/marketing page.

On first load:
1. The campus map renders centered on YabaTech.
2. A floating search bar is visible.
3. Map controls (zoom, locate-me) are accessible.
4. Location permission may be requested (browser/device prompt).

If location permission is granted: the user's position is shown on the map.
If location permission is denied: the user can manually choose a starting point later.

---

## 2. Search

**APPROVED INTENT**

1. User taps or clicks the search bar.
2. User types a destination name or category.
3. Results appear (buildings, departments, gates, facilities, etc.).
4. User selects a result.
5. The map pans/zooms to the destination.
6. A destination panel / bottom sheet appears showing:
   - destination name
   - category
   - brief description (if available)
   - "Get Directions" action

---

## 3. Getting Directions

**APPROVED INTENT**

From the destination panel:
1. User taps "Get Directions".
2. If GPS is active: route is calculated from current location.
3. If GPS is not active: user is prompted to choose a starting point (search for one, or tap the map).
4. Route is visualized on the map.
5. A route panel / bottom sheet appears showing:
   - total distance
   - estimated walking time
   - basic written step-by-step guidance
6. User begins navigation.

---

## 4. Active Navigation

**APPROVED INTENT**

1. The map follows the user's live position.
2. Route progress is shown.
3. If the user materially departs the route, rerouting is triggered.
4. GPS noise does not trigger unnecessary rerouting.
5. User may cancel navigation at any time.

---

## 5. Browse by Category

**OPEN — design to be confirmed**

User may browse campus locations organized by category (buildings, gates, food, hostels, sports, etc.) without using the search bar.

---

## 6. Submit a Contribution (Unauthenticated)

**APPROVED INTENT**

1. User finds a location that is missing or incorrect.
2. User accesses the contribution flow (exact entry point OPEN).
3. User fills in contribution details — no account required.
4. Submission enters the moderation queue.
5. User receives confirmation that the submission was received.
6. User is not shown the submitted data as verified until an editor approves it.

---

## 7. Editor Login

**APPROVED INTENT**

1. Editor navigates to the editor / admin interface.
2. Editor logs in with credentials.
3. Editor accesses the editor dashboard.

Authentication uses Django's built-in session-based authentication for administrator-provisioned editor accounts.

---

## 8. Editor Workflow

See `docs/project/product/EDITOR_WORKFLOW.md`.

---

## 9. Empty States

**APPROVED INTENT**

- Search with no results: clear message, suggestion to submit a contribution.
- No GPS available: prompt to choose starting point manually.
- No route found: clear message explaining the issue.

---

## 10. Error States

**APPROVED INTENT**

- Map fails to load: clear error message; do not show a broken UI.
- Network failure: surfaced to the user; no silent failure.
- Route calculation failure: clear message; user is not shown a fake success.

---

## 11. Session Recovery

**OPEN**

No persistent session for normal users (no account required).
Editor sessions: standard authentication session/token behavior.
