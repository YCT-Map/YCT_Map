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
