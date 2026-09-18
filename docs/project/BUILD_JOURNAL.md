# YCT Map Build Journal

This journal is the student-facing technical learning record for YCT Map. It explains what the team built, how the parts work together, and why the implementation took its current form. It is separate from `operations/SPRINT_LOG.md`, which records operational sprint history and status.

Entries must be based on repository evidence, accepted decisions, test results, and Git history. A completed sprint entry is historical evidence: later entries may add context, but must not rewrite earlier work to make later architecture appear inevitable. Update this journal after every accepted sprint. Add a phase-level summary only when that phase is complete.

## Phase 1 — Sprint 001: Core Foundation and Initial Map Experience

**Recorded status:** OWNER VERIFIED / ACCEPTED. A dedicated Sprint 001 milestone commit was authorized after owner verification.

**Acceptance addendum — 2026-09-17:** The owner subsequently verified and accepted Sprint 001 and authorized its dedicated milestone commit. Statements below that explicitly say “at reconstruction time” preserve the factual sequence in which this journal entry was first assembled; they are not the current sprint status.

### Purpose

Sprint 001 established the smallest useful end-to-end foundation for YCT Map. It proved that a Django application could store campus-style destinations, expose a deliberately limited public data contract, and support a mobile-first map and search experience in the browser.

This sprint was not intended to prove routing, live navigation, field-verified campus data, or production deployment. Its purpose was to create a sound base for those later capabilities.

### User Outcome

A user can open the application directly into the map experience, see explicitly synthetic destinations in the YabaTech viewport, search by destination name or alias, filter by category, choose a result or marker, and inspect a destination card.

Every Sprint 001 destination is labelled `DEMO`, and the interface explains that the records are synthetic rather than verified campus information.

### Starting State

The repository began Sprint 001 at pre-build baseline commit `1bce21c` (`chore: establish YCT Map pre-build baseline`). It contained approved product, technical, governance, and operational documentation, but no Django project or application implementation.

The owner had approved these constraints:

- Django on the server and Django templates in the browser.
- SQLite for Sprint 001 local development, with ordinary Django ORM usage compatible with a later PostgreSQL move.
- MapLibre GL JS with the OpenFreeMap Liberty style.
- Native modular JavaScript with pinned CDN assets and no Node/npm build pipeline or SPA framework.
- Minimal persisted `Location` and `LocationAlias` models.
- Synthetic fixture data, visibly marked `DEMO`, rather than invented real YabaTech facts.
- OpenStreetMap campus object `way 671850885` as the source for the initial viewport, centred approximately at longitude `3.37424`, latitude `6.51857`.
- No routing, ETA, live GPS, contribution workflow, editor, detailed 3D work, field verification, or production deployment in this sprint.

### What We Built

- A Django 5.2 LTS project and a `locations` application.
- Persisted `Location` and `LocationAlias` models with an initial migration.
- A repeatable JSON fixture containing six synthetic destinations and four aliases.
- A small, explicit GeoJSON endpoint at `GET /api/locations/`.
- Server-rendered map-page configuration.
- A MapLibre map using the OpenFreeMap Liberty style.
- Search by case-insensitive partial name and alias, plus category filtering.
- Synchronized list and map selection.
- A mobile destination bottom sheet that becomes a destination card on wider screens.
- Clear demonstration-data labels, empty states, loading states, and map failure handling.
- Automated model, endpoint, fixture, and page tests, plus static and browser checks.

### Technical Concepts Introduced

**Layered web architecture.** Django handles persistence, validation, URLs, and the public endpoint. The browser handles interaction and presentation. The two sides communicate through an explicit contract.

**Relational modelling.** A destination is stored once as a `Location`. Alternative searchable names are separate `LocationAlias` rows linked through a foreign key. This avoids numbered alias columns and allows any location to have zero or more aliases.

**Controlled domain values.** Categories and verification states use Django `TextChoices`. This limits stored values to project-defined meanings such as `library` or `DEMO`, instead of accepting inconsistent arbitrary strings.

**Fixture data.** Demonstration records live in an explicitly loaded JSON fixture, not inside a schema migration. A migration defines database structure; a fixture supplies replaceable example content. Removing demo content therefore does not require undoing the production schema.

**API contracts and serialization.** The endpoint does not expose an entire Django model automatically. It constructs only the fields needed by the map and search interface. This protects internal fields and makes the public response predictable and testable.

**GeoJSON.** Locations are returned as a GeoJSON `FeatureCollection`. Every destination is a `Feature` with point geometry and selected properties. GeoJSON orders a point as `[longitude, latitude]`, which is why the YabaTech centre is written as `[3.37424, 6.51857]`.

**Progressive resilience.** Destination data and search are initialized independently of the external map style. If the map library or tile style cannot load, users can still search and select destinations where practical.

**Responsive and accessible interaction.** The same destination component acts as a bottom sheet on a phone and a card on a larger screen. Native buttons, visible focus states, keyboard movement into results, focus restoration, and reduced-motion handling improve keyboard and motion-sensitive use.

### How It Works Internally

When the map page is requested, Django renders a template containing safe configuration values: the API URL, map centre, style URL, MapLibre version, and allowed categories. The browser reads that configuration instead of duplicating it across JavaScript files.

The browser requests the destination collection. Django queries active `Location` rows, prefetches aliases, applies any validated query or category filter, and serializes the result into GeoJSON. The initial browser request loads the full active demo collection. Search and category interactions then filter that in-memory collection, giving immediate feedback without a server request on every keystroke. The endpoint still supports server-side `q` and `category` parameters as an independently testable contract.

The application passes filtered features to both the results list and MapLibre GeoJSON source. Selecting a result or marker updates one shared selection state: the map may move to the point, and the destination panel displays its explicit properties. Camera movement is non-essential so reduced-motion preferences can take effect.

The base map and YCT Map data remain separate. OpenFreeMap supplies geographic context and styling; the Django endpoint supplies the project's destination layer. Changing the base-map provider should not require changing `Location` records.

### Architecture / Components Involved

```text
                        server-rendered configuration
Browser  <------------------------------------------------  Django map view
   |
   | GET /api/locations/
   v
Django URL -> location_collection view -> Django ORM -> SQLite
   ^                    |
   |                    v
   +------------- explicit GeoJSON FeatureCollection

In the browser:

GeoJSON -> search/category filter -> results list
                            |-----> MapLibre destination layer
                            `-----> selected destination panel

