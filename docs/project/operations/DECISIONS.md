# Decisions — YCT Map

This document records material decisions made for the project using a lightweight ADR format.

New decisions must be added here when made. Rationale must be recorded at the time of decision.

---

## Decision Format

```
ID:          DEC-XXX
Date:        YYYY-MM-DD
Status:      ACCEPTED | SUPERSEDED | DEFERRED
Decision:    What was decided
Context:     Why a decision was needed
Reason:      Why this option was chosen
Consequences: Impact of this decision
Alternatives considered:
```

---

## DEC-001

```
ID:          DEC-001
Date:        2026-09-16
Status:      ACCEPTED
Decision:    The map is the primary interface. No unnecessary landing page before the map experience.
Context:     Product needed a clear stance on the first-screen experience.
Reason:      YCT Map's value is navigation. Putting a marketing page before the map adds friction with no benefit for the primary use case.
Consequences: The map must render quickly. First-load performance is critical.
Alternatives considered: Traditional landing page (rejected — unnecessary friction).
```

---

## DEC-002

```
ID:          DEC-002
Date:        2026-09-16
Status:      ACCEPTED
Decision:    Normal users require no account for navigation, search or contributions.
Context:     Deciding whether to require registration for any V1 feature.
Reason:      Accounts create friction. Most campus users are students who will not register just to find a building. Contributions should be as easy as possible to encourage data improvement.
Consequences: No session persistence for normal users. Contribution data is anonymous.
Alternatives considered: Optional login (deferred to post-V1).
```

---

## DEC-003

```
ID:          DEC-003
Date:        2026-09-16
Status:      ACCEPTED
Decision:    Student contributions enter a moderation queue. They do not directly modify verified campus data.
Context:     Open contributions risk data corruption if applied directly.
Reason:      Campus navigation requires trust in the data. Unreviewed submissions should not overwrite verified information.
Consequences: Editor review workflow is required in V1. Contributions may take time to appear.
Alternatives considered: Direct edits by students (rejected — data quality risk).
```

---

## DEC-004

```
ID:          DEC-004
Date:        2026-09-16
Status:      ACCEPTED
Decision:    Routing applies only within YabaTech campus boundaries.
Context:     Scope of navigation needed to be defined.
Reason:      YCT Map is a campus tool. City-wide routing is out of scope and would require different data and infrastructure.
Consequences: The application must be clear to users that it is campus-only navigation.
Alternatives considered: City-wide routing (explicitly deferred).
```

---

## DEC-005

```
ID:          DEC-005
Date:        2026-09-16
Status:      ACCEPTED
Decision:    Software is built first using clearly labelled demonstration data. Real campus data is verified separately.
Context:     Real YabaTech campus data requires field visits and cannot be fabricated.
Reason:      Development must not be blocked by the unavailability of verified real data. Demo data allows all software features to be verified independently.
Consequences: Demo data must be structurally separate from production verified data. A DEMO verification state is required in the data model. Demo records must be removable without damaging the production schema.
Alternatives considered: Building with real unverified data from the start (rejected — risk of publishing inaccurate navigation).
```

---

## DEC-006

```
ID:          DEC-006
Date:        2026-09-16
Status:      ACCEPTED
Decision:    Each navigable physical location uses one primary arrival point (main entrance) in V1. Multiple entrances are deferred.
Context:     Routing needs a consistent arrival point per destination.
Reason:      One entrance per location is sufficient for V1 navigation. Multiple entrance support adds complexity without proportional benefit at this stage.
Consequences: Some large buildings may have a non-optimal entrance for certain approaches. This is acceptable in V1.
Alternatives considered: Multiple entrances from V1 (deferred).
```

**Supersession addendum — 2026-09-18:** This historical decision is superseded for Phase 4 and V1 campus-data design by the owner-approved [`../phase4/CAMPUS_DATA_AND_EDITOR_SPEC.md`](../phase4/CAMPUS_DATA_AND_EDITOR_SPEC.md). Outdoor places must support multiple named entrances while retaining one primary/default routing entrance. The original record remains above to preserve decision history.

---

## DEC-007

