# SWITCH — Smart-Home Routine Verification, Replay and Regression Requirements

> **SIMULATED DEMO.** Nothing here controls real devices. There is **no Amazon / Alexa+ connection** (the Alexa+
> experience is an in-app simulation, labelled as such), no physical device, and no live LLM. Every device, sensor,
> scenario and result is modeled. A PASS means only that the selected modeled requirements passed for the recorded
> scenarios and versions — it does not certify a real home.

**A fix today should not become a failure tomorrow.** SWITCH turns a household's explicitly confirmed correction
("Don't turn off the hallway light while someone is there") into a versioned regression requirement, replays it against
later routine edits in a deterministic simulator, shows the evidence, proposes a constrained repair, reruns the suite,
and leaves the decision to a person.

**Authoritative status, evidence and limitations: [FINAL_SUBMISSION_STATUS.md](./FINAL_SUBMISSION_STATUS.md).**
Also: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) · [docs/CONTRACTS.md](docs/CONTRACTS.md) ·
[docs/ALEXA_PLUS_INTEGRATION.md](docs/ALEXA_PLUS_INTEGRATION.md) · [docs/VERIFICATION.md](docs/VERIFICATION.md) ·
master spec in `docs/SWITCH_Complete_Merged_Master_Specification_AlexaPlus.pdf`.

## What you will see

* **Landing page:** the giant **SWITCH** wordmark types itself in. The SWITCH logo sits inside the
  [React Bits](https://reactbits.dev) **Orb** (WebGL2; it follows the cursor and pulses on click, with a static fallback
  when WebGL2 is unavailable), above a live preview of the 3D villa. **Explore Your Home** opens the app; **Talk to
  SWITCH** opens it with the assistant.
* **SWITCH Assistant:** a simulated Alexa+-style chat that runs every action on the real backend. Say a correction,
  then "yes, save it as a rule", "what changed in Goodnight?", "check it", "why did it fail?", "fix it", "run the checks
  again", "approve it". Results appear as clean cards (rule, diff, replay verdict, failed assertion with its trace event,
  repair, decision), never raw JSON. Full script: [docs/JUDGE_WALKTHROUGH.md](docs/JUDGE_WALKTHROUGH.md).
* **Floating dock** (bottom of the screen): Home, Search, Assistant, Routines (Replay Lab), House view, Saved
  Requirements, Reports, Notifications, Theme and Settings. It magnifies on hover, bounces on click, shows tooltips,
  marks the active page, carries real badges and supports ←/→ keyboard navigation.
* **Themes:** dark (graphite/cyan) and light (terracotta/gold), saved per browser.

## Requirements

* **Node.js 20+** (tested with 22) and npm.
* **Python 3.11+** for the backend; **3.13** recommended (the optional ML artifacts were serialized with Python 3.13,
  scikit-learn 1.9.1, NumPy 2.5.3, pandas 3.0.5 — pinned in `switch_backend/requirements.txt`).
* A desktop browser with WebGL (Chrome/Edge/Firefox/Safari).

## Quick start

| OS | Command (from the project root) |
|---|---|
| Windows | double-click `start-switch.bat` (or `powershell -ExecutionPolicy Bypass -File start-switch.ps1`) |
| macOS / Linux | `./start-switch.sh` |

The scripts create `switch_backend/.venv`, install the pinned backend requirements, run `npm ci` if needed, start the
backend on **http://127.0.0.1:8000** (API docs at `/docs`) and the app on **http://127.0.0.1:5173**.

### Windows, step by step

1. Install **Python 3.13** (python.org; tick "Add python.exe to PATH" and "py launcher") and **Node.js 20+** (nodejs.org, LTS).
2. Extract the ZIP, open the `SWITCH_FINAL_SUBMISSION_READY` folder and double-click **`start-switch.bat`**.
   The first run creates `switch_backend\.venv`, installs the backend requirements and runs `npm ci` (a few minutes).
3. A second window titled *SWITCH Person 2 Backend - SIMULATED* runs the API on http://127.0.0.1:8000. The first window
   runs the app.
4. Open **http://127.0.0.1:5173** in Chrome or Edge.
5. To stop, close both windows.

PowerShell alternative: `powershell -ExecutionPolicy Bypass -File start-switch.ps1`. Manual Windows commands:

```bat
cd switch_backend
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m app
:: second terminal, project root
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

Problems? See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

### Manual start

```bash
# terminal 1 — backend (SIMULATED DEMO)
cd switch_backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app                        # defaults: SWITCH_ENV=demo, SWITCH_DEMO_PROFILE=journey, SWITCH_DB=data/switch.db

# terminal 2 — frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

The database `switch_backend/data/switch.db` is created and migrated on first start and seeded with the demo
household. **Settings → Reset demo** (or `POST /demo/reset {"profile":"journey"}`) restarts the story at any time.
If the backend is not running, the app still works with the in-browser simulator and labels every result
**LOCAL / offline fallback**; open `/?offline` to force that mode.

## Tests and build

