# Phase 4 Final Physical Field Acceptance Checklist

This is the definitive real-device and real-campus acceptance procedure for **Phase 4 Sprint 004**.

Complete it on a physical phone at YabaTech. Automated tests are supporting evidence only: they do not pre-approve any item in this checklist.

## How to Record Results

For every check, enter exactly one result:

- `PASS` — personally tested and the stated behavior was observed.
- `FAIL` — personally tested and a concrete defect was observed.
- `NOT TESTED` — not performed or insufficient evidence was available.

Do not leave a performed check ambiguous. Record concise notes and an evidence reference where useful. Do not record private precise personal-location history beyond what is necessary to identify the campus test.

## Test Evidence Header

| Field | Record |
|---|---|
| Date | |
| Owner/tester | |
| Device | Samsung S21+ or equivalent: |
| Browser and version | |
| Tunnel URL | |
| Physical route walked | Describe generally; avoid unnecessary personal-location history. |
| Screenshots | |
| Video | |
| General notes | |

## Preconditions

Do not begin until each precondition is confirmed. Preconditions are preparation checks, not product acceptance results.

| Precondition | Confirmed (`YES` / `NO`) | Notes |
|---|---|---|
| Samsung S21+ or equivalent physical phone is available. | | |
| Tester is physically at the YabaTech campus. | | |
| Current Django development server is running. | | |
| Current Cloudflare HTTPS Quick Tunnel is running. | | |
| A fresh browser tab loads current application assets. | | |
| Owner can log in where editor access is required. | | |
| No segment has been granted `FIELD_VERIFIED` before evidence review. | | |
| Tester understands that Quick Tunnel is development-only. | | |

If a required precondition is `NO`, record affected sections as `NOT TESTED`; do not convert them to `FAIL` unless the application itself caused the precondition failure.

---

## A. Public Mobile Map

Use the normal mobile browser mode, not forced desktop-site mode.

| # | Test | Result (`PASS` / `FAIL` / `NOT TESTED`) | Notes and screenshot/video reference |
|---|---|---|---|
| A1 | Public map loads through the HTTPS tunnel. | | |
| A2 | Header, search and category rail fit the mobile viewport. | | |
| A3 | Every category can be reached by horizontal scrolling. | | |
| A4 | Public Menu opens above every HUD and map control. | | |
| A5 | Tapping outside closes Menu without activating the map or a control underneath. | | |
| A6 | Required map attribution remains compact by default and can be expanded. | | |
| A7 | Locate Me, zoom, status and developer tools do not collide. | | |
| A8 | Portrait orientation remains usable. | | |
| A9 | Short landscape orientation remains usable. | | |

**Section A result:** `PASS / FAIL / NOT TESTED`  
**Section A notes/evidence:**

---

## B. Live Location

Perform this outdoors where practical.

| # | Test | Result (`PASS` / `FAIL` / `NOT TESTED`) | Notes and screenshot/video reference |
|---|---|---|---|
| B1 | Tap **Locate Me** and receive a location response. | | |
| B2 | Warm-up or quality-improving state appears before the location is treated as stable. | | |
| B3 | Remain stationary for 30–60 seconds. | | Duration: |
| B4 | Marker remains reasonably stable while stationary. | | |
| B5 | Accuracy halo remains visible and reflects reported uncertainty. | | |
| B6 | Wording describes estimated uncertainty rather than guaranteed precision. | | |
| B7 | Location quality/stability wording is understandable. | | |
| B8 | Heading is suppressed while stationary or unreliable. | | |
| B9 | Walk slowly for 10–30 metres. | | Approximate distance: |
| B10 | Continue at a normal walking pace. | | Approximate distance/time: |
| B11 | Marker releases promptly from stationary stabilization when genuine movement begins. | | |
| B12 | Marker does not snap to a route, building or destination. | | |
| B13 | After a location failure/restart, no obviously stale position is reused as current. | | |

### Section B pass criteria

- No severe stationary wandering.
- Genuine movement appears without excessive lag.
- Uncertainty is communicated honestly.
- No room-level precision claim is made.