```
ID:          DEC-007
Date:        2026-09-16
Status:      ACCEPTED
Decision:    Path distances are calculated from geographic geometry, not manually entered.
Context:     Routing required a decision on how distance is determined.
Reason:      Manual entry of distances is error-prone, unscalable and inconsistent. Geographic calculation from path geometry is accurate and automatic.
Consequences: Path geometry must be correct for routing distances to be accurate. Field verification of paths is important.
Alternatives considered: Manual distance entry (rejected — error-prone and unscalable).
```

---

## DEC-008

```
ID:          DEC-008
Date:        2026-09-16
Status:      ACCEPTED
Decision:    YCT Map maintains its own campus-specific data layer. Missing paths or locations can be represented without requiring upstream OSM edits.
Context:     OpenStreetMap campus coverage for YabaTech is incomplete.
Reason:      Waiting for OSM contributors to improve campus data would block the project. YCT Map must be able to represent campus reality independently.
Consequences: YCT Map has its own data layer on top of OSM base tiles. OSM is used for geographic context only, not as the source of campus accuracy.
Alternatives considered: Relying solely on OSM data (rejected — insufficient campus coverage).
```

---

## DEC-T01

```
ID:          DEC-T01
Date:        2026-09-16
Status:      ACCEPTED
Decision:    Mobile-first responsive web interface built with modern HTML5, CSS, and modular JavaScript, using MapLibre GL JS for interactive mapping.
Context:     The public map and editor interfaces require a lightweight, high-performance UI layer targeting ordinary student smartphones with limited mobile data and battery sensitivity.
Reason:      Avoiding heavy Single-Page Application (SPA) framework overhead ensures fast initial load times, low data consumption, and optimal responsiveness on mobile browsers. MapLibre GL JS provides open-source, hardware-accelerated vector and raster map rendering, smooth camera transitions, and lightweight visual depth without vendor lock-in.
Consequences: UI components and map interactions remain lightweight, modular, and cleanly integrated with the backend without client-side bundle bloat.
Alternatives considered: Heavy SPA frameworks like React/Next.js (rejected for V1 due to unnecessary bundle overhead, complexity, and high data consumption on entry-level student phones).
```

---

## DEC-T02

```
ID:          DEC-T02
Date:        2026-09-16
Status:      ACCEPTED
Decision:    Python / Django as the primary server-side application framework.
Context:     A reliable, secure server framework is required to manage business logic, campus data models, REST API endpoints, moderation queues, and trusted user access.
Reason:      Django provides a battle-tested ORM, administrative capability, robust authentication, session management, built-in CSRF/XSS protections, and straightforward API integration. It enables rapid, secure development and matches the approved V1 technical plan.
Consequences: Backend business logic, database migrations, authentication, and moderation workflows are unified under a well-structured Python/Django application.
Alternatives considered: Node.js / Express or FastAPI (rejected — Django includes ready-to-use administrative tooling, robust ORM, and integrated auth, significantly reducing custom infrastructure code).
```

---

## DEC-T03

```
ID:          DEC-T03
Date:        2026-09-16
Status:      ACCEPTED
Decision:    Managed PostgreSQL service, with Neon as the primary preferred provider and Supabase as a validated compatible alternative.
Context:     Persistent storage is required for campus physical destinations, internal locations, walkable paths, verification states, and public contributions.
Reason:      PostgreSQL is the industry standard for relational data and spatial geometry. Neon provides serverless, managed PostgreSQL with branching, automated backups, and low operational overhead. Supabase remains a fully compatible alternative if future requirements dictate.
Consequences: The data model leverages native PostgreSQL capabilities (UUIDs, JSONB fields, spatial operations). Standard connection configuration is managed via `DATABASE_URL`.
Alternatives considered: SQLite (unsuitable for concurrent multi-user production deployment), MySQL (inferior spatial and JSON capabilities compared to PostgreSQL).
```

---

## DEC-T04

```
ID:          DEC-T04
Date:        2026-09-16
Status:      ACCEPTED
Decision:    OpenStreetMap-derived tiles rendered via MapLibre GL JS using open/free tile styles as the base geographic context.
Context:     YCT Map requires an underlying base canvas representing surrounding roads, landmarks, and geographic context.
Reason:      OpenStreetMap-derived tiles provide open base geographic context with no prohibitive licensing costs or strict proprietary limits. YCT Map renders its own independent campus data layer on top of this base canvas, ensuring campus accuracy and completeness are never blocked by upstream OSM edits.
Consequences: Base map tiles provide orientation, while YCT Map's custom GeoJSON layer delivers verified campus buildings, arrival points, and paths.
Alternatives considered: Google Maps API (rejected — restrictive licensing, ongoing costs, difficulty overlaying independent walkable routing networks), Mapbox proprietary tiles (avoided to eliminate commercial licensing constraints and API key credit limits).
```