```bash
npm test                    # 77 Node tests: simulator, app store, GLB geometry/collision, canonical mapping, assistant (incl. a real-backend journey)
npm run test:integration    # 8 tests: the browser store driven through a REAL backend process (full journey, reset, offline)
npm run backend:test        # 143 pytest tests (119 original Person 2/3C + 24 integration tests)
npm run build               # production build (dist/)
# browser end-to-end (needs both servers running):
npm i --no-save playwright @axe-core/playwright && npx playwright install chromium
node tools/e2e_journey.mjs http://127.0.0.1:5173 http://127.0.0.1:8000
```

`npm run test:integration` uses `switch_backend/.venv` (or `$SWITCH_PYTHON`, else `python3`).
Actual results of every suite are recorded in [FINAL_SUBMISSION_STATUS.md](./FINAL_SUBMISSION_STATUS.md).

## The 2-minute demo (canonical journey)

1. **Home** — note `SIMULATED DEMO` and `Backend connected` in the top bar. The villa is the live house simulator.
2. **Saved Requirements** — the correction box already contains *"Don't turn off the hallway light while someone is
   there."* → **Draft requirement**. Person 3C's rule-based interpreter proposes the structured rule (hallway light must
   not be set OFF while the hallway is occupied); it is saved as a **DRAFT**, not enforced. Try *"Don't turn off the
   light while someone is there"* to see a clarification question ("Which light?") — nothing is saved until answered.
3. **Confirm & save** → `req-… v1 CONFIRMED` (owner confirmation recorded with time and version).
4. **Replay Lab** — the diff shows the pending Goodnight edit (`v2`) removed *"unless Hallway is occupied"*.
   **Run Replay** → **FAIL**: occupancy=true (E0001) → Goodnight fires (E0002/E0003) → hallway light ON→OFF (**E0006**)
   violates the requirement. The timeline flags the event; the 3D house below shows the hallway at that event with the
   light outlined in red. Approve is disabled.
5. **Apply Suggested Fix** → a rule-based repair restores the guard, validated by Person 3C's constrained-repair
   checker, shown as a diff, marked **NOT VERIFIED** (candidate `v3`).
6. **Re-run Regression Suite** → **PASS** on all 5 relevant tests → **Approve candidate** (recorded, nothing deployed).
7. **Reports** → the run's versions, trace, assertions, repair provenance and reviewer decision; **Export JSON /
   Markdown** or **Print / Save as PDF**. **Why SWITCH** now shows this journey from your own records.
8. **Alexa+ (simulated)** in the top bar: *"Propose a fix"*, *"Re-run the checks"*, *"Approve the change"* (asks for an
   explicit yes) — every answer is a real SWITCH tool result; the UI updates.
9. Optional: tick the *hallway sensor offline* edge case and replay → **INCONCLUSIVE**, never a false PASS
   (exploratory runs never count towards approval).

## What's in the app (seven pages)

| Page | What it does |
|---|---|
| **Home Overview** | The 3D villa (Exterior / Cutaway / Room tour / Walk, numbered rooms 1–8, fullscreen, day/night). Right rail: selected room/device, latest replay (with engine provenance), requirements at risk, active routines (canonical live versions), recent activity. Action strip: Run Replay, Compare Changes, View Trace, Review Proposed Fix. |
| **Why SWITCH** | The correction-to-regression story: an illustrated walkthrough computed by the in-browser engine, plus **Your recorded journey** built from your real backend records (correction, version, diff, trace, failed assertion, repair, rerun, decision). |
| **Replay Lab** | Candidate diff, deterministic event timeline (with condition evaluations), assertions, repair proposal with provenance, Run Replay / Apply Suggested Fix / Re-run / Reset Scenario / View Trace, edge-case (exploratory) runs, candidate selector, human decision, and the 3D house replaying the trace. |
| **Saved Requirements** | Capture a correction → interpretation → clarification → DRAFT → explicit confirmation. Library with filters, structured editing (title, expected behaviour, occupancy/time preconditions, routine scope, scenarios, open questions) creating new versions, disable / re-enable / retire, version history. |
| **Reports** | Canonical run records: run id, kind, scenario/requirement/routine/simulator versions, integration provenance, fingerprint, assertions with evidence events, repair provenance, comparison to the previous run, reviewer decision, timelines. Exports: JSON (canonical record), Markdown, Print / Save as PDF. |
| **Devices / Integrations** | 26 modeled devices (state, controls, controlling routine, canonical id) and backend-only devices; live status of the SWITCH backend, Alexa+ (Route C, **SIMULATED DEMO**, harmless connection test), Person 3C interpretation; unimplemented connectors labelled NOT IMPLEMENTED; embedded Alexa+ panel. |
| **Settings** | Verification engine (backend vs offline), house view, render quality, day/night, reduced motion, simulator speed, resets (including backend demo reset), data status, privacy & retention. |

## How the 3D house works