MapLibre --------------------------> OpenFreeMap Liberty base map
YCT Map destination data ----------> Django API (kept separate)
```

The principal components are:

- **Django project configuration (`yctmap`)** — settings, root URL routing, and deployment entry points.
- **Locations application (`locations`)** — models, API and page views, URLs, migrations, fixtures, and tests.
- **Django template** — semantic page structure and the configuration bridge between server and browser.
- **JavaScript modules** — API access, application coordination, search, map behavior, and destination-panel behavior.
- **CSS** — mobile-first layout, responsive card/sheet behavior, state styling, accessibility, and map overlays.
- **SQLite** — Sprint 001 local persistence.
- **MapLibre/OpenFreeMap** — map renderer and replaceable base-map style service.

### Important Files

- `manage.py` — Django's project command entry point.
- `yctmap/settings.py` — installed apps, SQLite, templates, static files, and environment-sensitive settings.
- `yctmap/urls.py` — root URL routing.
- `locations/models.py` — `Location`, `LocationAlias`, controlled categories, and verification states.
- `locations/migrations/0001_initial.py` — initial relational schema.
- `locations/fixtures/demo_locations.json` — six synthetic locations and four aliases.
- `locations/views.py` — page rendering, input validation, ORM filtering, and explicit GeoJSON serialization.
- `locations/urls.py` — map and public endpoint routes.
- `locations/tests/test_locations.py` — model, endpoint, fixture, and page-contract tests.
- `templates/map/index.html` — map-first interface and server-provided configuration.
- `static/yct_map/js/app.js` — browser application coordinator.
- `static/yct_map/js/api.js` — endpoint request and response-shape validation.
- `static/yct_map/js/search.js` — client-side name/alias search, category filters, and keyboard behavior.
- `static/yct_map/js/map.js` — MapLibre loading, layers, marker interaction, and camera movement.
- `static/yct_map/js/destination-panel.js` — selection details and focus restoration.
- `static/yct_map/css/app.css` — responsive presentation and interaction states.

### Data Flow

```text
1. Browser requests /
2. Django renders index.html + configuration
3. app.js requests GET /api/locations/
4. View reads active Location rows and aliases from SQLite
5. View returns a small GeoJSON FeatureCollection
6. Browser stores the collection in memory
7. Search/category input produces a filtered collection
8. Filtered collection updates both list results and map source
9. User selects a result or marker
10. Selection updates the map camera and destination panel
```

For a server-filtered request such as `/api/locations/?q=reading&category=library`, the view validates inputs and builds an ORM query. Name matching is case-insensitive and partial. Alias matching follows the relation to `LocationAlias`. Results are made distinct so a location is not repeated when more than one joined alias matches.

### Decisions and Trade-offs

**Persisted models instead of a static JavaScript array.** This introduced migrations and fixture loading, but proved the real server-to-database-to-browser path and avoided a disposable frontend-only design.

**SQLite now, PostgreSQL compatibility later.** SQLite makes student and local setup small. The models use portable Django fields rather than database-specific SQL. This does not make SQLite the final production database.

**Decimal coordinates instead of GeoDjango/PostGIS.** Point coordinates and validation are sufficient for Sprint 001. Spatial routing, polygon queries, and path analysis may justify spatial infrastructure later; adding it now would not serve the approved flow.

**A separate alias table.** It adds one relationship but gives search a normalized structure and avoids mixing alternate names into one unstructured field.

**Explicit serialization instead of automatic model dumping.** More code is written in the view, but the endpoint remains intentionally small. Internal timestamps and other model details are not leaked simply because they exist.

**Native modules and pinned CDN assets instead of npm or a SPA.** This keeps the first frontend understandable and removes a build-tool layer. The trade-off is runtime reliance on external CDN services and fewer bundling or offline capabilities.

**Load once and filter in the browser.** This is responsive for six records and supports map-style failure resilience. A much larger dataset may later require indexed server search, caching, pagination, or different synchronization.

**No directions control.** A directions action would suggest routing exists when it does not. Omitting it protects the product boundary.

**Synthetic data separated from real campus claims.** The records demonstrate software behavior without pretending to verify real buildings, entrances, paths, or coordinates. This is both a data-quality decision and an engineering constraint.

### Problems Encountered

Only problems supported by the build and verification record are listed:

- The available sandbox Python installation did not include the standard `venv` module, and Django was not initially installed.
- The embedded Python distribution did not automatically import locally installed packages or the repository root, causing successive `No module named django` and `No module named yctmap` errors.
- Dependency download was initially blocked by restricted network access.
- The first browser pass requested a missing favicon and produced a 404.
- Initial map movement was marked essential, which would prevent MapLibre from suppressing that animation for users who prefer reduced motion.
- One background server-launch wrapper did not return cleanly even though Django itself had started.

No evidence was found of a domain-model or application-logic defect during the final test run.

### How We Solved Them

- Django was installed into a Git-ignored workspace-local package directory rather than changing global Python state.
- A Git-ignored local runner added that package directory and the repository root to `sys.path`. This was an environment-specific verification aid; the documented setup remains a conventional virtual environment.
- Dependency installation was retried with the required approved network permission.
- A project favicon was added and linked from the page, removing the browser 404.
- Map camera movement was changed to non-essential so reduced-motion settings can take effect.
- The local service was verified directly in the browser rather than treating the wrapper's behavior as an application failure.

The local Python runner is not part of the application architecture and must not be presented as a production requirement.

### Testing and Verification

The final automated suite contained 12 passing tests. It verified:

- model creation and the alias relationship;
- rejection of uncontrolled category values during model validation;
- coordinate validation;
- explicit endpoint properties, including exclusion of internal `created_at` data;
- case-insensitive partial destination-name search;
- alias search;
- category filtering;
- empty-result behavior;
- rejection of invalid or overlong filters;
- the endpoint's read-only method boundary;
- required map-page configuration; and
- exactly six fixture locations, all with `DEMO` names and verification state.

Additional checks confirmed valid Django configuration, no missing migrations, successful Python compilation, and valid JavaScript module syntax.

The local application was exercised at desktop and mobile viewport sizes. Verification covered initial loading, alias search, category filtering, destination selection, the selected `DEMO — Library` card, keyboard movement into results, visible focus, reduced-motion handling, absence of horizontal overflow, and a clean browser console after the favicon correction.

Technical verification is not sprint acceptance. At reconstruction time, owner acceptance, final evidence capture, and a Sprint 001 commit were still recorded as pending.

### Current Limitations

- All destinations are synthetic; there is no field-verified campus population.
- The YabaTech coordinates establish an initial viewport only, not verified individual locations.
- There is no walking route, distance, ETA, GPS, rerouting, or navigation guidance.
- There are no contribution, moderation, or editor workflows.
- SQLite and current settings support local development, not production deployment.
- Map rendering depends on external CDN services. Search/list behavior is designed to remain useful when map loading fails cleanly.
- Client-side filtering suits the current small dataset but has not been proven at production scale.
- The API is a small read-only contract, not a versioned general-purpose platform API.
- At the time of the original reconstruction, Sprint 001 had not yet been committed; owner verification, acceptance and milestone-commit authorization followed afterward.

### Evidence

The approved Sprint 001 evidence references are:

- **`P1-S1-A-initial-map-campus-view.png`** — demonstrates the map-first opening experience in the YabaTech viewport: base map, synthetic destination layer, search and category controls, and visible `DEMO` status. It establishes that a user reaches the core map rather than an unnecessary landing page.
- **`P1-S1-D-selected-destination-card.png`** — demonstrates the completed selection flow: the map and interface agree on a chosen destination, and the responsive card exposes its category, description, and `DEMO` state without claiming verified campus data.

The image binaries were not present in the repository during this reconstruction. These descriptions are based on the approved evidence names, their required purpose, and browser-verified application behavior; the journal does not claim a new visual inspection of those exact files.

### What Students Should Understand

Students should be able to explain the complete request path:

1. Django renders the page and configuration.
2. JavaScript requests an explicit data contract.
3. The view uses the ORM to query relational data.
4. GeoJSON carries only public map properties back to the browser.
5. Browser modules filter and present that data in a list, map layer, and destination panel.

They should understand why a base map is not the same as YCT Map's data. OpenFreeMap provides cartographic context. YCT Map owns destination records, verification states, search behavior, and interaction. Keeping these concerns separate makes the provider replaceable and prevents external map content from silently becoming project-verified truth.

Students should also defend the scope: a minimal, tested vertical slice is more valuable than unverified places or pretend routing. Sprint 001 proves architecture and interaction while preserving clear boundaries for later work.

### Presentation / Defence Notes

- **Why Django?** It provides routing, templates, ORM persistence, migrations, validation, testing, and a future path to built-in administration and authentication in one server framework.
- **Why SQLite if PostgreSQL is planned?** SQLite lowers local setup cost. Portable ORM models preserve a migration path; production database selection is later work.
- **Why GeoJSON?** It is understood by mapping libraries and separates geometry from properties. Its coordinate order is `[longitude, latitude]`.
- **Why `LocationAlias`?** Aliases form a one-to-many relationship. A separate table keeps them normalized and searchable.
- **Why selected endpoint fields only?** A stable API exposes what its consumer needs rather than accidentally mirroring the database.
- **Why `DEMO` everywhere?** This sprint verifies software, not campus facts. Field verification is a separate evidence process.
- **Why can search survive map-style failure?** Destination loading and search are initialized separately from the external renderer.
- **Why no routing?** It was outside scope and requires verified paths plus a routing design. A non-functional control would misrepresent capability.
- **What proves it works?** Model/API/page tests, framework and syntax checks, desktop/mobile browser verification, and milestone screenshots cover structure, behavior, and visible outcome.

For a demonstration, show the initial map, search with an alias such as `Reading Room`, apply a category filter, select the result, and point out the `DEMO` state. Then trace that action backwards through `search.js`, the GeoJSON response, the Django view, and the two models.

### Next Sprint

Owner review and acceptance of Sprint 001 are complete. The next approved task is Phase 1 Sprint 002 — Campus Orientation, UX Refinement & Phase 1 Completion. Its discussion/planning brief is approved, but implementation must wait for the standalone `BUILD` command.

When Sprint 002 is implemented, tested and owner accepted, append its learning record without rewriting this Sprint 001 history.

Phase 1 is still in progress, so no Phase 1 completion summary is included. When the phase is formally completed, add a summary covering achievements, resulting architecture, major concepts learned, important problems and solutions, evidence, current capabilities, and transition to the next phase.

## Phase 1 — Sprint 002: Campus Orientation, UX Refinement & Phase 1 Completion

**Recorded status:** OWNER VERIFIED / ACCEPTED. This sprint completed Phase 1 with one approved cosmetic carryover for Phase 2.

### Purpose

Sprint 001 proved that YCT Map could display and search destinations. Sprint 002 addressed a different problem: a map can be technically centred on a campus without making the campus immediately understandable to a user.

Owner testing showed that surrounding roads were valuable for geographic recognition, but wider views made the YabaTech campus itself harder to identify. Sprint 002 therefore improved orientation without cropping away the useful neighbourhood context or pretending that recognizable base-map buildings were field verified.

### User Outcome

A user opening YCT Map can identify the YabaTech campus through a subtle boundary and campus label while still seeing the surrounding road network. If the user pans or zooms away, an accessible control returns the map to the campus extent.

Category browsing now reveals matching destinations directly, selected destinations receive clearer marker feedback, and important mobile controls meet a reliable 44-pixel touch target. Search and textual destination details remain usable when the external map module or style is unavailable.

### Starting State

Sprint 002 began from accepted Sprint 001 commit `acb72ef`, which provided the Django application, six synthetic DEMO destinations, search, category filtering, MapLibre rendering, selection and responsive destination details.

The owner had observed that:

- surrounding streets helped users recognize the area;
- some base-map buildings looked recognizable, but their accuracy was not verified;
- wider zoom levels made the campus difficult to identify immediately.

OpenStreetMap way `671850885` was already approved as a trusted published source for campus-level viewport information. It did not authorize field verification of individual buildings, paths, gates or destinations.

### What We Built

- A version-controlled GeoJSON snapshot derived directly from OSM way `671850885`.
- Source, version, retrieval, licence and orientation-only metadata stored with the boundary.
- A low-opacity green campus fill and restrained outline.
- A project-controlled `YabaTech Campus` label.
- Geometry-derived initial framing using `fitBounds()`.
- An accessible “Return to YabaTech campus” map control.
- A selected-marker halo synchronized with the destination card.
- Category buttons that open their matching browse results.
- 44-pixel category, close and campus-focus touch targets.
- Automated boundary/configuration tests and expanded live-browser verification.
- Project rules separating YCT Map application data from OpenStreetMap editing.
- A deferred Path Survey Mode concept for later editor and field-verification phases.

### Technical Concepts Introduced

**Reference geometry versus verified application data.** The campus polygon is trusted for orientation because it comes from a traceable published OSM object. That does not make every feature visible inside it a verified YCT Map record.

**Map extent fitting.** A fixed centre and zoom assume one screen shape. `fitBounds()` calculates a camera view from the polygon’s minimum and maximum coordinates, then adds responsive padding for interface overlays.

**Layer composition.** The base map, orientation polygon, campus label, DEMO destinations and selection halo are separate MapLibre layers. Each has a distinct responsibility and can change without rewriting the others.

**Custom map controls.** The return-to-campus action implements MapLibre’s control interface while remaining an ordinary accessible button with an explicit label and touch target.

**Graceful degradation.** Search is initialized before the map. Destination selection always updates textual details and only asks the map to move when a map controller exists.

**Source provenance.** Geographic reference data includes where it came from, which source object/version was used, when it was retrieved and what claims it does—and does not—support.

### How It Works Internally

The Django template supplies the static campus-boundary URL alongside the existing map configuration. The browser loads destination GeoJSON and the local boundary GeoJSON independently from the external MapLibre module and OpenFreeMap style.

When MapLibre finishes loading, the application adds:

1. the campus fill;
2. the campus outline;
3. the campus text label;
4. the DEMO destination circles;
5. the selected-destination halo; and
6. destination text labels.

The polygon bounds are calculated from every coordinate. Initial framing and the campus-focus control both call the same `focusCampus()` behavior, so there is one definition of the intended campus view.

Selecting a destination stores its stable ID in a MapLibre filter. The halo layer uses that filter to render around only the selected marker. The destination panel continues to receive the same GeoJSON feature.

### Architecture / Components Involved

```text
Official OSM way 671850885
          |
          v
reviewed static GeoJSON snapshot
          |
          +----> boundary fill / outline
          +----> campus label
          `----> fitBounds / campus-focus control

Django location API ----> search/category state ----> destination layer
                                      |                    |
                                      +----> results       +----> selected halo
                                      `----> details panel

OpenFreeMap Liberty ----> geographic background and surrounding roads
```

The external base map remains replaceable. The campus reference overlay and YCT Map destination data are project-controlled layers above it.

### Important Files

- `static/yct_map/data/yabatech-campus-boundary.geojson` — reviewed campus reference geometry and provenance.
- `static/yct_map/js/map.js` — boundary layers, bounds calculation, custom focus control and selection halo.
- `static/yct_map/js/app.js` — boundary configuration passed into map creation.
- `static/yct_map/js/search.js` — category browsing behavior.
- `static/yct_map/css/app.css` — touch targets and campus-control presentation.
- `templates/map/index.html` — boundary asset URL exposed to JavaScript.
- `locations/tests/test_locations.py` — boundary provenance, geometry and page-configuration checks.
- `docs/project/operations/DECISIONS.md` — OSM/YCT Map ownership rule.
- `docs/project/operations/BACKLOG.md` — deferred Path Survey Mode.

### Data Flow

```text
Page request
  -> Django renders map configuration
  -> browser fetches DEMO locations
  -> browser fetches local campus boundary
  -> MapLibre loads OpenFreeMap style
  -> boundary and destinations become independent map sources
  -> polygon bounds set the initial camera

User selects category
  -> in-memory features are filtered
  -> results list opens
  -> destination map source updates

User selects destination
  -> details panel receives feature
  -> selected-ID filter updates halo
  -> map focuses destination when available
```

If MapLibre or the external style fails, the first data branch still succeeds. Search, results and textual destination details therefore remain useful.

### Decisions and Trade-offs

**Boundary plus label plus reset control.** Each solves a different orientation problem. The combination is more reliable than changing zoom alone, but the visual treatment remains restrained.

**Static reviewed snapshot instead of runtime OSM fetching.** A committed snapshot is reproducible and available without adding a runtime OSM dependency. Updates must be deliberately reviewed rather than silently synchronized.

**No hard map crop.** Users retain surrounding roads and approach context. YCT Map’s own destinations and future routing scope remain campus-focused even though the base map can show more geography.

**Polygon symbol label.** The initial implementation attached the label to the polygon. It worked at the overview scale but can repeat at close zoom. The owner accepted this as a cosmetic carryover; a deterministic point label is the first approved Phase 2 correction.

**Client search preserved during map failure.** Maintaining a separate discovery path adds state coordination, but prevents an external style failure from removing locally available destination information.

### Problems Encountered

- The standard PowerShell web client could not resolve the official OSM API host in the restricted build environment.
- An older Sprint 001 server process initially remained on port 8000, so the first page probe served the previous template.
- The preferred in-app browser connection was unavailable.
- The first isolated browser pass intentionally lacked external-map network access and exercised the failure path instead of the successful map path.
- Owner review later identified repeated campus-label placement at close zoom.

### How We Solved Them

- The official OSM way was retrieved read-only through an alternate permitted client, then its ordered node coordinates were converted directly without guessing geometry.
- The exact old local server process was identified and replaced rather than broadly terminating unrelated processes.
- An isolated hidden Chrome profile was used for live verification.
- The restricted pass became useful graceful-degradation evidence; a later approved-network pass verified MapLibre and OpenFreeMap rendering with software WebGL.
- The repeated label is documented as a LOW-severity cosmetic carryover with a narrow deterministic-point fix approved for Phase 2.

### Testing and Verification

The Django suite increased from 12 to 13 passing tests. The additional coverage verifies that:

- the template exposes the boundary asset;
- the file is a GeoJSON `FeatureCollection`;
- its source identifies OSM way `671850885`;
- its geometry is a closed polygon;
- it is explicitly an orientation boundary; and
- it does not claim a destination verification state.

System checks, migration-drift checks, Python compilation, JavaScript syntax checks and JSON parsing passed.

Live verification covered desktop and 390 × 844 mobile layouts, campus framing, surrounding roads, the focus control, category browsing, destination selection, selected-marker feedback, 44-pixel targets, keyboard focus, reduced motion, horizontal overflow and the successful-map console. Separate forced failures of the MapLibre module and OpenFreeMap style confirmed that search and textual details remain usable.

### Current Limitations

- The campus polygon is an orientation reference, not field-verified YCT Map geometry.
- All destinations remain synthetic DEMO records.
- The map still depends on external services for its rendered base geography.
- There is no routing, path network, distance, ETA, GPS or navigation result.
- Polygon-based campus text may repeat at close zoom; this is the documented Phase 2 carryover.
- No application change writes automatically to OpenStreetMap.

### Evidence

- **`P1-S2-A-campus-orientation.png`** — demonstrates the accepted campus overview with the subtle boundary, campus label, DEMO destinations and useful surrounding-road context.
- **`P1-S2-B-phase1-final-ux.png`** — demonstrates the accepted Phase 1 interaction quality across search/category discovery, destination selection and responsive details.

After the carryover correction, the selected-destination evidence should be replaced with **`P1-S2-B-phase1-final-ux-fixed.png`** so the retained Phase 1 evidence shows stable single-label behavior. No new Phase 1 recording is required.

### What Students Should Understand

Students should be able to distinguish three kinds of information on the screen:

1. OpenFreeMap/OSM-derived background geography for context.
2. An OSM-derived campus reference polygon used only for orientation.
3. YCT Map-owned DEMO destination records and interaction state.

They should understand that visual recognition is not verification, that source provenance limits what a dataset can claim, and that a good map camera must account for both geographic bounds and interface overlays.

They should also be able to explain why resilient discovery is an architectural property: search survives because it does not depend on successful map initialization.

### Presentation / Defence Notes

- **Why not crop the map to the campus?** Nearby roads help users approach and recognize YabaTech. Navigation scope and visible base-map extent are separate concerns.
- **Why trust the boundary but not every building?** The boundary comes from one traceable published object approved for orientation. Individual features require separate YCT Map verification.
- **Why keep a local GeoJSON copy?** It creates a reproducible reviewed input and avoids runtime synchronization surprises.
- **Why use `fitBounds()`?** It frames the complete polygon responsively instead of assuming one zoom works on every screen.
- **Why does search still work when the map fails?** Destination loading and discovery are initialized before and independently of MapLibre.
- **Does editing YCT Map edit OSM?** No. OSM contribution would be a separate deliberate workflow.
- **What remains imperfect?** The polygon symbol can repeat at close zoom. The accepted fix is one dedicated label point, not a geometry change.

### Next Sprint

Phase 2 Sprint 001 — Walkable Network & Routing Foundation — is the next approved task. Its first implementation action will close the repeated-label carryover. It will then establish synthetic walkable nodes, path geometry, calculated segment length and an in-memory graph without implementing A* or route results.

Implementation must wait for the standalone `BUILD` command.

## Phase 1 Summary — Foundation & Map Experience

**Status:** OWNER ACCEPTED on 2026-09-17.

### Achievements

Phase 1 transformed the documentation-only repository into a runnable mobile-first campus map. It established Django persistence, an explicit GeoJSON contract, search and category discovery, responsive selection details, MapLibre rendering, campus orientation and graceful degradation.

### Resulting Architecture

```text
SQLite -> Django ORM -> explicit location GeoJSON -> browser modules
                                                   |-> search/results
                                                   |-> destination panel
                                                   `-> MapLibre DEMO layer

reviewed campus GeoJSON -> orientation layers / fitBounds / focus control
OpenFreeMap Liberty -----> replaceable background geography
```

