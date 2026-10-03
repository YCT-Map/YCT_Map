# Editor Workflow — YCT Map

This document defines the workflow for authenticated editors and administrators managing YCT Map campus data.

---

## Editor Capabilities

Editors and administrators require authenticated access.

An authenticated editor may:

- **Add locations** — create new campus location records
- **Correct locations** — update name, category, entrance point, description, aliases
- **Verify information** — mark a location as FIELD VERIFIED after physical confirmation
- **Review contributions** — view and act on public submissions
- **Manage internal locations** — add/edit departments, offices, classrooms linked to parent buildings
- **Maintain aliases and categories** — manage search aliases and location categories
- **Identify main entrances** — set or update the primary arrival point for a building
- **Represent missing paths** — add walkable paths that are missing from the base map

---

## Contribution Review Actions

When reviewing a public submission, an editor may:

| Action | Description |
|--------|-------------|
| **Approve** | Accept the report as useful input for later editor resolution; do not automatically mutate public campus data |
| **Edit and Approve** | Resolve the report through an authenticated editor action, preserving review history |
| **Merge** | Combine with an existing duplicate record |
| **Reject** | Dismiss the submission with an optional reason |
| **Flag** | Mark for further review by another editor or administrator |
| **Add Missing Info** | Supplement incomplete submission data before approving |

Approved submissions may later be applied through an explicit authenticated editor action, but moderation approval itself does not automatically publish data and never makes it `FIELD_VERIFIED`. Field verification remains a separate deliberate action after trusted physical confirmation.
Rejected submissions are archived, not permanently deleted.

---

## Data Verification States

| State | Meaning |
|-------|---------|
| DEMO | Demonstration/seed data — clearly labelled, not real campus data |
| UNVERIFIED | Submitted or added but not yet field-confirmed |
| FIELD VERIFIED | Physically confirmed by a trusted team member |

Editors must not mark a location FIELD VERIFIED without actual physical confirmation.

Walkable Segments have one approved evidence-specific exception: when an authorized owner explicitly completes a future Path Survey, the server may promote an `UNVERIFIED` segment only if cumulative independent finalized passes satisfy the strict quality and ambiguity rules. This never applies to Locations or Entrances and never automatically revokes verification.

See `docs/project/governance/DEFINITION_OF_DONE.md` for the full SOFTWARE VERIFIED vs FIELD VERIFIED distinction.

---

## Editor Access

- Authentication method: Django built-in authentication
- Editor invite/onboarding model: administrator-managed, invite-only account creation
- Administrators manage editor accounts; authenticated editors and administrators may maintain campus data and moderate contributions according to assigned Django permissions

---

## Editor Interface

Phase 4 Sprint 001 implements the authenticated foundation at `/editor/`:

- login and POST-only logout;
- a small dashboard;
- outdoor-place list;
- Draft place creation;
- place metadata editing;
- controlled physical place type;
- multiple functional categories;
- typed aliases/codes;
- archive and deliberate reactivation.

Draft and Archived places remain outside the public map. Raw coordinate input is deliberately absent; map/current-location placement, entrances, internal places, contribution resolution, path editing and verification tools remain later Phase 4 work.