---

## DEC-T05

```
ID:          DEC-T05
Date:        2026-09-16
Status:      ACCEPTED
Decision:    Campus network graph routing using shortest-path graph algorithms (Dijkstra / A*) operating over YCT Map's connected walkable path linestring geometry.
Context:     Pedestrian navigation is confined strictly to YabaTech campus boundaries and must calculate routes and distances from verified walkable paths.
Reason:      Campus walking paths are distinct from municipal road networks. A campus-specific graph model where path segments and destination arrival points form connected nodes enables precise pedestrian routing, automatic geographic distance calculation (along path coordinates), and estimated walking time (default walking speed 1.35 m/s). External routing engines lack YabaTech pedestrian path data and add unnecessary infrastructure overhead.
Consequences: YCT Map maintains complete control over campus routability, walkable shortcuts, and inaccessible barrier bypasses.
Alternatives considered: External public routing APIs (rejected — no internal campus pedestrian path data), heavy self-hosted OSRM/Valhalla instance (rejected — excessive server overhead for a single campus).
```

---

## DEC-T06

```
ID:          DEC-T06
Date:        2026-09-16
Status:      ACCEPTED
Decision:    Django's built-in authentication system (`django.contrib.auth`) for trusted editors and administrators. Normal users require no authentication.
Context:     Editors require authenticated access to manage campus data, moderate contributions, and verify locations. Public users (students, staff, visitors) require no accounts.
Reason:      Django provides battle-tested password hashing (PBKDF2/Argon2), session/token management, role-based permissions (Admin vs. Editor), and CSRF protection out of the box with zero external dependencies or subscription costs.
Consequences: No third-party authentication vendor dependencies. Minimal PII stored. Unauthenticated public access for student navigation and contributions is fully preserved.
Alternatives considered: Third-party OAuth/Auth0 (rejected — unnecessary external dependency, cost, and complexity for a small team of campus editors), Student account registration (explicit non-goal for V1).
```

---

## DEC-T07

```
ID:          DEC-T07
Date:        2026-09-16
Status:      ACCEPTED
Decision:    Render for hosting the web application, connected to managed PostgreSQL (Neon).
Context:     A reliable, cost-effective hosting environment is required to run the web application with automated GitHub continuous deployment.
Reason:      Render provides native Python/Django web service support, automatic SSL/TLS, Git integration, environment variable management, and straightforward scaling, matching the approved V1 technical and commercial plan.
Consequences: Deployment is triggered from the production branch via GitHub. Database runs independently on Neon.
Alternatives considered: Self-managed VPS (DigitalOcean/AWS EC2 — rejected due to maintenance overhead for the student group), Heroku (rejected due to pricing and lack of free tier).
```

---

## DEC-T08

```
ID:          DEC-T08
Date:        2026-09-16
Status:      ACCEPTED
Decision:    Use Render's provided platform subdomain (e.g., `yctmap.onrender.com`) for V1 staging and initial deployment, with custom project/institutional domain configuration (e.g., `yctmap.ng` or institution-assigned subdomain) supported via DNS alias when acquired by the group.
Context:     The application must be deployable and testable immediately without waiting for domain purchase or institutional DNS delegation.
Reason:      Render subdomains come with automated SSL and zero setup friction. This allows immediate testing on student devices while leaving custom domain setup as an administrative configuration step upon formal launch or handover.
Consequences: Development and verification are never blocked by domain registration. The platform URL can be updated seamlessly via DNS CNAME when ready.
Alternatives considered: Delaying deployment until a custom institutional domain is registered (rejected — blocks deployment testing and Phase 1–4 validation).
```

---

## DEC-T09