The architecture separates persistence, public serialization, browser interaction, external base geography, orientation reference data and project-owned destination data.

### Major Concepts Learned

- Relational location and alias modelling.
- Controlled verification states.
- Explicit API contracts.
- GeoJSON coordinate ordering.
- Mobile-first responsive design.
- Accessible keyboard and touch interaction.
- Map source/layer composition.
- Geographic bounds and responsive camera fitting.
- Data provenance and verification scope.
- Graceful degradation around external services.

### Important Problems and Solutions

- Restricted Python tooling was handled with an isolated local runner rather than changing project architecture.
- Missing browser assets and reduced-motion behavior were corrected during Sprint 001 verification.
- Campus ambiguity was solved with a subtle trusted boundary, clear label, geometry-derived framing and reset control.
- Restricted external access was separated into intentional failure-path testing and an approved-network rendering pass.
- Repeated close-zoom label placement remains documented for a deterministic point-label correction.

### Evidence

Phase 1 evidence references are:

- `P1-S1-A-initial-map-campus-view.png`
- `P1-S1-D-selected-destination-card.png`
- `P1-S2-A-campus-orientation.png`
- `P1-S2-B-phase1-final-ux.png`

The last item will be replaced by `P1-S2-B-phase1-final-ux-fixed.png` after the cosmetic carryover is corrected.

### Current System Capabilities

Users can open the map, recognize the YabaTech campus area, retain surrounding-road context, return to the campus view, search synthetic destinations by name or alias, browse categories, select markers or results, and inspect responsive destination details. Search and details remain available when the external map cannot render.

The system does not yet calculate or display routes. No campus location or path has been field verified.

### Transition to Phase 2

Phase 2 will introduce YCT Map’s own synthetic walkable network, geometry-derived distance calculation, graph construction and later A* routing. Base-map roads will remain contextual and will not automatically become routable YCT Map paths.

## Phase 2 — Sprint 001: Walkable Network & Routing Foundation

**Recorded status:** OWNER VERIFIED / ACCEPTED on 2026-09-17.

### Purpose

Sprint 001 established the data and service foundation required before YCT Map can calculate routes. It introduced a project-owned walkable network, geometry-derived segment distance and an in-memory graph representation while deliberately excluding route selection. It also closed Phase 1’s cosmetic label carryover without changing the accepted base-map configuration or camera behavior.

### User Outcome

In development mode, a reviewer can inspect a purple dashed DEMO network and its junction nodes over the map, hide or show it, and see an explicit statement that no route has been calculated. Existing search, category browsing and destination selection continue to work.

This is a technical inspection outcome, not yet a directions feature. A user cannot choose endpoints or receive a route, total distance or ETA in this sprint.

### Starting State

Phase 1 was owner accepted at commit `602a0be` with a searchable map, six synthetic destinations, campus orientation and responsive destination details. It had no project-owned walkable-network tables, no graph and no routing service.

One accepted cosmetic carryover remained: the polygon-based `YabaTech Campus` symbol could repeat at close zoom. The owner required its correction as the first Phase 2 action. The owner also approved a persistent DEMO network using ordinary Django models and GeoJSON, with no GeoDjango/PostGIS requirement and no A* implementation in Sprint 001.

### What We Built

- `WalkableNode` and `WalkableSegment` Django models with UUID identities, controlled verification state and active state.
- Start/end node relationships, bidirectional direction state and GeoJSON `LineString` geometry for every segment.
- Geometry validation, endpoint anchoring and dynamic Haversine length calculation.
- A service that converts active database records into an immutable adjacency graph.
- Reverse graph arcs with reversed geometry for bidirectional segments.
- Diagnostics for malformed geometry, zero length, self-edges and exact duplicate or reverse-duplicate segments.
- An explicit fixture containing five synthetic DEMO nodes and five synthetic DEMO segments.
- A DEBUG-only GeoJSON inspection endpoint and dashed purple network layer with node circles and a visibility toggle.
- A deterministic point source for the single `YabaTech Campus` label while retaining the accepted polygon boundary and camera behavior.

### Technical Concepts Introduced

**Graph nodes and edges.** A graph represents a network as nodes connected by edges. In YCT Map, a node is a junction or endpoint where movement can begin, end or change direction. An edge is a walkable segment connecting two nodes. This structure lets a later algorithm compare possible sequences of connected segments.

**Persistence versus computation.** Django models store the editable network definition in the database. Routing algorithms should not repeatedly query relational rows while exploring paths, so the application converts those rows into an in-memory adjacency graph optimized for traversal.

**LineString geometry.** A GeoJSON `LineString` is an ordered list of `[longitude, latitude]` coordinate pairs. Two coordinates describe a straight line. Three or more can follow a bend or curve as a series of short straight legs.

**Geometry-derived weight.** Each graph edge needs a cost. Sprint 001 uses metres derived from the segment’s coordinates rather than a manually entered distance. This keeps the routing weight tied to the represented path.

**Directed arcs.** A persisted segment is one physical record, but graph traversal has direction. A bidirectional segment becomes one forward arc and one reverse arc. A future one-way segment will create only its allowed arc.

**Stable identity.** Node and segment UUIDs remain stable even when labels or geometry are edited. Future Path Survey Mode can associate observations, review history or replacement geometry with a specific segment without relying on a mutable name or list position.

### How It Works Internally

`WalkableNode` represents a network junction or endpoint with a coordinate. `WalkableSegment` references one start node and one end node and stores the detailed geometry between them. Model validation rejects a segment that connects a node to itself, has invalid or zero-length geometry, or does not begin and end at its selected nodes.

Distance calculation validates the LineString, then applies the Haversine formula to every consecutive pair. Haversine estimates the surface distance between two longitude/latitude coordinates on Earth. The individual leg distances are summed:

```text
[A, bend 1, bend 2, B]

distance = H(A, bend 1)
         + H(bend 1, bend 2)
         + H(bend 2, B)
```

Using only `H(A, B)` would cut across bends and underestimate a curved walking path.

The graph builder queries active nodes and active segments whose endpoints are also active. It creates an adjacency entry for every node. A segment from A to B produces an arc in A’s adjacency list containing the segment ID, B’s ID, calculated metres and ordered geometry. If it is bidirectional, B receives a second arc back to A with the same distance and reversed coordinate order.

### Architecture / Components Involved

```text
SQLite / Django ORM
        |
        | WalkableNode + WalkableSegment rows
        v
geometry validation -----> Haversine metres
        |
        v
graph builder ------------> adjacency graph in memory
        |                    A -> [B, D]
        |                    B -> [A, C]
        |
        `-> DEBUG GeoJSON endpoint -> dashed inspection layer

