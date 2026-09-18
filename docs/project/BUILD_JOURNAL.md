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