* **Blender authors, three.js runs.** `blender/build_villa.py` builds the villa procedurally (original reconstruction from screenshots, no third-party geometry). It names every interactive object and writes metadata as glTF extras (`device_id`, `kind`, `room`, `level`). It also exports eye-level room cameras (`CAM_<ROOM>` empties with a look-at target). The app loads only the local `public/models/switch_villa.glb`.
* **Single source of truth.** `src/sim/engine.js` (deterministic simulator) owns device and sensor state and the ordered trace. `src/state/appStore.js` wires the simulator, requirements, runs, selection and settings. The 3D house, panels, device table and timelines all read the same objects, so they cannot disagree.
* **Device mapping.** `src/three/houseRegistry.js` maps simulator device IDs to GLB nodes by name and extras, never by mesh index. A test proves all 26 devices map, and that every GLB device is known to the simulator.
* **Lights.** One runtime point light per (light device × room zone) and emissive bulb materials, each independent per device ID. A small shader patch (`src/three/sceneSetup.js`) makes a point light affect only fragments inside the room zone that contains it, so lights don't leak through walls without costly point-light shadows.
* **Fans, AC, TV and more.** Fan blades rotate about their own pivot at the modeled rpm, and stop when off. AC shows louver swing, a mode-coloured LED and an airflow cone while the modeled duty is above 5%. Temperature changes gradually (first-order thermal model). The TV screen glows and lights the room. Also modeled: purifier vanes, coffee/security/motion LEDs, and sliding or hinged doors that animate.
* **Room tour and walk mode.** `src/three/walker.js` is a capsule character controller against a three.js `Octree` of the real triangles. Walls, glass, furniture and ceilings block it. Closed doors block as dynamic boxes and open doors let you through. Stairs are climbed with a 0.30 m step height, so you can walk from the living room up to Bedroom 3. Room tour limits movement to the selected room's box. The same walker is used by the Node tests.
* **Cutaway.** One shared clipping plane cuts architecture at 2.72 m (ground) or 5.35 m (upper). Roof and upper storey are hidden for the ground cut. Devices, terrace furniture and the site stay visible, and everything is restored on exit.
* **Day/night** (`src/sim/daylight.js`). The browser's local time and date give a sun position (documented formula, latitude setting only for season length, location never requested). Elevation is blended through a key table into sky colours, sun/moon/hemisphere intensity, exposure and stars, and transitions ease smoothly. Manual mode previews any time and date. It never changes device state, and replays use their own deterministic clock.

### Optional: regenerate the 3D model (Blender 5.2 via the `bpy` module, Python 3.13)
```
py -3.13 -m venv venv                         (macOS/Linux: python3.13 -m venv venv)
venv\Scripts\pip install bpy==5.2.2 pillow numpy
venv\Scripts\python blender\build_villa.py    -> blender/out/switch_villa.blend + public/models/switch_villa.glb
npm run test:geometry                         -> re-validates cameras, rooms, devices and collision on the new GLB
```

## Trust boundary

AI may interpret a correction or propose a repair. Only the deterministic evaluator (`switch_backend/app/assertions.py`)
returns PASS / FAIL / INCONCLUSIVE, and only an authorized person can approve a candidate. The interpreter is Person
3C's rule-based engine (no live LLM is configured); repairs are rule-derived and validated against a constrained
allowlist. Unknown or unsupported states yield INCONCLUSIVE. Approval is recorded; deployment is not implemented.

## Project map

```
contracts/canonical_home.json   shared room/device contract (backend, Person 3C, frontend)
switch_backend/app/             FastAPI: main (routes), services, simulator, assertions, regression, diff, store,
                                p3c_bridge (Person 3C <-> Person 2), alexa_adapter (Route C), fixtures/seed (profiles)
switch_backend/switch_p3c/      Person 3C: interpreter, repair validator, optional LLM provider, ML artifacts
switch_backend/tests/           143 pytest tests
src/state/                      appStore (single store), canonicalWorkflow (backend provider), StoreContext
src/api/                        switchBackend (client), canonicalMap (pure mapping), backendBridge (compat)
src/sim/                        browser house simulator + offline workflow (switch.js), rooms, daylight
src/three/                      3D viewer (HouseViewer, sceneSetup, houseRegistry, walker, Environment)
src/pages/, src/ui/             seven pages, device UI, assistant panel (AlexaPanel, simulated Alexa+), floating Dock
src/assistant/                  assistant.js (intent routing + typed result cards), session.js (context, confirmations, backend tool calls)
src/landing/                    Landing page + TypewriterWordmark
src/components/reactbits/Orb/   React Bits Orb (upstream source + CSS, MIT + Commons Clause licence)
public/brand/                   SWITCH logo (cut from the supplied intro video's final frame)
tests/                          Node tests incl. canonical, assistant and backend_store tests; fixtures/backend_journey.json
tools/e2e_journey.mjs           browser E2E of the canonical journey (+ a11y, responsive)
public/models/switch_villa.glb  runtime 3D model; blender/ sources
```

## Appearance themes

SWITCH includes a persisted theme toggle in the top bar. Dark mode remains the original graphite / deep-slate and cyan theme. Light mode uses a warm terracotta sky with gold accents. Both themes add translucent glass-style cards and subtle pointer-following edge highlights. Theme preference is saved in browser localStorage when available. Reduced-motion preferences disable hover transitions.