OpenFreeMap Liberty ----------------> geographic background only
YCT Map routing network ------------> project-owned traversal data
```

The base map and routing network are separate by design. OpenFreeMap supplies visual context such as streets, buildings and labels. YCT Map does not automatically treat visible base-map roads as walkable. Only project-owned `WalkableSegment` records enter the routing graph, because they can carry project verification state and later field evidence.

### Important Files

- `routing/models.py` — persisted nodes, segments, choices and model validation.
- `routing/geometry.py` — LineString validation, Haversine calculation and total length.
- `routing/graph.py` — immutable graph arcs and database-to-adjacency conversion.
- `routing/validators.py` — network diagnostics such as duplicate segments.
- `routing/views.py` and `routing/urls.py` — DEBUG-only inspection contract.
- `routing/migrations/0001_initial.py` — routing schema.
- `routing/fixtures/demo_walkable_network.json` — replaceable synthetic topology.
- `routing/tests/test_routing.py` — routing-foundation tests.
- `static/yct_map/js/map.js` — inspection layers, toggle behavior and deterministic campus label.
- `templates/map/index.html` and `static/yct_map/css/app.css` — inspection notice and presentation.

### Data Flow

```text
1. Fixture loads DEMO nodes and segments into SQLite.
2. Django ORM reads active network records.
3. Geometry service validates coordinates and derives metres.
4. Graph builder creates adjacency arcs for algorithm use.
5. DEBUG endpoint serializes active DEMO geometry for inspection.
6. Browser adds dashed segment and junction layers above the base map.
7. Toggle changes only inspection-layer visibility.
```

The purple network is the complete stored DEMO topology being inspected. It is not the output of a route algorithm. A calculated route would be a selected subset of segments connecting a requested origin and destination; Sprint 001 has no origin, destination or selection algorithm.

### Decisions and Trade-offs

**JSONField instead of GeoDjango/PostGIS.** GeoJSON is sufficient for a small foundation and keeps local SQLite setup simple. It does not provide spatial indexing or database-native geometry operations, which can be reconsidered when actual scale or queries justify them.

**Dynamic distance instead of a stored length column.** Recalculation prevents stale distance when geometry changes. It costs some computation, but the current DEMO network is small and correctness is more important than premature caching.

**One segment record, potentially two graph arcs.** This avoids duplicating persisted geometry for ordinary two-way paths while still giving the algorithm explicit traversal directions.

**DEBUG-only visualization.** Developers need to inspect topology, but presenting the purple network as a public route would be misleading. The endpoint is unavailable outside DEBUG and the interface explicitly says no route was calculated.

**Base map kept independent.** Automatically routing over every visible base-map path would bypass YCT Map’s verification rules. Separation costs later data-population work but preserves provenance and safety.

### Problems Encountered

- The accepted polygon label could repeat because symbol placement operated over polygon geometry.
- The integrated browser connection was unavailable during implementation verification, and the isolated browser did not complete the external OpenFreeMap style load.
- Owner review raised a concern that the current map might look less detailed than the accepted Phase 1 view.

No routing-model or graph defect was found in the accepted sprint.

### How We Solved Them

- The campus label was moved to one deterministic point source. The polygon remains responsible for boundary fill, outline and `fitBounds()`.
- Automated tests, local endpoint checks and isolated desktop/mobile rendering were completed; the owner later performed the required normal-browser visual verification.
- A read-only comparison against Phase 1 commit `602a0be` confirmed that the MapLibre version, Liberty style URL, zoom limits, camera fitting, boundary opacity and base-map CSS had not changed. The perceived detail difference was not caused by a Phase 2 base-map regression.

### Testing and Verification

All 23 Django tests passed at acceptance, including the 13 Phase 1 regression tests. Routing tests cover:

- DEMO-only fixture integrity;
- curved LineString length using every geometry leg;
- zero-length rejection;
- self-edge rejection;
- geometry endpoint anchoring;
- forward and reverse arcs for a bidirectional segment;
- exclusion of inactive segments;
- reverse-duplicate diagnostics;
- the explicit DEBUG endpoint contract; and
- endpoint absence when DEBUG is disabled.

Django system checks, migration drift checks, JavaScript syntax checks and Git whitespace checks passed. The owner visually verified the network, junction rendering, toggle, “no route calculated” notice, corrected single campus label, search, categories and destination selection.

### Current Limitations

- The purple network is synthetic and geographically unverified. Some segments do not follow actual campus walkways.
- Some DEMO destination positions are inaccurate. These are dataset limitations, not routing-engine defects.
- No path or destination in this fixture is evidence of real-world walkability, access or safety.
- There is no A*, Dijkstra, origin selection, destination snapping, calculated route, total distance, ETA, GPS or rerouting.
- Disconnected-network analysis is not yet a user-facing routing error flow.
- JSONField geometry has no spatial database index.
- Real pathways and locations must be populated and field-verified later before trustworthy campus navigation.

### Evidence

- **`P2-S1-A-demo-walkable-network.png`** demonstrates that persisted DEMO segment geometry and junction nodes can be inspected over the campus viewport, with an unmistakable DEMO presentation.
- **`P2-S1-B-routing-foundation.png`** demonstrates the routing-foundation state: the inspection control, explicit “no route calculated” message and preserved map/search interface.

These images prove the implementation and review state. They do not prove that the synthetic coordinates match real campus walkways.

### What Students Should Understand

Students should distinguish five related ideas:

1. The base map is visual context, not automatically trusted routing data.
2. Persisted nodes and segments describe YCT Map’s own candidate network.
3. LineString geometry supplies shape; Haversine summation supplies edge weight.
4. The adjacency graph reorganizes persisted data for efficient traversal.
5. A route is a future algorithm-selected sequence of arcs, not the complete purple network.

They should also understand that technically correct graph construction does not make synthetic coordinates geographically correct. Software correctness and data truth are separate verification responsibilities.

### Presentation / Defence Notes

- **What is a node?** A point where a path starts, ends or connects to another path.
- **What is an edge?** A walkable segment between two nodes; in memory it becomes one or more directed arcs.
- **Why calculate distance?** Geometry can change, so deriving metres prevents a manually stored value from disagreeing with the visible path.
- **Why reverse the geometry?** Guidance along B-to-A must follow coordinate order B-to-A, not reuse A-to-B ordering.
- **Why stable UUIDs?** Future surveys and audit records need to refer to the same segment across edits.
- **Is the purple network a route?** No. It shows all active DEMO topology for inspection.
- **Does it represent real YabaTech paths?** No. It is synthetic test data awaiting later replacement and field verification.
- **What did the regression review prove?** Phase 2 did not alter the accepted base-map provider, style, camera or campus-overlay configuration.

### Next Sprint

Phase 2 Sprint 002 will use this accepted adjacency graph as the input to A* route calculation and route-result behavior. It must select a connected sequence of arcs, reconstruct ordered geometry and handle invalid or unreachable requests without confusing the full network with the chosen route.

Sprint 002 implementation requires separate authorization under the Build Control Protocol. No Sprint 002 code is included in this milestone.

## Phase 2 — Sprint 002: A* Route Calculation, Distance & Baseline ETA

**Recorded status:** OWNER VERIFIED / ACCEPTED on 2026-09-18.

### Purpose

Sprint 002 taught YCT Map to choose a walkable route through the graph created in Sprint 001. The goal was not merely to draw a line between two destinations. The system had to select the lowest-distance connected sequence of graph arcs, preserve the geometry actually traversed, calculate total walking distance, and produce an approximate baseline ETA.

This sprint remained a technical routing milestone. It did not build live GPS navigation, rerouting, final route guidance or verified campus paths.

### User Outcome

In the development route inspector, a reviewer can choose two anchored DEMO destinations, request a route, see the selected route highlighted separately from the complete network, and inspect its distance and approximate ETA.

The interface continues to identify the result as a DEMO route over synthetic geometry. It does not claim that the displayed path follows real YabaTech walkways.

### Starting State

Sprint 001 provided persistent `WalkableNode` and `WalkableSegment` records, geometry-derived segment costs, directional graph arcs and a complete-network inspection overlay. It did not choose a path between nodes.

Locations also remained separate from graph junctions. That separation was intentional: the graph service needed to remain useful for testing, future GPS snapping and manual origins without requiring a destination model.

### What We Built

- A pure A* shortest-path implementation.
- Immutable route-result and explicit routing-error types.
- Predecessor-based ordered node and arc reconstruction.
- Route geometry assembly that supports forward and reverse traversal.
- Total route distance from selected graph-arc costs.
- Approximate ETA using the approved `1.35 m/s` fallback.
- A routing-owned `LocationNetworkAnchor` relationship connecting DEMO destinations to graph nodes.
- Node-to-node and location-to-location routing service entry points.
- DEBUG-only endpoints for anchor discovery and calculated-route inspection.
- A development route selector and solid red calculated-route layer distinct from the dashed purple complete network.
- Tests for algorithm choice, geometry, directionality, inactive data, anchoring, ETA and API boundaries.

### Technical Concepts Introduced

**Shortest-path routing.** A shortest-path algorithm finds the connected route with the smallest total edge cost. In YCT Map, cost means geometry-derived walking metres. It does not mean fewest segments, fewest turns or the visually straightest line.

**A* search.** A* combines known travel cost with an estimate of the remaining cost. It can avoid exploring irrelevant areas while still returning an optimal result when its heuristic is admissible.

**g-score.** `g(n)` is the exact accumulated cost from the origin to candidate node `n`. Here it is the sum of the selected graph arcs' distances in metres.

**h-score.** `h(n)` estimates the remaining cost from `n` to the goal. YCT Map uses straight-line Haversine distance.

**f-score.** `f(n) = g(n) + h(n)`. The priority queue explores the candidate with the smallest expected total cost first.

**Admissible heuristic.** A heuristic is admissible when it never overestimates the cheapest real path. Straight-line geographic distance cannot be longer than a walkable path that must bend around obstacles, so it is a safe lower bound when graph weights are real geometry lengths.

**Predecessor reconstruction.** During search, YCT Map records which prior node and arc produced the best known cost. Once the goal is reached, those references are followed backwards and reversed into travel order.

**Location anchoring.** A destination and a graph junction are different concepts. An anchor connects a destination's arrival relationship to a routing node without turning the `Location` record into graph topology.

### How It Works Internally

The routing service accepts stable start and goal node IDs. It rejects identifiers absent from the active graph. A priority queue begins with the start node. Each time A* examines an outgoing arc, it calculates a candidate `g-score`:

```text
candidate g = current g + arc distance
candidate f = candidate g + Haversine(candidate node, goal)
```

If the candidate cost improves the best known cost for that node, the service stores the new score and predecessor arc. Stable node and segment IDs are used as deterministic tie-break information where practical.

When the goal is reached, reconstruction produces ordered node IDs and arcs. Arc geometry is already oriented in travel direction by the graph builder. The assembler retains the first arc's full coordinate sequence and appends later sequences without repeating their shared first junction.

The route distance is the sum of the chosen arcs. The heuristic is never used as final walking distance; it only guides search. ETA seconds are calculated as distance divided by `1.35 m/s`, then presented as approximate whole minutes.

### Architecture / Components Involved

```text
Location -- LocationNetworkAnchor --> WalkableNode ID
                                         |
Manual node ID --------------------------+
                                         v
                                  RoutingGraph
                                         |
                                         v
                                  A* algorithm
                          g + admissible h -> f
                                         |
                               predecessor chain
                                         v
                                   RouteResult
                    nodes + segments + geometry + metres + ETA
                                         |
                                         v
                          DEBUG inspector / route layer
```

The algorithm depends on `RoutingGraph`, not Django queries or HTTP. The service layer builds the graph and adapts locations to node IDs. The view serializes only the narrow fields required by the development inspector.

### Important Files

- `routing/algorithm.py` — A* queue processing, scores and reconstruction.
- `routing/results.py` — immutable result and explicit domain errors.
- `routing/route_geometry.py` — continuous geometry assembly.
- `routing/eta.py` — baseline speed and approximate display formatting.
- `routing/services.py` — graph construction and location-anchor adapter.
- `routing/models.py` — `LocationNetworkAnchor` alongside network models.
- `routing/migrations/0002_locationnetworkanchor.py` — anchor schema.
- `routing/fixtures/demo_route_anchors.json` — five synthetic destination connections.
- `routing/views.py` — narrow DEBUG anchor and route contracts.
- `routing/tests/test_algorithm.py` and `test_services.py` — algorithm and integration coverage.
- `static/yct_map/js/route-inspector.js` — development selector and result state.
- `static/yct_map/js/map.js` — selected-route source and solid route layer.

### Data Flow

```text
1. Reviewer selects two DEMO destinations.
2. Browser sends stable location UUIDs to the DEBUG route endpoint.
3. Service resolves active LocationNetworkAnchor records.
4. Anchors provide start and goal node UUIDs.
5. Active database network becomes an in-memory RoutingGraph.
6. A* selects the lowest-distance connected arc sequence.
7. Predecessors reconstruct ordered nodes and arcs.
8. Arc geometries are joined in traversal order.
9. Selected arc distances are summed.
10. Distance / 1.35 produces fallback ETA seconds.
11. Endpoint returns an explicit route feature and result properties.
12. Browser draws a solid red route and displays metres and approximate minutes.
```

### Decisions and Trade-offs

**A* instead of plain Dijkstra.** Dijkstra is equivalent to using a zero heuristic and may inspect more of the graph. A* uses geographic knowledge to focus toward the goal while preserving correctness with an admissible heuristic.

**Distance rather than hop count.** A route with four short segments may be better than a route with two long segments. Counting edges would optimize database structure rather than walking effort.

**Explicit result dataclass instead of model serialization.** A route is a computed value, not a persisted Django row. An immutable contract prevents callers from depending on internal model objects.

**Routing-owned anchor instead of `Location.arrival_node`.** The extra model keeps destination data and graph topology separate. The current one-to-one relationship supports one V1 arrival connection and can evolve toward multiple entrances later.

**Explicit exceptions for failure states.** Invalid nodes, missing anchors and unreachable components are different conditions. Returning partial geometry or `None` would make those cases ambiguous.

**Fallback ETA rather than pretend personalization.** `1.35 m/s` provides a consistent baseline, but it cannot represent every user. Live personalized estimates require reliable movement samples, GPS-noise rejection and stationary-period handling in a later phase.

### Problems Encountered

- Floating-point division produced `59.99999999999999` seconds for an exact conceptual minute in one test.
- A same-origin route contains one coordinate, which is not a valid two-point GeoJSON `LineString`.
- The preferred integrated browser connection remained unavailable, and the isolated browser again did not complete external OpenFreeMap style loading.

No shortest-path correctness failure remained at acceptance.

### How We Solved Them

- The ETA test uses tolerance-based floating-point comparison rather than demanding binary equality.
- The internal same-origin result remains a successful zero-distance route with one node and no arcs. Its debug serialization uses a GeoJSON `Point`, avoiding an invalid or invented line.
- Algorithm, API and regression behavior were verified through the full automated suite and live local endpoint checks. The owner completed normal-browser visual verification of route selection, multiple states, distance and ETA.

### Testing and Verification

All 45 tests passed at acceptance. New coverage proves:

- direct and multi-segment routes;
- a longer-hop but lower-distance path beats a fewer-hop longer path;
- deterministic equal-cost behavior;
- predecessor reconstruction;
- unreachable and same-origin handling;
- one-way directionality;
- inactive node and segment exclusion;
- forward and reverse geometry order;
- shared-junction deduplication;
- intermediate-vertex preservation;
- geometry-derived route distance and baseline ETA;
- valid, missing and inactive anchors;
- node routing without `Location` objects;
- explicit DEBUG route contracts and their production exclusion.

Django checks, migration drift, JavaScript syntax and Git whitespace checks passed. A local example traversed three nodes and two segments for `158.51 m` with an approximate `~2 min` ETA. Owner verification confirmed the visual route and earlier functionality.

### Current Limitations

- All current routes use synthetic, geographically unverified DEMO geometry.
- Algorithm correctness cannot make an incorrect graph match the real campus.
- The DEBUG inspector is not the final student navigation interface.
- Static origin and destination endpoint markers require clearer Sprint 003 presentation.
- There is no GPS, live heading, progress, rerouting or turn guidance.
- The `1.35 m/s` ETA is a generic fallback, not a personal walking-speed measurement.
- One primary network anchor per location is supported; multiple entrances are deferred.
- Real pathways, entrances and destination positions still require editor review and field verification.

### Evidence

- **`P2-S2-A-calculated-demo-route.png`** demonstrates that A* selects and highlights one connected subset of the complete DEMO network. The solid calculated route remains visibly different from the dashed network.
- **`P2-S2-B-route-distance-eta.png`** demonstrates the explicit result contract in the interface: selected DEMO endpoints, geometry-derived distance and approximate baseline ETA.

The images prove calculation and presentation behavior. They do not prove real-campus path accuracy.

### What Students Should Understand

Students should be able to work through this small example:

```text
A --100 m--> D
A -- 40 m--> B --30 m--> C --20 m--> D

Direct-looking route A-D:         100 m, 1 edge
Connected route A-B-C-D:           90 m, 3 edges