**Section B result:** `PASS / FAIL / NOT TESTED`  
**Section B notes/evidence:**

---

## C. Live Routing

Use a known routable destination. Prefer an Entrance with confirmed arrival-connector geometry.

**Destination used:**  
**Entrance used:**

| # | Test | Result (`PASS` / `FAIL` / `NOT TESTED`) | Notes and screenshot/video reference |
|---|---|---|---|
| C1 | Select the destination. | | |
| C2 | Choose **Use my live location**. | | |
| C3 | Calculate the route successfully. | | |
| C4 | Map remains geographically centred around YabaTech rather than zooming absurdly outward. | | |
| C5 | Current position, highlighted route and destination are visible. | | |
| C6 | Route card automatically collapses to its compact active state. | | |
| C7 | Destination, remaining/route distance and ETA are shown. | | |
| C8 | Expand **Details** successfully. | | |
| C9 | Collapse **Details** successfully. | | |
| C10 | Pan and zoom remain usable during the active route. | | |
| C11 | Public Menu opens and closes correctly while the route is active. | | |
| C12 | Route panel stays inside the viewport; all controls, including **End**, remain visible. | | |
| C13 | Select **End** and confirm normal browsing state is fully restored. | | |

### Section C pass criteria

- Map remains the dominant surface.
- Route camera stays locally meaningful.
- Route panel does not cover most of the map or overflow the viewport.
- Ending the route restores browsing cleanly.

**Section C result:** `PASS / FAIL / NOT TESTED`  
**Section C notes/evidence:**

---

## D. Exact Entrance Arrival

Use an Entrance with explicitly approved connector geometry.

**Place:**  
**Entrance:**  
**Connector reviewed by:**

| # | Test | Result (`PASS` / `FAIL` / `NOT TESTED`) | Notes and screenshot/video reference |
|---|---|---|---|
| D1 | A* portion of the route follows the walkable graph. | | |
| D2 | Route continues beyond the anchor node through the approved connector. | | |
| D3 | Final route coordinate reaches the physical Entrance point. | | |
| D4 | Destination marker sits at the physical Entrance. | | |
| D5 | Displayed distance includes connector distance. | | |
| D6 | Displayed ETA includes connector distance. | | |
| D7 | Representative Location point remains unchanged and independent. | | |

Visible backtracking caused by connecting through an existing node should be recorded below as `KNOWN LIMITATION`, not automatically as `FAIL`, provided the route still honestly reaches the Entrance.

**Known node-first backtracking observed:** `YES / NO / NOT TESTED`  
**Known-limitation notes:**  
**Section D result:** `PASS / FAIL / NOT TESTED`

---

## E. Internal Place Handoff

Use **LR3** or another InternalPlace.

**InternalPlace:**  
**Parent Place:**  
**Resolved Entrance:**

| # | Test | Result (`PASS` / `FAIL` / `NOT TESTED`) | Notes and screenshot/video reference |
|---|---|---|---|
| E1 | Search finds the InternalPlace. | | |
| E2 | Destination details show the parent Place. | | |
| E3 | Destination details show the Floor. | | |
| E4 | Destination details show the room/code. | | |
| E5 | Wing/section appears when present. | | |
| E6 | Direction note appears when present and remains distinct from general description. | | |
| E7 | Directions use the configured active same-parent routing Entrance when present. | | |
| E8 | Otherwise, Directions use the parent active primary Entrance. | | Mark `NOT TESTED` if E7 applies. |
| E9 | Route UI does not claim indoor route geometry. | | |
| E10 | Outdoor arrival names the building Entrance, not the room. | | |
| E11 | Internal guidance remains available after routing begins. | | |
| E12 | If live arrival is safely detected, the UI announces the Entrance and then presents textual internal guidance. | | May be `NOT TESTED` if safe arrival is not detected. |

### Section E semantic pass condition

```text
OUTDOOR ROUTE
      ↓
BUILDING ENTRANCE
      ↓
TEXTUAL INDOOR HANDOFF
```

**Section E result:** `PASS / FAIL / NOT TESTED`  
**Section E notes/evidence:**

