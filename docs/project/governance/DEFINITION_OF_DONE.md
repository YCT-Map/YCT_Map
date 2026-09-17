# Definition of Done

A feature is not "done" simply because its main UI works.

A feature is complete only when all applicable requirements below are satisfied.

## Functional

- Intended user flow works.
- Expected persistence works.
- Refresh/reload behavior works where relevant.
- Error states are handled.
- Loading states are handled.
- Empty states are handled.
- Permission/ownership rules work.
- Offline behavior is handled where applicable.

## UX

- Feature fits the existing product flow.
- Copy is understandable.
- Responsive behavior is acceptable.
- Existing design system is respected.
- User is not shown misleading success states.

## Data

- Validation exists.
- Invalid states are rejected safely.
- Data ownership is enforced.
- Migrations are safe where applicable.
- Historical data is preserved unless otherwise approved.

## Security

- Authentication requirements are enforced.
- Authorization requirements are enforced.
- Secrets stay server-side.
- Sensitive information is not exposed in logs or responses.

## Testing

- Focused tests pass.
- Relevant regression tests pass.
- Typecheck passes.
- Production build passes.
- No legitimate test was skipped or weakened.

## Documentation

Relevant documentation is updated.

## Git

- Diff reviewed.
- No secrets/private files included.
- Worktree state understood.
- Commit created only when authorized.

---

## Demonstration Data vs Field Verification

YCT Map distinguishes two separate verification states. These must never be confused.

### SOFTWARE VERIFIED

A feature is SOFTWARE VERIFIED when:

- code works correctly;
- tests pass;
- map renders as expected;
- search returns results;
- route algorithm produces a valid route;
- distance and time calculation work;
- UI behaves correctly in all required states;
- persistence works;
- contributions are handled.

A feature may be SOFTWARE VERIFIED using demonstration/seed data.

### FIELD VERIFIED

A location or path is FIELD VERIFIED when:

- the real destination physically exists;
- the recorded entrance is correct;
- the path is actually walkable on campus;
- the route does not cross fences, walls or restricted spaces;
- internal location information (floor, department, office) is accurate;
- the record has been reviewed by a trusted team member with physical access.

### Rules

A routing feature may be SOFTWARE VERIFIED while real campus data is still awaiting FIELD VERIFICATION.

Do not confuse SOFTWARE VERIFIED with FIELD VERIFIED.

Do not mark a location FIELD VERIFIED without actual campus confirmation.

Demonstration data must be clearly labelled and must never appear as verified campus data in production.

Demo records must be removable or replaceable without damaging the production data model.

---

## Completion Labels

A feature may be labelled:

- IMPLEMENTED
- TESTED
- OWNER REVIEW REQUIRED
- COMPLETE

Do not use COMPLETE until all required gates are satisfied.