A* must choose A-B-C-D because 90 m < 100 m.
```

The example shows why hop count is not walking distance. `g` tracks the 40, then 70, then 90 metres actually accumulated. `h` estimates remaining straight-line distance. `f` prioritizes the most promising candidate. The final answer comes from chosen graph arcs, never from the heuristic alone.

Students should also understand that reverse traversal requires reversed geometry, not only reversed node IDs. Otherwise the result's coordinates would run opposite to travel. Finally, a mathematically optimal route is only useful if the graph correctly represents walkable reality.

### Presentation / Defence Notes

- **Why A*?** It preserves shortest-path correctness while using a geographic lower bound to guide exploration.
- **Why is Haversine not the route distance?** It ignores path bends, obstacles and network connectivity. It is only the heuristic.
- **Why not count segments?** Segment boundaries are modelling choices; metres represent actual graph cost.
- **How is the route reconstructed?** Follow predecessor arcs from goal to start, then reverse the collected sequence.
- **Why an anchor model?** Destinations and intersections have separate responsibilities and lifecycles.
- **What happens when no route exists?** The service returns an explicit no-route condition rather than inventing a connection.
- **What happens when start equals goal?** It returns success with zero metres, zero ETA and no traversal arcs.
- **Is `1.35 m/s` final?** No. It is the approved fallback until reliable personal movement data exists.
- **Can visible OSM paths be reused?** They may inform future mapping, but explicit YCT Map graph records, editor review and field verification are still required.

### Next Sprint

Phase 2 Sprint 003 will turn the technical route result into a clearer user-facing route experience. Approved endpoint presentation requires a distinct static start marker and red destination indicator. Static origins must not imitate live GPS; directional live-position and heading indicators remain reserved for reliable Phase 3 geolocation data.

No Sprint 003 implementation is included in this accepted milestone.

## Phase 2 — Sprint 003: User-Facing Navigation UX & Phase 2 Completion

**Recorded status:** OWNER VERIFIED / ACCEPTED on 2026-09-18.

### Purpose

Sprint 003 converted the accepted routing engine into a normal-user navigation experience. It also replaced the primary synthetic visual graph with a reviewed, OSM-derived development network so route UX could be evaluated against geographically plausible topology without claiming field verification.

### User Outcome

A user can select an anchored DEMO destination, choose another anchored DEMO location as a manual start, request Directions, and see a blue calculated route with a static blue `S`, red `D`, walking distance, approximate ETA and simple start/follow/arrive guidance. The user can change either endpoint or clear the route. Developer topology inspection remains separate and collapsed.

### Starting State

Sprint 002 already had correct A* calculation, route reconstruction, distance and ETA, but these were exposed mainly through a DEBUG inspector. Endpoint presentation needed to distinguish manual selection from future live GPS. The original five-segment graph was deterministic and useful for algorithm tests, but owner review found it geographically unrealistic for continued visual product evaluation. Medical Centre also had no Directions action because it lacked an active network anchor.

### What We Built

- A narrow public route endpoint using location UUIDs rather than graph internals.
- A normal-user Directions flow and responsive route summary.
- Explicit `browsing`, `destination-selected`, `choosing-origin` and `route-available` UI states.
- A blue cased route, static blue `S`, red `D`, and panel-aware route framing.
- Change-start, change-destination, cancel and clear behavior.
- JavaScript behavior tests for the real interaction sequence.
- OSM provenance fields plus a deterministic reviewed-snapshot importer.
- A 47-node, 54-segment, six-anchor OSM-derived `UNVERIFIED` development graph.
- A deliberate non-verified Medical Centre anchor.

### Technical Concepts Introduced

**Public contract isolation.** The browser sends stable location identifiers and receives only names, route geometry, distance, ETA and verification context. Database node IDs and A* internals remain private.

**Finite UI state.** The interface has named states with one clear owner. This prevents two panels from competing or both disappearing during a transition.

**Provenance versus verification.** Provenance answers where geometry came from; verification answers how strongly YCT Map trusts it. An OSM way reference is useful audit information, but it is not evidence that the path was physically checked.

**Data quality and algorithm quality.** A shortest-path algorithm can be correct and still produce an implausible real-world route when its graph is unrealistic. A* optimizes the network supplied to it; it cannot discover missing paths or reject an incorrectly included service road without suitable data.

### How It Works Internally

The location endpoint exposes `routing_available` only when an active anchor exists. Directions changes the app to `choosing-origin`; a successful selection calls the public route endpoint. Django resolves both location anchors, builds the adjacency graph and runs A*. The response geometry is rendered as a selected blue route, not the complete network.

The importer reads a repository-owned Overpass snapshot and reviewed manifest. It rejects disallowed/construction features, clips processing to the campus reference area, splits OSM ways at endpoints, shared OSM nodes and reviewed arrival nodes, then persists owned nodes and segments transactionally. Source references, versions and timestamps remain attached while verification stays `UNVERIFIED`.

```text
Destination card --Directions--> choosing-origin
       |                              |
       |                         choose origin
       |                              v
       `----------------------> POST /api/routes/
                                      |
                          anchors -> graph -> A*
                                      |
                                      v
                         route-available UI state
```

### Architecture / Components Involved

```text
Reviewed OSM snapshot + manifest
              |
              v
      deterministic importer
              |
              v
SQLite: WalkableNode -- WalkableSegment -- LocationNetworkAnchor
              |
              v
        in-memory adjacency graph
              |
              v
          A* route service
              |
              v
public route JSON -> navigation controller -> MapLibre layers/panel
```

OpenFreeMap tiles remain visual background. The imported graph is YCT Map-owned application data and is not read from rendered tiles at route time.

### Important Files

- `routing/models.py` and `routing/migrations/0003_walkable_provenance.py` — source metadata and controlled provenance.
- `routing/osm_import.py` and `routing/management/commands/import_osm_walkable_network.py` — deterministic conversion and transactional loading.
- `routing/data/osm/` — captured source snapshot, review manifest and provenance notes.
- `routing/views.py` and `routing/urls.py` — narrow public route contract.
- `static/yct_map/js/user-navigation.js` — navigation state and route-panel behavior.
- `static/yct_map/js/app.js`, `destination-panel.js` and `map.js` — coordinated state, intent and map rendering.
- `tests/js/sprint003-public-navigation.test.mjs` — behavior-level frontend regression coverage.
- `routing/tests/test_osm_import.py` — conversion, provenance and replacement tests.

### Data Flow

```text
OSM way geometry
 -> reviewed walking candidate
 -> split at routing decisions/junctions
 -> WalkableNode endpoints
 -> WalkableSegment LineStrings
 -> active adjacency arcs
 -> A* selected arc sequence
 -> continuous traversal-oriented coordinates
 -> browser route line + endpoints + summary
```

For bidirectional segments the graph creates a reverse arc with reversed coordinates. Distance is the sum of Haversine lengths over every selected LineString leg. ETA is `distance / 1.35 m/s`, rounded for display and explicitly approximate.

### Decisions and Trade-offs

- The small synthetic graph remains the deterministic test fixture but is no longer the primary visual dataset.
- A captured snapshot plus reviewed manifest is reproducible; querying Overpass during every load would make tests and local setup depend on changing network data.
- JSON geometry and SQLite remain sufficient at this scale; PostGIS is not yet justified.
- OSM-derived records stay editable and `UNVERIFIED`. There is no automatic OSM write-back or automatic promotion to `FIELD_VERIFIED`.
- One current anchor per location keeps the model narrow; multiple entrances remain future work.

### Problems Encountered

The initial implementation passed backend and static checks, but the first owner review appeared to expose the DEBUG route experience rather than the intended public flow. Asset caching was one cause, so shared versioning was introduced. A later review exposed a second issue: the destination panel could close before the navigation controller had successfully taken ownership. Backend response tests and syntax checks could not prove this interaction sequence.

Separately, the owner correctly rejected the five-segment synthetic geometry as too unrealistic. Medical Centre lacked Directions because it had no active `LocationNetworkAnchor`.

### How We Solved Them

- Versioned the related frontend assets together to prevent mixed old/new modules.
- Made application state explicit and initialized navigation before destination interaction.
- Closed the destination panel only after `begin()` successfully entered choosing-origin state.
- Added executable JavaScript behavior tests covering intent, origin selection, request/result rendering, cancellation and clearing.
- Replaced the primary visual dataset with reviewed OSM-derived topology while retaining the routing engine unchanged.
- Added a deliberate `UNVERIFIED` Medical Centre anchor.

The central engineering lesson is precise: **A* was already correct. Poor route realism came from poor input geometry, not from an incorrect shortest-path algorithm.** Better network data materially improved the same A*, reconstruction, distance and ETA pipeline.

### Testing and Verification

At acceptance, 52 Django tests and 3 Node-executed JavaScript behavior tests passed. Coverage includes public contract isolation, route edge cases, source restrictions, deterministic import, provenance, transactional replacement, 47/54 record counts, six anchors, Medical Centre availability and all 15 unordered destination pairs. Django checks, migration drift, JavaScript syntax and Git diff/whitespace checks form the milestone gate.

Owner verification confirmed the normal-user route flow, endpoint markers, route-aware framing, Medical Centre routing, preserved discovery features and improved plausibility of several routes.

### Current Limitations

- OSM-derived paths are not field verified; service-road walkability is not guaranteed.
- Exact entrances/exits are not deeply mapped and some arrival points remain approximate.
- There is no browser GPS, live position, heading, route progress or rerouting.
- ETA still uses the `1.35 m/s` fallback.
- Path Survey Mode and the complete editor mapping interface do not exist yet.
- Plausible geometry must not be presented as proof of safe or permitted real-world access.

### Evidence

- **`P2-S3-A-navigation-route-endpoints.png`** demonstrates the normal-user blue route, static blue start and red destination indicators, route summary and separation from DEBUG inspection.
- **`P2-S3-B-medical-centre-route.png`** demonstrates that the formerly unanchored Medical Centre now participates in routing through an explicit non-field-verified anchor.
- **`P2-S3-C-osm-unverified-network.png`** supports review of the 47-node/54-segment OSM-derived development topology and its explicit unverified status.
- **`P2-R-navigation-flow.mp4`** records the end-to-end Phase 2 interaction from destination selection through route display and route controls.

The evidence demonstrates software behavior and owner review, not field verification of campus access.

### What Students Should Understand

Students should be able to explain why persistent graph records are converted into an adjacency structure, why reverse arcs reverse geometry, why destination anchors are separate from junctions, and why route distance follows every geometry leg. They should distinguish DEBUG topology inspection from the public route experience, provenance from verification, and algorithm correctness from dataset realism.

They should also understand why tests at multiple levels matter: Django tests proved contracts and services, syntax checks proved parseability, but only behavior tests and owner browser review exercised panel ownership and state transitions.

### Presentation / Defence Notes

- **Why A*?** It preserves shortest-distance correctness while its admissible straight-line Haversine heuristic prioritizes nodes likely to lead toward the goal.
- **What are `g`, `h` and `f`?** `g` is distance already travelled, `h` is the non-overestimating straight-line estimate remaining, and `f = g + h` orders candidates.
- **Why anchors?** A destination is a semantic place; a node is routing topology. An anchor connects them without confusing their responsibilities.
- **Why not route over the base map?** Rendered tiles are presentation. YCT Map needs explicit, editable, auditable graph records.
- **Is OSM-derived equal to verified?** No. It preserves source provenance but remains `UNVERIFIED` until review and physical confirmation.
- **Why did routes improve without changing A*?** The graph began representing more plausible real geography.

### Next Sprint

Phase 3 is next for discussion and planning. It may add browser geolocation, a genuinely live directional position indicator, progress and controlled rerouting. No Phase 3 implementation is authorized by this acceptance milestone; a standalone `BUILD` command is still required.

## Phase 2 Summary — Routing & Navigation

**Status:** OWNER ACCEPTED on 2026-09-18.

### Achievements

Phase 2 established persisted routing topology, geometry-derived weights, adjacency conversion, A* shortest-distance routing, reconstruction, distance and baseline ETA, destination anchoring, normal-user Directions UX, static endpoint markers, responsive framing and a reproducible OSM-derived development network with provenance.

### Resulting Architecture

```text
Persistent layer          Computation layer             Experience layer
---------------           -----------------             ----------------
WalkableNode       ->     adjacency[node]       ->      public route API
WalkableSegment           directed GraphArc(s)          navigation state
LocationAnchor            A* + reconstruction           MapLibre route UI
OSM provenance            distance + ETA                 S / D + summary
```

Nodes represent routing decisions; persisted segments represent shaped connections. Active rows become directed arcs in memory. A* maintains `g`, estimates admissible Haversine `h`, orders by `f = g + h`, then follows predecessor arcs backward and reverses them to reconstruct the route. Segment coordinates are oriented for travel and joined without duplicated junction points.

### Major Concepts Learned

- Graph topology is different from visible cartography.
- A LineString carries path shape; summed Haversine legs provide traversal cost.
- Persistence supports validation, provenance and editing; adjacency supports efficient search.
- Directionality belongs in graph arcs, including reversed geometry for reverse travel.
- Anchors connect places to topology without making place coordinates graph junctions.
- ETA at `1.35 m/s` is a fallback estimate, not observed user speed.
- UI state is architecture: explicit ownership prevents fragile multi-panel transitions.
- OSM provenance does not equal YCT Map field verification.
- A correct algorithm cannot compensate for an unrealistic graph.

### Important Problems and Solutions

The repeated campus label was resolved with deterministic point placement. Sprint 003's stale-asset and fragile-transition failures were resolved through shared versioning, explicit states and behavior tests. The unrealistic synthetic graph was replaced as the visual development dataset by reviewed OSM-derived records while remaining available for deterministic tests. The missing Medical Centre anchor was added without claiming field verification.

### Evidence

Phase 2 evidence comprises `P2-S1-A-demo-walkable-network.png`, `P2-S1-B-routing-foundation.png`, `P2-S2-A-calculated-demo-route.png`, `P2-S2-B-route-distance-eta.png`, `P2-S3-A-navigation-route-endpoints.png`, `P2-S3-B-medical-centre-route.png`, supporting `P2-S3-C-osm-unverified-network.png`, and `P2-R-navigation-flow.mp4`.

### Current System Capabilities

The local application can search and select six DEMO destinations, calculate routes between every pair, render a selected route distinctly, display geometry-derived distance and approximate ETA, explain static start/arrival steps, and allow endpoint changes or clearing. Developers can inspect the complete graph separately. The primary graph is plausible enough for development review but remains unverified.