---

## F. Path Survey Lifecycle

Create a **new** survey. Do not reuse historical survey classifications.

**New survey UUID:**  
**Mapped path/area:**

| # | Test | Result (`PASS` / `FAIL` / `NOT TESTED`) | Notes and screenshot/video reference |
|---|---|---|---|
| F1 | Create a new survey. | | |
| F2 | Start the survey. | | |
| F3 | Explicitly select **Begin GPS Capture**. | | |
| F4 | Remain stationary for approximately 20 seconds. | | Actual duration: |
| F5 | Walk slowly for approximately 30 seconds. | | Actual duration/distance: |
| F6 | Walk normally along a known mapped path for 60–120 seconds. | | Actual duration/distance: |
| F7 | Live raw, accepted, weak and rejected counters are visible. | | |
| F8 | Active-capture time advances only while capture is active. | | |
| F9 | Current-position marker is visible. | | |
| F10 | Evidence trace uses accepted/usable samples and is not distorted by rejected readings. | | |
| F11 | Temporarily interrupt connectivity. | | Method and duration: |
| F12 | Restore connectivity. | | |
| F13 | Buffered samples synchronize and authoritative counters recover. | | |
| F14 | Pause the survey and confirm collection stops. | | |
| F15 | Reload or reopen the paused survey. | | |
| F16 | GPS capture does not restart automatically. | | |
| F17 | Resume capture explicitly. | | |
| F18 | Walk briefly and observe new evidence. | | |
| F19 | Finish the survey. | | |

### Final authoritative counters

| Counter | Final value |
|---|---:|
| Raw | |
| Accepted | |
| Weak | |
| Rejected | |

### Rejection reasons

| Reason | Count/observation |
|---|---|
| Poor accuracy | |
| Stationary/downsampled duplicate | |
| Implausible jump/outlier | |
| Other | |

### Section F pass criteria

- Raw evidence is preserved.
- High-frequency stationary observations may be downsampled without treating callback frequency as movement evidence.
- Slow and normal walking produce meaningfully usable evidence.
- Connectivity interruption causes no silent evidence loss.
- Pause/resume/reopen behavior remains explicit.
- Completed counters are authoritative.

**Section F result:** `PASS / FAIL / NOT TESTED`  
**Section F notes/evidence:**

---

## G. Survey Match Review

Complete this only after Section F finishes successfully enough to produce reviewable evidence.

| # | Test | Result (`PASS` / `FAIL` / `NOT TESTED`) | Notes and screenshot/video reference |
|---|---|---|---|
| G1 | Inspect the primary candidate matches. | | |
| G2 | Expand low-support diagnostics. | | |
| G3 | Effectively 0%-coverage/minimal-evidence noise is de-emphasised in the primary review list. | | |
| G4 | Genuine discrepancies remain visible. | | |
| G5 | Coverage approximately represents the segment portions actually walked. | | |
| G6 | Repeated OSM way IDs remain distinguishable as separate segment records where applicable. | | |
| G7 | Only paths with sufficient cumulative independent finalized evidence may become `FIELD_VERIFIED` when the new survey completes; unrelated paths remain unchanged. | | |
| G8 | A newly sufficient path disappears from Needs Confirmation, while ambiguous/conflicting evidence remains for human review. | | |

### Candidate interpretation record

| Segment UUID | Source/OSM reference | Classification | Coverage | Reviewer interpretation |
|---|---|---|---:|---|
| | | | | |
| | | | | |
| | | | | |

Do not use a manual grant during this section. Record any automatic one-way promotion produced by survey completion, including the contributing survey/pass evidence.

**Section G result:** `PASS / FAIL / NOT TESTED`  
**Section G notes/evidence:**

---

## H. Manual `FIELD_VERIFIED` Control Test

Perform this only when explicit human override/review still has a justified use after cumulative evaluation. Never grant verification merely to complete this checklist.

**Segment UUID:**  
**Pre-test revision:**  
**Pre-test fingerprint:**  
**Evidence/survey UUID:**