```
ID:          DEC-T09
Date:        2026-09-16
Status:      ACCEPTED
Decision:    Admin-managed, invite-only account creation. Administrators create and assign trusted editor accounts directly.
Context:     A model was needed for onboarding campus editors while protecting campus data integrity.
Reason:      Editor access grants permissions to modify verified locations, paths, and moderation statuses. Allowing open self-registration introduces security and vandalism risks. A curated, admin-controlled list of trusted project members is sufficient and appropriate for V1.
Consequences: No public registration endpoint for editors. Admins provision accounts via Django admin or management command.
Alternatives considered: Open editor registration with email confirmation (rejected — risk of unauthorized edits or spam), Public student accounts (rejected — explicit V1 non-goal).
```

---

## DEC-T10

```
ID:          DEC-T10
Date:        2026-09-16
Status:      ACCEPTED
Decision:    Server-side validation and rate limiting as the initial V1 approach for contributions. Stronger anti-abuse measures (e.g., CAPTCHA) are deferred unless actual abuse or testing demonstrates a need.
Context:     Public students can submit location additions and corrections without creating an account. A mitigation strategy is needed to prevent spam and submission abuse without adding unnecessary friction.
Reason:      All public submissions enter a moderation queue (DEC-003) and are never published directly to the map, inherently isolating unverified submissions from the public experience. Strict server-side payload validation (field length limits, required fields, coordinate boundary checks within YabaTech geographic bounds) and IP-based rate limiting provide sufficient protection for V1 while keeping student contributions frictionless on mobile devices.
Consequences: Normal students experience zero friction (no CAPTCHA hurdles). The moderation queue remains protected from automated flood scripts. If abuse is observed in testing or production, Cloudflare Turnstile or reCAPTCHA can be introduced without altering data models.
Alternatives considered: Mandatory CAPTCHA for all submissions from day 1 (deferred — introduces user friction on mobile devices), Requiring student accounts to contribute (rejected — contradicts DEC-002 and V1 scope).
```

---

## DEC-T11