### Transition to Phase 3

Phase 3 can build live navigation on a stable route contract and explicit frontend states. It must introduce permission-aware browser geolocation, reliable live-position semantics, progress and noise-tolerant rerouting without confusing manual/static origins with GPS. Field verification, Path Survey Mode and full editor mapping remain later responsibilities.

## Phase 3 — Sprint 001: Live Location Foundation

**Recorded status:** OWNER VERIFIED / ACCEPTED on 2026-09-18. **SIMULATED GEOLOCATION VERIFIED. PHYSICAL PHONE GPS NOT YET VERIFIED.**

### Purpose

This sprint established a trustworthy answer to “Where is the user now?” before attempting live-origin routing, route progress or rerouting. It introduced browser permission handling, transient position acquisition, accuracy-aware filtering, honest uncertainty presentation and a dedicated live-location marker.

### User Outcome

The user can deliberately press **Locate me**, respond to the browser permission prompt, see an accepted simulated campus position with an accuracy halo, recenter the map and stop location tracking. Permission denial and temporary failures leave search and manual Directions available.

### Starting State

Phase 2 could route between manually selected anchored DEMO destinations. It had a static blue `S` and red `D`, but no browser geolocation, live marker, accuracy model or watcher lifecycle. Ordinary-user coordinates had no approved reason to reach the backend or database.

### What We Built

- Explicit location states: idle, unsupported, requesting permission, locating, active, low accuracy, denied, unavailable, timed out and stopped.
- Initial `getCurrentPosition()` acquisition followed by `watchPosition()` updates.
- Separate raw-sample and accepted-display-position handling.
- Validation for coordinates, accuracy, timestamps, heading and speed.
- Accuracy bands and a 100 m display ceiling.
- Retention of a previously better position when a substantially worse sample arrives.
- Basic implausible-jump protection.
- A blue live dot without heading and a chevron only with trustworthy movement heading.
- A geographic accuracy halo, first reliable focus, recenter and stop controls.
- Cleanup on stop, page visibility changes and permission revocation.
- Behavior-level JavaScript tests alongside existing Django regressions.

### Technical Concepts Introduced

**Browser Geolocation API.** `getCurrentPosition()` requests a single reading and is useful for initial acquisition. `watchPosition()` continues delivering updates until its watcher is cleared. Neither proves that every delivered sample is accurate.

**Permission states.** Permission is asynchronous and user-controlled. The application must remain useful when access is denied, unavailable, unsupported or slow.

**Raw versus accepted position.** A raw sample is browser input. An accepted position is the location YCT Map has validated and chosen to display. Separating them prevents one poor measurement from immediately moving the marker.

**Accuracy metadata.** The browser’s `accuracy` value describes an estimated uncertainty radius in metres. It is not a guarantee that the device lies exactly at the centre point.

**Heading semantics.** Device heading and route bearing answer different questions. The chevron represents supplied movement heading only; it is never rotated merely because a route points in that direction.

### How It Works Internally

```text
User presses Locate me
          |
          v
 getCurrentPosition()
          |
          v
      raw sample --------------------+
          |                           |
          v                           | rejected
 coordinate/time/accuracy validation +--> keep last better position
          |
          v
 accuracy + jump assessment
          |
          v
 accepted display position
       /        \
      v          v
 marker      accuracy halo
          |
          v
 watchPosition() supplies later samples
```

`location-filter.js` normalizes browser values and applies pure validation. Samples worse than 100 m are not displayed. A new provisional sample does not replace an existing position of materially better quality. For movement updates, Haversine distance divided by elapsed time estimates apparent speed; an implausible jump above the generous 12 m/s guard is rejected unless accuracy improved substantially.

This is display stabilization, not walking-speed estimation or stationary-state modelling.

### Architecture / Components Involved

```text
navigator.geolocation
        |
        v
 geolocation.js       acquisition + watcher lifecycle
        |
        v
 location-filter.js   validation + quality decision
        |
        v
 user-location.js     UI state + accepted position
        |
        v
 map.js               dot/chevron + halo + recenter
```

The pipeline is entirely client-side. Django serves the interface but receives no Sprint 001 position payload.

### Important Files

- `static/yct_map/js/geolocation.js` — browser API wrapper, error normalization and watcher cleanup.
- `static/yct_map/js/location-filter.js` — sample normalization, accuracy bands, Haversine movement and rejection rules.
- `static/yct_map/js/user-location.js` — state machine, controls and accepted-position ownership.
- `static/yct_map/js/map.js` — MapLibre sources/layers, metre-based halo and recenter behavior.
- `static/yct_map/js/app.js` — composition with existing discovery and routing.
- `templates/map/index.html` and `static/yct_map/css/app.css` — accessible controls, status and responsive presentation.
- `tests/js/phase3-live-location.test.mjs` — deterministic acquisition/filtering/state tests.

### Data Flow

The browser supplies latitude, longitude, accuracy, timestamp and optional speed/heading. YCT Map keeps the latest raw input conceptually separate from the last accepted position. Only an accepted position reaches the map renderer. Stop clears both the watcher and displayed location.

No coordinate is written to SQLite, local storage, session storage, analytics, a URL or a Django endpoint.

### Decisions and Trade-offs

**User-triggered permission.** The application asks only after a meaningful action, providing context and avoiding an intrusive page-load prompt.

**High accuracy with controlled lifetime.** High-accuracy acquisition is appropriate for campus-scale positioning but may consume more power, so tracking is explicit, stoppable and paused while the page is hidden.

**Keep the better position.** Stability and honesty are preferable to moving the marker for every sample. The trade-off is that the marker can appear unchanged; a future refinement should explain that a worse update was rejected.

**No live-origin routing yet.** A GPS coordinate is not automatically a graph node. Safe routing requires segment projection, maximum snap distance and off-network behavior. Deferring that adapter prevents arbitrary snapping or false connectors through buildings.

**No new persistence.** Live display does not require a schema or history. This reduces privacy risk and keeps Path Survey Mode—a future deliberate editor workflow—separate from ordinary navigation.

### Problems Encountered

The accepted behavior test demonstrated that a roughly 100 m sample should not replace an already accepted roughly 40 m position. The filter handled this correctly, but the UI currently gives no explicit explanation that the previous better location was retained.

The automated in-app browser connection was unavailable during implementation verification. Repository tests, local HTTP checks and owner browser verification supplied the evidence; no unauthorized external exposure or tunnel was introduced.

### How We Solved Them

Accuracy classification and accepted-position ownership ensure poorer samples cannot casually displace better information. Watchers are cleared on stop and permission revocation, and hidden-page tracking is paused. The unexplained-retention copy improvement is documented as a minor non-blocking carryover rather than misrepresented as complete.

### Testing and Verification

At acceptance:

- 52 Django tests passed;
- 8 Node-executed JavaScript tests passed;
- all JavaScript syntax checks passed;
- Django system checks passed;
- migration drift was absent;
- Git whitespace checks passed;
- localhost served the current asset version and live-location controls.

The owner verified permission, simulated campus positioning, marker, halo, low-accuracy behavior, recenter, stop, denied fallback, preserved manual Directions and better-position retention.

### Current Limitations

- Physical-phone GPS is not verified because no approved HTTPS test origin exists.
- Rejected-worse-sample retention is not yet explained explicitly in the UI.
- Live position cannot yet be used as a route origin.
- There is no graph snapping, progress, arrival detection, dynamic ETA or rerouting.
- Indoor accuracy and real campus conditions remain unknown.

### Evidence

- **`P3-S1-A-live-location-marker.png`** demonstrates the simulated campus live marker, campus context and metre-based uncertainty halo.
- **`P3-S1-B-location-permission-fallback.png`** demonstrates that denied/unavailable location is explained while manual Directions remains usable.

Both images use simulated campus coordinates and do not capture the owner’s private real-world location. They prove simulated product behavior, not physical-device GPS performance.

### What Students Should Understand

Students should understand that browser GPS data is uncertain input rather than unquestionable truth. Accuracy metadata must influence presentation and filtering. A raw sample can be structurally valid yet still be unsuitable to replace a better accepted position. They should also understand that permission denial is a normal product state, cleanup matters for privacy and battery use, and a live map point is not automatically safe routing topology.

### Presentation / Defence Notes

- **Why use both acquisition methods?** One obtains the initial result; the watcher supplies controlled updates.
- **Why keep raw and accepted positions?** It prevents bad samples from directly controlling the UI.
- **Why does the halo change size?** Its geographic radius represents reported uncertainty in metres.
- **Why is there sometimes a dot instead of a chevron?** Direction is shown only when the browser supplies credible movement heading.
- **Was real phone GPS tested?** No. The accepted milestone is explicitly simulated geolocation verification.
- **Where is location stored?** Nowhere persistent; it exists only in browser memory during the active session.
- **Why can it not start a route?** Safe graph matching and off-network limits require a separate designed adapter.

### Next Sprint

Phase 3 Sprint 002 is next for discussion/planning. Its exact scope is not yet approved. Candidate follow-up work includes the retained-position explanation and a carefully bounded live-position-to-network adapter, but no Sprint 002 implementation is authorized by this milestone.

## Phase 3 — Sprint 002: Live Route Start, Route Progress & Dynamic ETA

**Recorded status:** OWNER ACCEPTED on 2026-09-18. **SIMULATED LIVE NAVIGATION VERIFIED. PHYSICAL LIVE NAVIGATION NOT VERIFIED.**

### Purpose

This sprint connected the transient live position from Sprint 001 to the routing system without treating an arbitrary GPS coordinate as a trustworthy graph node. It also introduced stable route progress and an ETA that can use a filtered personal walking pace while retaining the documented 1.35 m/s fallback.

### User Outcome

A user with a sufficiently accurate accepted position can choose **Use my live location**, request a route to an anchored DEMO destination, see the measured position separately from the matched route origin, and watch remaining distance and approximate ETA respond to simulated movement. Manual starting points remain available.

### Starting State

Sprint 001 could display and filter transient browser positions, but only anchored locations could start routes. The server had no safe coordinate-to-graph adapter, and the browser had no route-progress, personal-speed, stationary or arrival model.

### What We Built

- A CSRF-protected `POST /api/routes/from-position/` endpoint with a narrow no-store response.
- Complete-polyline nearest-point matching against active walkable segments.
- Quality-aware snap limits: preferred through 25 m, conditional caution through 40 m, and rejection beyond 40 m.
- A request-local virtual graph origin connected through partial segment geometry while respecting directionality.
- A live-origin option that does not remove or imitate manual routing.
- Separate measured-position and network-matched-origin presentation.
- Client-side route projection, stable displayed progress, remaining distance, walking-speed filtering, stationary state, dynamic ETA and two-sample arrival confirmation.
- Explicit feedback when a worse incoming GPS sample is rejected in favor of the previous better position.

### Technical Concepts Introduced

**GPS-to-network matching** converts an uncertain geographic sample into a safe routing attachment. It is not verification of the person's exact physical position.

**Nearest point on a polyline** checks every line segment between consecutive LineString vertices. For one leg from `A` to `B`, the position is projected onto the leg and the projection fraction is clamped to `0…1`; the candidate with the smallest perpendicular distance wins.

**Partial-segment geometry** preserves the real line shape between the matched point and an endpoint. This matters because the user may join halfway along a curved segment rather than at its start.

**Ephemeral graph augmentation** adds a virtual origin only to the in-memory graph for one request. It does not create a database node or movement history.

**Route progress projection** maps each accepted sample onto the already calculated route and measures distance along the route. Straight-line distance to the destination would cut across geometry and produce incorrect progress.

**Robust speed estimation** excludes weak samples, uncertainty-sized movement, implausible speeds and stationary periods. A rolling median limits the influence of one noisy value.

### How It Works Internally

```text
accepted live sample + destination UUID
                |
                v
 POST /api/routes/from-position/
                |
                v
 project onto every eligible segment leg
                |
       safe threshold decision
         | reject        | accept
         v               v
      HTTP 422     ephemeral virtual node
                            |
                   partial directed arc(s)
                            |
                            v
                       existing A*
                            |
                            v
                fixed route geometry returned

later accepted browser samples
                |
                v
 project onto fixed route -> stabilize progress
                |                    |
                v                    v
       remaining route distance   filtered pace
                \                    /
                 +---- dynamic ETA -+
```

The server performs initial network matching because the routing graph and its direction rules are authoritative there. After the route is returned, routine progress calculations remain in browser memory; repeated coordinates are not sent to Django.

### Architecture / Components Involved

- Django routing view: validates the small JSON request and returns a controlled contract.
- Matching service: validates position quality and projects onto active `WalkableSegment` geometry.
- Routing service: creates the virtual node and partial arcs, then calls the existing A* implementation.
- User-navigation controller: offers live/manual origins and owns active-route UI state.
- Live-route tracker: projects later samples, stabilizes progress and estimates pace/ETA.
- Map controller: keeps the blue measured location separate from the hollow matched route origin and red destination.

### Important Files