| # | Test | Result (`PASS` / `FAIL` / `NOT TESTED`) | Notes and screenshot/video reference |
|---|---|---|---|
| H1 | Confirm the current segment revision and fingerprint. | | |
| H2 | Confirm evidence is sufficiently trustworthy for an explicit verification decision. | | |
| H3 | Grant `FIELD_VERIFIED` through the authorized workflow. | | |
| H4 | Confirm an append-only verification record exists. | | Record UUID: |
| H5 | Confirm unrelated segments remain unchanged. | | |
| H6 | If safe, revoke verification afterward. | | May be `NOT TESTED`. |
| H7 | If revoked, confirm grant and revoke history both remain. | | May be `NOT TESTED`. |

Do not mutate production-like geometry merely to prove invalidation; automated coverage already exercises material-edit invalidation.

If evidence is not trustworthy enough, record the section result exactly as:

`NOT TESTED — INSUFFICIENT FIELD EVIDENCE`

**Section H result:** `PASS / FAIL / NOT TESTED — INSUFFICIENT FIELD EVIDENCE`  
**Section H notes/evidence:**

---

## I. Quick Editor Regression

Run from the phone or a laptop through the current build.

| # | Test | Result (`PASS` / `FAIL` / `NOT TESTED`) | Notes and screenshot/video reference |
|---|---|---|---|
| I1 | Editor login succeeds for an authorized owner/editor. | | |
| I2 | Compact mobile editor menu is usable. | | |
| I3 | Places list/detail opens. | | |
| I4 | Entrance edit opens and saves an ordinary valid edit. | | |
| I5 | Floor edit opens and saves an ordinary valid edit. | | |
| I6 | InternalPlace edit opens and saves an ordinary valid edit. | | |
| I7 | Paths overview opens. | | |
| I8 | Path Surveys list/detail opens. | | |
| I9 | A normal authorized form POST succeeds without a CSRF debug page. | | |
| I10 | Logout succeeds. | | |
| I11 | No horizontal overflow obstructs the editor workflow. | | |
| I12 | No control or direct URL exposes unauthorized functionality. | | |

**Section I result:** `PASS / FAIL / NOT TESTED`  
**Section I notes/evidence:**

---

## J. Contribution Safety Boundary

Detailed `ContributionResolution` owner QA remains intentionally deferred. Do not expand this section into that deferred workflow.

| # | Safety check | Result (`PASS` / `FAIL` / `NOT TESTED`) | Notes and screenshot/video reference |
|---|---|---|---|
| J1 | An anonymous contribution does not directly publish campus data. | | |
| J2 | Contribution approval does not grant `FIELD_VERIFIED`. | | |
| J3 | Contribution approval does not silently mutate public campus records. | | |

**Detailed ContributionResolution workflow:** `DEFERRED BY OWNER`  
**Section J result:** `PASS / FAIL / NOT TESTED`  
**Section J notes/evidence:**

---

## Final Acceptance Decision

Copy each section's recorded result into this table. Do not infer a result from automated tests.

| Acceptance area | Final result (`PASS` / `FAIL` / `NOT TESTED`) | Key evidence or blocker |
|---|---|---|
| Public mobile map | | |
| Live location | | |
| Live routing | | |
| Exact entrance arrival | | |
| InternalPlace handoff | | |
| Path Survey lifecycle | | |
| Offline/buffer recovery | | |
| Survey matching | | |
| Verification control | | |
| Editor regression | | |
| Contribution safety boundary | | |

### Overall status

Select exactly one only after reviewing every section:

- [ ] **SPRINT 004 — OWNER ACCEPTED**
- [ ] **SPRINT 004 — NOT ACCEPTED**

If **NOT ACCEPTED**, list only concrete observed blockers:

1. 
2. 
3. 

If **OWNER ACCEPTED**, the authorized next sequence is:

1. final regression sweep;
2. Build Journal Sprint 004 finalization;
3. milestone commit after separate authorization;
4. Phase 4 closure reconciliation.

Owner name/sign-off:  
Decision date:  
Final evidence references:

PHASE 4 FIELD ACCEPTANCE — PENDING OWNER EXECUTION