```
ID:          DEC-T11
Date:        2026-09-17
Status:      ACCEPTED
Decision:    Use OpenFreeMap as the initial V1 base-map style/tile service with its official Liberty style (`https://tiles.openfreemap.org/styles/liberty`).
Context:     DEC-T04 approved MapLibre GL JS and open, OSM-derived base tiles but did not identify the initial concrete service and style.
Reason:      OpenFreeMap supplies a directly usable open map style for the lightweight MapLibre foundation without coupling YCT Map's campus-specific data to a proprietary provider.
Consequences: The base-map provider must remain reasonably replaceable. YCT Map campus data stays in an independent application-owned layer.
Alternatives considered: Leaving the concrete provider unresolved (rejected — Phase 1 requires an implementable map foundation).
```

---

## DEC-T12

```
ID:          DEC-T12
Date:        2026-09-17
Status:      ACCEPTED
Decision:    Use OpenStreetMap way 671850885 as the trusted source for the initial YabaTech viewport, with approximate centre latitude 6.51857 and longitude 3.37424 (MapLibre order `[3.37424, 6.51857]`).
Context:     Phase 1 requires an initial campus viewport without inventing or falsely verifying YabaTech campus data.
Reason:      The existing OSM campus object provides a traceable geographic source suitable for viewport framing.
Consequences: The coordinates authorize viewport positioning only. They do not verify individual campus locations, entrances, paths, floors or building geometry. Retain or derive viewport information from the OSM campus geometry where practical.
Alternatives considered: Guessing a centre point (rejected — violates campus-data integrity rules).
```

---

## DEC-T13

```
ID:          DEC-T13
Date:        2026-09-17
Status:      ACCEPTED
Decision:    Phase 1 uses explicitly synthetic demonstration locations, unmistakably marked with the DEMO verification/data state, positioned within the initial viewport solely to demonstrate product behaviour.
Context:     Search, selection and destination panels require data before verified real YabaTech location data is available.
Reason:      Synthetic records allow software verification without representing invented campus facts as real or verified.
Consequences: Demo records must be replaceable or removable without changing the production data model. Names must be visibly prefixed or otherwise labelled as DEMO.
Alternatives considered: Invented records using real campus names (rejected — risks misleading users and violating campus-data rules).
```

---

## DEC-T14

```
ID:          DEC-T14
Date:        2026-09-17
Status:      ACCEPTED
Decision:    Use 1.35 m/s as the default walking-speed assumption for approximate walking ETA.
Context:     The earlier planning text referenced approximately 1.2 m/s and required correction before routing implementation.
Reason:      The owner selected 1.35 m/s as the current default assumption.
Consequences: ETA must be presented as approximate. This routing assumption does not add routing to Phase 1 scope.
Alternatives considered: Retaining 1.2 m/s (superseded by owner decision).
```

---

## DEC-T15

```
ID:          DEC-T15
Date:        2026-09-17
Status:      ACCEPTED
Decision:    YCT Map maintains its own campus-specific application data layer. Changes inside YCT Map do not automatically modify or synchronize back to OpenStreetMap.
Context:     The base map and the approved campus-orientation outline use published OpenStreetMap geography, while destinations, aliases, entrances, internal locations, walkable paths, verification states and editor corrections belong to YCT Map.
Reason:      Automatic write-back would blur data ownership, bypass deliberate verification and create an unsafe dependency between local editor actions and a public geographic database.
Consequences: YCT Map may deliberately review and refresh OSM-derived reference geometry, but any contribution of verified public geography to OpenStreetMap must be a separate, intentional OSM editing workflow. No automatic OSM write-back or synchronization is permitted.
Alternatives considered: Automatic two-way synchronization (rejected — unsafe and outside project scope), treating all visible base-map features as YCT Map-verified data (rejected — violates verification rules).
```

---

## DEC-T16

```
ID:          DEC-T16
Date:        2026-09-18
Status:      ACCEPTED
Decision:    Static/manual route origins use a clear non-GPS start marker; destinations use a clear red destination indicator. Directional triangle/chevron and heading presentation are reserved for reliable future live geolocation/heading data.
Context:     Sprint 002 proved route calculation but owner review identified a need for clearer endpoint presentation in Sprint 003.
Reason:      A static point must not imply live position, movement or device orientation that the application does not possess.
Consequences: Sprint 003 must visually distinguish static start, destination and calculated route. Phase 3 may add directional live-position presentation only with reliable data.
Alternatives considered: Reusing a GPS-style marker for manual origins (rejected — misleading), always showing heading (rejected — invents unavailable orientation).
```

---

## DEC-T17

```
ID:          DEC-T17
Date:        2026-09-18
Status:      ACCEPTED
Decision:    OSM/OpenFreeMap-visible pathways may be mapping reference input, but YCT Map must own explicit routing graph geometry; editor review and field verification remain separate. Future validation flags ordinary outdoor path/building intersections with deliberate exceptions for real passages.
Context:     Synthetic routing proved the software while highlighting the future cost of constructing accurate campus topology.
Reason:      Reusing suitable published reference information reduces unnecessary redrawing without treating rendered cartography as verified routing data.
Consequences: Import/construction must create explicit editable YCT Map records. Missing or incorrect paths remain correctable, Path Survey Mode may refine evidence, and footprint-intersection warnings require human review rather than unconditional rejection.
Alternatives considered: Route directly over rendered base-map paths (rejected — no project ownership or verification), redraw every path without reference (rejected — unnecessary work), reject every footprint intersection (rejected — would exclude genuine passages/corridors).
```

---

## DEC-T18

```
ID:          DEC-T18
Date:        2026-09-18
Status:      ACCEPTED
Decision:    The primary local development routing network is imported from a reviewed OSM/Overpass snapshot into YCT Map-owned WalkableNode and WalkableSegment records with preserved provenance and UNVERIFIED status. The original synthetic topology is retained only for deterministic tests.
Context:     The synthetic five-segment graph proved graph construction and A* correctly but produced geographically unrealistic routes during product review.
Reason:      A geographically plausible development graph permits meaningful UX review without claiming field verification or coupling route execution to rendered base-map tiles.
Consequences: Imported geometry remains editable, is never automatically FIELD_VERIFIED, and is not written back to OSM. Route quality still depends on later entrance review, access review and physical survey. Algorithm tests continue to use the small synthetic fixture for deterministic edge cases.
Alternatives considered: Keep synthetic geometry as the primary visual dataset (rejected as unsuitable for continued review), route directly against rendered tiles (rejected because tiles are presentation rather than owned graph data), mark imported OSM data FIELD_VERIFIED (rejected because no field survey occurred).
```