- `routing/matching.py` — position validation, polyline projection and safe-match policy.
- `routing/services.py` — ephemeral graph origin and A* integration.
- `routing/views.py` and `routing/urls.py` — protected public live-route contract.
- `static/yct_map/js/live-route-progress.js` — route projection, progress, pace, ETA and arrival state.
- `static/yct_map/js/user-navigation.js` — live-origin selection and navigation summary updates.
- `static/yct_map/js/user-location.js` — retained-better-position explanation.
- `static/yct_map/js/map.js` — distinct measured, matched-origin and destination symbols.
- `routing/tests/test_live_routing.py` and `tests/js/phase3-live-routing.test.mjs` — deterministic server and client behavior.

### Data Flow

The initial accepted latitude, longitude and reported accuracy travel once to Django with the destination UUID. The endpoint validates them, matches them to the graph, calculates A* and returns route geometry plus a small summary. It does not echo separate raw coordinates, persist them or cache the response.

Later accepted samples stay in the browser. They update the measured marker and progress tracker. The tracker returns presentation state—remaining metres, ETA source, movement state and arrival—not a breadcrumb history.

### Decisions and Trade-offs

**Nearest segment instead of nearest node.** Nearest-node snapping can send a user to a junction far along the path and omit the usable partial segment. Polyline projection represents where the route is actually joined.

**Measured point remains visible.** Snapping is a routing decision, not permission to move the blue location marker. A hollow origin communicates the graph match without pretending GPS and routing geometry are identical.

**25/40 m safety boundary.** Matches within 25 m are preferred. A 25–40 m match is allowed only when reported accuracy is 25 m or better. Anything farther is rejected. This favors a transparent failure over a plausible-looking but unsafe route.

**Displayed progress is stabilized.** Raw projected progress may move backward because of jitter. A small regression is ignored; a larger regression requires confirmation before displayed progress moves backward. The raw measurement therefore cannot make the UI oscillate freely.

**Pace and stationary state are separate.** Being stationary should change movement state without replacing the last useful walking pace with zero. Personal pace becomes available only after enough plausible samples; otherwise ETA uses 1.35 m/s.

**Arrival requires confirmation.** One good-looking GPS sample near the end is insufficient. Two eligible samples at least three seconds apart must be near both the route end and remaining-distance threshold.

### Problems Encountered

The owner's original simulated coordinate (`6.51857, 3.37424`) enabled live location but produced HTTP 422. Repository inspection showed that its nearest eligible segment was approximately 69.35 m away, beyond the 40 m hard limit. This was correct safety behavior, not an A* defect.

The test coordinate initially used by server unit tests belonged to the synthetic test fixture rather than the active OSM-derived development graph. Owner verification therefore required a dataset derived from the active graph.

The owner did not cleanly complete every stationary and arrival transition during manual simulation. Those behaviors must not be described as owner-verified.

### How We Solved Them

We retained the rejection rule and derived an owner test trace from the active graph instead of weakening safety. The trace began at the active School Building anchor, followed exact calculated route geometry toward `DEMO — Hostel`, and produced an initial route of approximately 209 m. Later owner-observed values of approximately 185 m and 179 m confirmed advancing progress.

Stationary handling, pace isolation, arrival confirmation and progress stability remain backed by deterministic automated tests. Documentation records that narrower verification boundary explicitly.

### Testing and Verification

At acceptance:

- 60 Django tests passed;
- 12 Node-executed JavaScript tests passed;
- JavaScript syntax checks passed;
- Django system checks passed;
- no migration drift existed;
- Git whitespace checks passed.

The owner visually verified live-origin availability, safe matching, HTTP 422 rejection of the approximately 69 m case, route initialization, marker separation, a fixed route during updates, advancing progress, decreasing remaining distance, personal-pace ETA behavior and preserved manual routing.

Deterministic automated tests verified stationary-state handling, stationary samples not corrupting walking pace, ETA fallback/personal hierarchy, two-sample arrival, backward-progress stability, snap rejection and manual/live regressions. Physical-phone navigation was not tested.

### Current Limitations

- The OSM-derived graph and anchors remain `UNVERIFIED`, not field verified.
- Physical-phone GPS/navigation remains unverified pending an approved secure test origin.
- Full off-route detection and automatic rerouting are absent.
- Outside-campus behavior is not a complete product flow.
- Path Survey Mode and persistent editor survey traces are future work.
- Stationary and arrival transitions were not cleanly owner-observed in this sprint.

### Evidence

- **`P3-S2-A-live-origin-route.png`** demonstrates the approximately 209 m live-origin route, simulated live marker, distinct matched graph origin, destination and navigation summary.
- **`P3-S2-B-dynamic-eta-progress.png`** demonstrates an active fixed route after simulated movement, reduced remaining distance and dynamic navigation state. A screenshot explicitly showing personal pace is preferred where available.
- The HTTP 422 unsafe-snap screenshot is supporting evidence of the safety boundary, not one of the two primary images.

All evidence uses simulated campus coordinates. It does not establish physical GPS reliability or field-verified walkability.

### What Students Should Understand

Students should be able to explain why GPS coordinates cannot be inserted directly into A*, how projecting onto every polyline leg differs from choosing the nearest node, and how partial geometry connects a virtual origin without modifying persistence. They should distinguish raw projected progress from stabilized displayed progress and explain why remaining distance follows the route.

They should also understand that speed derived from noisy GPS is a statistical estimate. Accuracy, elapsed time, uncertainty-sized movement, plausible speed limits, sample count and smoothing all affect whether personal pace is trusted. Stationary state describes current movement; it does not mean the person's walking pace is zero. Finally, privacy depends on data flow: initial coordinates are transient server input, while ongoing progress remains client-side.

### Presentation / Defence Notes

- **Why not snap to the nearest node?** It can skip usable path geometry and select a topologically misleading junction.
- **What is the virtual origin?** A request-only node at the safe projected point, connected through partial segment geometry and discarded after routing.
- **Why did the 69 m test fail?** The hard limit is 40 m; refusing the match prevents false campus guidance.
- **Why can displayed progress differ from one raw projection?** Stabilization prevents GPS jitter from repeatedly moving progress backward.
- **How is dynamic ETA calculated?** Remaining route distance is divided by a rolling-median personal pace when reliable; otherwise 1.35 m/s is used.
- **Was stationary/arrival manually verified?** No. Those transitions are deterministic automated-test verification only.
- **Was physical navigation verified?** No. The accepted label is `SIMULATED LIVE NAVIGATION VERIFIED`.

### Next Sprint

Phase 3 Sprint 003 is next for discussion/planning. Expected future concerns include full off-route evidence and controlled rerouting, but no Sprint 003 implementation has begun or is authorized without a standalone `BUILD` command.

## Phase 3 — Sprint 003: Off-Route Detection & Controlled Rerouting

**Recorded status:** OWNER ACCEPTED on 2026-09-18. **SIMULATED REROUTING VERIFIED. PHYSICAL REROUTING NOT VERIFIED.**

### Purpose

This sprint made live navigation recover when reliable evidence shows that the user is no longer following the active route. The goal was not to react to every GPS fluctuation; it was to distinguish uncertainty from a genuine deviation and request one safe replacement route only when confidence was sufficient.

### User Outcome

During an active live route, suspicious displacement first displays **Checking your position…**. One anomaly does not destroy navigation. Several trustworthy samples away from the route can trigger a controlled reroute to the same destination. Progress and ETA then continue against the replacement route without forcing the camera away from the user’s chosen view.

### Starting State

Sprint 002 could match one accepted coordinate to the graph, calculate a live-origin route and project later samples onto that fixed route. It had no explicit off-route evidence model, replacement-route lifecycle, request lock, cooldown or graceful reroute-failure state.

### What We Built

- A deterministic client-side off-route detector with following, checking, confirmed, rerouting, failure and arrival outcomes.
- Separate handling for GPS quality and active-route match quality.
- Bounded accuracy-aware route corridors rather than one fixed tolerance.
- Three-sample/eight-second confirmation with credible-movement requirements.
- Recovery from one anomaly and preservation of valid backtracking.
- Controlled automatic reuse of the live-origin endpoint after confirmation.
- One-request locking, ten-second route stabilization, a 30-second cooldown and a 20 m movement gate.
- Route replacement that retains destination and trusted walking pace while resetting route-specific state.
- Faded retained guidance and a **Try reroute again** action after failure.
- Deterministic active-graph-derived deviation and poor-accuracy traces.

### Technical Concepts Introduced

**Location quality** asks whether the position itself is trustworthy. **Route-match quality** asks how well that trustworthy point fits the active route. **Network-match quality** is a later server decision about whether the coordinate safely fits the complete walkable graph. **Off-route state** requires accumulated evidence; none of the first three questions alone proves departure.

A **route corridor** is a tolerance band around route geometry. It acknowledges that real GPS points rarely lie exactly on a thin mathematical LineString. The corridor expands with reported uncertainty but remains capped so weak GPS cannot make every point appear valid.

Repeated evidence is a small deterministic confidence model. It uses route distance, accuracy, sample count, elapsed time and credible movement. It is understandable, testable and does not require machine learning.

### How It Works Internally

```text
accepted GPS sample
        |
        v
is accuracy <= 25 m? ---- no ----> location uncertain
        |
       yes
        v
project onto active route
   |          |             |
 inside     between       outside
 corridor   thresholds    off-route threshold
   |          |             |
following   checking    collect reliable evidence
                              |
                    3 samples over >= 8 s
                              |
                    confirmed deviation
                              |
                 one protected POST request
                              |
             server safe match + virtual origin + A*
                              |
                       replacement route
```

The key contrast is:

```text
single anomaly
    -> check only
    -> recovery
    -> no reroute

several trustworthy samples away from route
    -> confirmed deviation
    -> controlled reroute
    -> replacement route
```

Arrival is checked before off-route action. Poor accuracy freezes the last trustworthy route state rather than advancing progress or creating evidence.

### Architecture / Components Involved

```text
user-location.js       accepted position stream
        |
        +--> live-route-progress.js   progress / pace / arrival
        |
        +--> off-route.js             corridor / evidence / cooldown
                         |
                         v
                user-navigation.js    request lock + state UX
                         |
                         v
             POST /api/routes/from-position/
                         |
                 safe graph match + A*
                         |
                         v
                      map.js           route replacement / stale style
```

The browser performs frequent projection and evidence checks. Django is contacted only after confirmation or an explicit retry.

### Important Files

- `static/yct_map/js/off-route.js` — accuracy-aware thresholds, evidence, state and cooldown.
- `static/yct_map/js/live-route-progress.js` — progress plus route replacement that preserves pace.
- `static/yct_map/js/user-navigation.js` — controlled request, route replacement, failure and retry UX.
- `static/yct_map/js/map.js` — camera-safe replacement and faded stale guidance.
- `tests/js/phase3-off-route.test.mjs` — deterministic detector behavior.
- `tests/js/fixtures/p3s3-traces.mjs` — graph-derived owner and automated traces.
- `tests/js/sprint003-public-navigation.test.mjs` — full controller replacement/failure behavior.
- `routing/matching.py`, `routing/services.py` and `routing/views.py` — unchanged server authority reused from Sprint 002.

### Data Flow

Normal accepted samples remain in browser memory. They are projected onto the active route and contribute only transient progress, pace and off-route evidence. Once deviation is confirmed, the newest coordinate, its accuracy and the existing destination UUID are sent in a CSRF-protected JSON POST. Django repeats validation and full-network matching; it does not trust the client’s conclusion.

The replacement response contains route geometry and a narrow summary. No coordinate, evidence sequence, reroute history or breadcrumb is persisted.

### Decisions and Trade-offs

**Three samples over eight seconds.** This delays recovery slightly but prevents one noisy sample from causing a request and visual disruption.

**Accuracy-aware thresholds.** Reliable 3 m samples use a tighter corridor than 25 m samples. Accuracy worse than 25 m can express uncertainty but cannot prove departure.

**Backtracking is not departure.** Walking backward still projects close to the same route. Lateral distance—not decreasing progress alone—drives off-route evidence.

**Reuse the endpoint.** Initial live routing and rerouting both mean “route from this transient position to this destination.” Reusing the protected endpoint keeps matching and privacy rules consistent.

**Automatic only after strong confirmation.** The application reroutes without another prompt when evidence is strong. A manual retry appears after failure rather than interrupting normal walking with repeated confirmation dialogs.

**Preserve pace, reset route state.** Rerouting does not change the person’s walking ability, so reliable pace samples remain. Progress, stationary timers, backward evidence and arrival confirmation belong to the old route and are reset.

### Problems Encountered

The owner trace had to exercise both the existing implausible-jump filter and the new off-route detector. Jumping instantly from an early route point to a distant alternate path would be rejected before the detector saw it. The trace therefore uses repository geometry and sufficient timestamp spacing before entering real OSM-derived way `1335008711`.

The automated browser-control connection was unavailable during implementation review. The local server, repository tests and owner’s Edge Sensors run provided verification without creating an external tunnel.

### How We Solved Them

The deterministic trace begins on the active School Building-to-Hostel route, includes one derived lateral anomaly and recovery, then moves to three points on another active mapped branch. Timing keeps the samples acceptable under Sprint 001 filtering while still satisfying Sprint 003 confirmation.

Replacement-route rendering receives an explicit replacement flag, so it updates geometry and endpoints without running the initial fit-bounds camera action. Failure reduces route opacity instead of deleting potentially useful reference guidance.

### Testing and Verification

At acceptance, 60 Django tests and 23 JavaScript tests passed. JavaScript syntax, Django system checks, migration drift and Git whitespace checks also passed.

The owner visually verified the checking state, controlled reroute, route replacement, unchanged `DEMO — Hostel` destination, continued live-position updates, decreasing remaining distance and preserved camera. Observed remaining distances included approximately 39 m, 31 m and 25 m.

Deterministic automated tests verified the exact three-sample/eight-second rule, single-anomaly recovery, poor-GPS uncertainty, backtracking, request locking, stabilization, cooldown, movement gate, failure handling, walking-pace preservation, arrival precedence and regressions. Those detailed branches are not represented as owner-manually verified.

### Current Limitations

- Physical-phone GPS/navigation/rerouting remains unverified.
- OSM-derived routing geometry and destination anchors remain `UNVERIFIED`.
- Full outside-campus behavior and city routing are absent.
- Path Survey Mode and editor GPS recording remain future work.
- No field verification has occurred.
- Route alternatives, semantic turn instructions, voice navigation and background GPS are outside this sprint.

### Evidence

- **`P3-S3-A-off-route-detected.png`** demonstrates the active route, displaced simulated live position and restrained **Checking your position…** state.
- **`P3-S3-B-rerouted-navigation.png`** demonstrates the replacement route, unchanged `DEMO — Hostel` destination, current live position and reduced remaining distance after rerouting.

Both images use simulated coordinates. Supporting failure images may be retained separately but do not replace the two primary records.

### What Students Should Understand

Students should understand that one GPS sample cannot prove departure. A sample may be accurate but laterally displaced, inaccurate but close to the route, or accurate on another network path. These conditions require different responses.

They should be able to explain route corridors, threshold scaling, repeated evidence, the distinction between active-route projection and full-network matching, and why Django repeats safety checks. They should also understand that cooldown is part of correctness: without it, a newly replaced route could immediately trigger another request because of the same GPS uncertainty.

### Presentation / Defence Notes

- **Why not reroute immediately?** One point may be noise; repeated reliable evidence is safer.
- **Why does poor GPS not mean off-route?** It reduces knowledge of position rather than proving a route departure.
- **Why is backtracking allowed?** The user remains close to route geometry even when progress decreases.
- **Why reuse the live-origin endpoint?** It already validates and safely matches transient coordinates before A*.
- **Why preserve walking pace?** Route geometry changed, not the walker.
- **Why retain a failed route?** Faded reference is more useful and honest than silently removing all guidance.
- **Was every safety branch manually tested?** No. The exact timing, cooldown, poor-GPS, failure and arrival rules are deterministic automated-test verification.
- **Was physical rerouting verified?** No. The accepted label is `SIMULATED REROUTING VERIFIED`.

### Next Sprint

Phase 3 Sprint 004 is next for discussion/planning. Its scope is not yet authorized. Full outside-campus UX, Path Survey Mode, physical-device verification and field verification remain future work unless explicitly approved.

## Phase 3 — Sprint 004: Anonymous Contributions, Moderation & Mobile Polish

**Recorded status:** OWNER ACCEPTED on 2026-09-18. Phase 3 OWNER ACCEPTED / COMPLETE.

### Purpose

This sprint completed Phase 3 by letting ordinary users report missing or incorrect campus information without accounts, while preventing unreviewed reports from changing the public map. It also refined the mobile interface so navigation and contribution panels remain usable on realistic phone screens.

### User Outcome

A user can report an existing-place correction or suggest a missing place, optionally mark a proposed point, and receive a pending-review reference. Trusted staff can approve, reject or merge the report in Django admin. Moderation records a decision but does not silently publish data. Search and navigation remain available afterward.

### Starting State

Sprint 003 had accepted simulated live navigation and controlled rerouting but no public contribution store or moderation queue. The interface was map-first and responsive, although very narrow route actions, competing floating controls and long contribution content still needed deliberate mobile ownership rules.

### What We Built

- A minimal persisted `Contribution` model with UUID identity, controlled type/status choices, optional target location, proposed place/category/point, description/context and moderation audit fields.
- A CSRF-protected anonymous JSON endpoint that always creates `PENDING` reports.
- Existing-place and missing-place form modes with optional deliberate map-point placement.
- Django-admin moderation for `APPROVED`, `REJECTED` and `MERGED` outcomes.
- UUID idempotency, bounded validation, honeypot handling, accepted-submission throttling and a separate abuse ceiling.
- Six-decimal coordinate normalization in both browser and server.
- Mobile bottom sheets, horizontally reachable categories, touch-friendly route actions, capped landscape height and foreground-panel ownership.

### Technical Concepts Introduced

**Pending-only safety** separates collecting information from publishing trusted campus data. A public user can propose a change but cannot mutate `Location`, routing or verification state.

**Moderation is not editing.** `APPROVED` means the report is useful input for later authenticated editor work. It does not mean the content is field verified and does not perform an arbitrary data transformation.

**Idempotency** uses a browser-generated request UUID. If a successful response is lost and the browser retries, Django returns the original record rather than creating a duplicate or consuming another success slot.

**Two-tier throttling** distinguishes legitimate accepted submissions from abusive traffic. Three successfully stored reports per session per ten minutes is the normal quota. A broader salted, hashed-IP ceiling also counts invalid or automated traffic so malformed requests are not unlimited.

### How It Works Internally

```text
anonymous form
   -> CSRF-protected JSON POST
   -> payload/type/target/coordinate validation
   -> accepted-submission quota check
   -> Contribution(status=PENDING)
   -> reference returned to browser
   -> authenticated Django-admin review
   -> APPROVED / REJECTED / MERGED + reviewer/time/note
   -> no automatic Location or route mutation
```

The browser keeps the current form and request UUID after recoverable failure. Proposed coordinates are rounded to six decimals before transmission and quantized again by Django before model validation.

### Architecture / Components Involved

The independent `contributions` Django application owns persistence, endpoint and admin registration. `contributions.js` owns form state and API interaction. `app.js` coordinates foreground ownership with navigation, while `map.js` provides a temporary proposed-point layer. Existing location and routing services are referenced but never mutated by submission or moderation.

### Important Files

- `contributions/models.py` — pending report and moderation audit model.
- `contributions/views.py` — validation, normalization, throttling and idempotent submission.
- `contributions/admin.py` — authenticated moderation.
- `static/yct_map/js/contributions.js` — form modes, retry and point payload.
- `static/yct_map/css/app.css` — mobile sheets, controls and narrow layouts.
- `tests/js/phase3-contributions.test.mjs` and `phase3-mobile-layout.test.mjs` — browser-state and responsive contracts.
- `contributions/tests/test_contributions.py` — endpoint, security, throttling and moderation tests.

### Data Flow

Only intentionally entered report fields and an intentionally chosen proposed point reach Django. No live-location history, breadcrumb, student identifier, email or telephone number is attached. Staff decisions add reviewer and timestamp fields. Public location responses continue reading `Location`, not approved contributions.

### Decisions and Trade-offs

We used Django admin rather than a custom editor because full editor tooling belongs to Phase 4. This is less polished than a purpose-built review queue but gives authenticated, permission-backed moderation without expanding scope.

Coordinates remain ordinary decimal fields rather than PostGIS geometry because one optional proposed point does not justify spatial infrastructure. Six decimal places provide sub-metre numeric resolution while keeping the schema portable.

The local throttle uses process memory, which is sufficient for owner testing but requires a shared production cache before multi-instance deployment.

### Problems Encountered

Owner testing found an integration defect that the initial automated examples missed:

```text
high-precision MapLibre coordinates
    -> Django six-decimal validation returned HTTP 422
    -> repeated retries consumed the normal session quota
    -> HTTP 429 hid the original problem
```

The visible form looked complete because the invalid precision existed only in the generated map-point payload. Generic error copy did not identify the selected point.

### How We Solved Them

The client rounds coordinates before building the payload, and the server independently validates finite numeric values then quantizes to six decimals. Coordinate failures now receive intentional map-point feedback. Validation failures no longer consume the three-success quota; a separate 30-request hashed-IP abuse ceiling still bounds malicious invalid traffic. Regression tests use realistic MapLibre precision.

### Testing and Verification

At acceptance, 74 Django tests and 34 JavaScript tests passed. JavaScript syntax, Django system checks, migration drift and whitespace checks were clean. The owner verified both submission types, a proposed point, pending records, approval, rejection with a note, reviewer audit fields, unchanged public data, manual routing and mobile routing around 360×800.

Automated tests verify validation, normalization, throttling, abuse protection, idempotency, failure/retry preservation, accessible status behavior, responsive contracts and all previous regressions.

### Current Limitations

- Approval requires later authenticated editor action and does not publish data.
- Full editor CRUD, real campus place modeling, entrance management, floors/internal places, path editing and Path Survey Mode are absent.
- Throttling uses process-local cache in development.
- Demo destinations and the `UNVERIFIED` OSM-derived graph remain.
- Physical-phone GPS/navigation/rerouting and all field verification remain unverified.

### Evidence

- **`P3-S4-A-anonymous-contribution.png`** demonstrates map context, successful submission, pending-review wording and the report reference.
- **`P3-S4-B-mobile-navigation-polish.png`** demonstrates the active route at approximately 360×800, visible map, full-width route sheet, summary and touch-friendly actions.
- Supporting admin images demonstrate pending, approved and rejected states without claiming public-data mutation.

### What Students Should Understand

Students should be able to explain why accepting anonymous input is different from trusting or publishing it; how controlled choices, server validation, CSRF and staff authorization protect the boundary; and why moderation status is not field verification. They should understand idempotency and the difference between a successful-submission quota and a malicious-request ceiling.

They should also be able to explain why browser-generated floating-point coordinates must be normalized at integration boundaries, why both client and server participate, and why owner testing is essential even with a green automated suite. Responsive foreground ownership is application state, not only CSS: hiding a route sheet must not destroy its route.

### Presentation / Defence Notes

- **Why no account for contributors?** Navigation and community reporting are intentionally lightweight; trust is established through moderation, not forced identity.
- **Why does approval not move the map?** A report is evidence for an editor, not a safe universal update instruction.
- **Why normalize twice?** Client rounding produces a clean contract; server quantization enforces authority against arbitrary clients.
- **Why did tests miss the first defect?** Initial fixtures used short decimal examples rather than real MapLibre precision.
- **How is spam limited?** Successful reports have a small session quota; all traffic also faces a broader non-PII hashed-IP ceiling.
- **Was physical navigation verified?** No. Phase 3 acceptance preserves a simulated-versus-physical boundary.

### Next Sprint

Phase 3 is complete. The next permitted activity is Phase 4 specification integration and planning. No Phase 4 implementation is authorized without an approved sprint plan and standalone `BUILD` command.

## Phase 3 Summary — Live Navigation & Core Product Systems

### Achievements

Four sprints transformed static routing into a privacy-conscious simulated live-navigation product and added a safe community-reporting channel. Sprint 001 established browser geolocation and filtering; Sprint 002 connected transient positions to the graph and tracked route progress/ETA; Sprint 003 confirmed genuine deviation before controlled rerouting; Sprint 004 added pending moderation and mobile polish.

### Resulting Architecture

```text
Geolocation API -> raw sample filter -> accepted transient position
       -> route/network projection -> virtual origin -> existing A*
       -> progress + pace + ETA + stationary/arrival state
       -> route-corridor evidence -> controlled reroute

Anonymous report -> validated PENDING contribution -> staff decision
                  -> later editor action (not automatic publication)
```

Raw and accepted GPS positions are separate. Accuracy metadata controls whether samples may update the marker, pace, progress or off-route evidence. Server matching inserts only request-local virtual graph origins. Frequent progress and evidence calculations remain in browser memory; reroute requests reuse the protected live-origin endpoint.

### Major Concepts Learned

- Browser permission and `getCurrentPosition`/`watchPosition` lifecycle.
- GPS uncertainty, sample filtering and implausible-jump protection.
- Polyline network matching, virtual origins and A* reuse.
- Route projection, personal walking speed, 1.35 m/s fallback ETA, stationary state and confirmed arrival.
- Accuracy-aware route corridors, repeated off-route evidence, stabilization, cooldown and request locking.
- Pending moderation, auditability, idempotency, CSRF and layered throttling.
- Transient-location privacy and responsive foreground ownership.

### Important Problems and Solutions

Unsafe graph matches were rejected rather than weakening thresholds. Deterministic traces were derived from the active graph rather than guessed. Off-route evidence was accumulated instead of reacting to one sample. Failed reroutes retained faded guidance. MapLibre precision was normalized at both sides of the API, and validation failures were separated from accepted-submission throttling.

### Evidence

Phase 3 evidence comprises the accepted Sprint 001 live-location images, Sprint 002 live-route/progress images, Sprint 003 off-route/reroute images and Sprint 004 contribution/mobile-polish images. All GPS/navigation evidence uses simulated coordinates unless explicitly stated otherwise.

### Current System Capabilities

YCT Map now supports searchable DEMO destinations, OSM-derived `UNVERIFIED` campus routing, manual and safely matched live origins, route progress, dynamic/fallback ETA, stationary and arrival logic, controlled rerouting, anonymous pending contributions, staff moderation and responsive mobile panels.

### Transition to the Next Phase

Phase 4 will establish authenticated editor and campus-data tooling. It must preserve the distinction between moderation, editor review and `FIELD_VERIFIED` data. Physical-device verification, real campus population, entrance/internal-place tools, path editing and Path Survey Mode remain future work.
