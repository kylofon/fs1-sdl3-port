# Flight Simulator 1 (MS FS 1.05, 1982) — SDL3 port plan

A faithful C port of Microsoft Flight Simulator 1.05 for the IBM PC, followed by enhancements.

- **Phases 0–3 are done.** The original ran on our 8086 emulator; every routine was then reverse-engineered
  and replaced by C verified against the original. The default build now runs with no 8086 interpreter.
- **Phase 4 makes it a modern game:** sharp graphics, gamepad, widescreen.

**Execution tracker:** This file (subtasks, model per subtask, user tasks). Design rationale is in
[docs/PORT_PLAN.md](docs/PORT_PLAN.md) (phases 1–4 approach). Phase 3 detail: [docs/PHASE3_PLAN.md](docs/PHASE3_PLAN.md).

Token efficiency is a first-class goal:
- small subtasks, one session each;
- the cheapest model that can do the job;
- the user does whatever is cheap for a human and expensive for a model (looking at pictures, playing).

Tracker: `python tools/plan_site.py` → `site/index.html` (this plan plus token usage per subtask and model).

## Status

- **Done:** Phases 0–3 (S0.1, S1.1, S2.1, S3.0–S3.22). Default build: 0 original instructions.
- **Next:** S4.1 and S3F.3. User tasks that can start now: U1, U2.
- Escalation rule: a subtask that fails twice on Sonnet → new Opus session with a 5-line note
  (symptom, file, what was tried). Never carry an old transcript over.

## Model guide

| Model (app model picker) | Effort | Use for | Relative cost |
|---|---|---|---|
| **Haiku 4.5** | low–medium | Running and adapting existing tools, regenerating outputs (`gen_state.py`, `fs1dis.py`, traces), symbol merges, packaging, README/PLAN bookkeeping, coverage runs | 1× |
| **Sonnet 5.5** | medium | Default: features on top of existing natives (renderer back ends, panel, input, settings), most C work, bug fixes with a known cause | ~3× |
| **Opus 5.5** | high | Design of new architecture (display lists, render back end), anything touching the 3D projection/clipping or timing, cross-module bugs, escalations | ~5× |

## How to run a subtask (user, every time)

1. Code tab → **New session** in `C:\Coding\Flight Simulator 1`. Never continue an old session for a new
   subtask: the old context is re-billed on every turn.
2. Pick the model from the subtask table in the model picker; set the effort.
3. Send exactly: `Do S4.1 from PLAN.md.` (with the subtask id). `CLAUDE.md` tells the agent what to read.
4. When the agent says it is done:
   - glance at the commit (`git log -1 --stat`);
   - do any U-check it asks for;
   - run `python tools/plan_site.py` if it didn't;
   - close the session.

## Subtasks

Model: H = Haiku 4.5, S = Sonnet 5.5, O = Opus 5.5. Size: rough session length (S/M/L).
Status goes in the row's last cell (`done YYYY-MM-DD`, `U4 pending`); longer notes go in the "Notes:" list
under each table, never between rows.

### Phases 0–3 (done)
| Id | Task | Model | Status |
|---|---|---|---|
| S0.1 | Repo, Apple II and PC disk analysis, PC boot loader decoded | O | done 2026-10-01 |
| S1.1 | Embedded PC (8086, CGA, PIT/PIC, keyboard, speaker, HLE BIOS), composite colour, text font, key map | O | done 2026-10-01 |
| S2.1 | Program map: tracing, trace campaign, `fs1dis.py`, symbols, `PROGRAM_MAP.md` | O | done 2026-10-01 |
| S3.0 | Phase 3, subphases 3.0–3.22: every routine in C, verified; emulator retired from the default build ([PHASE3_PLAN](docs/PHASE3_PLAN.md)) | O | done 2026-10-03 |

### Phase 3 follow-ups
| Id | Task | Model | Size | Status |
|---|---|---|---|---|
| S3F.1 | Docs refresh after 3.22: README status/build section, `PROGRAM_MAP.md` "what this means for phase 3" → current architecture (C scheduler, natives, state.h), `PORT_PLAN.md` phase list → this file | H | S | done 2026-10-03 |
| S3F.2 | Emulator build sound: audio with natives on is ~62 % off the original (IRQ0 backlog vs int8 native). Find and fix, `tools/audio_compare.py` must pass | S | M done 2026-10-03 |
| S3F.3 | `scenery_interp` charges 30 cycles less than the original on the horizon capture program (3.5 notes); fix accounting, `--verify` with `exact_cycles` | S | S | |
| S3F.4 | Coverage of never-run paths: rare scenery opcodes (05 06 08 0D 0E 10 11 15 2A 34), carb ice, engine faults/empty tanks, ≥512 kt, war kills/explosions/damage. Uses U3 recordings; verify in the emulator build | S | M | needs U3 |
| S3F.5 | `disk_backup` (5F54): native, or hide the backup option in the default build; document | H | S | |

### Phase 4 — Modernise (default build only; the emulator build stays as the reference)
Rendering today: the natives draw into the 640×200 CGA bitmap, which is decoded to composite colour and
scaled. Phase 4 adds a **display list**: the same natives also record what they draw (lines, fills,
text, sprites) in resolution-independent form, and a new SDL back end draws it sharply at window size.
The CGA path stays as "authentic" mode.
| Id | Task | Model | Size | Status |
|---|---|---|---|---|
| S4.1 | Release v0.1.0: `release/` zip with `fs1.exe`, `SDL3.dll`, README, CHANGELOG; `tools/package.py` | H | S | |
| S4.2 | Design: display-list format and recording points in the natives (`raster.h` lines, `fill_rows`/horizon, `textdraw.h`, `panel.h` sprites/needles, scenery dots); sub-pixel coordinates from the projection before rounding; `docs/RENDER4.md`; no code beyond a skeleton | O | M | |
| S4.3 | 3D view display list: record scenery lines/dots/polygons and horizon with float coordinates; `--dump-dl` to a text file per frame for checks | S | M | |
| S4.4 | SDL back end for the 3D view: lines (`SDL_RenderLines`, thickness option), filled sky/ground and polygons (`SDL_RenderGeometry`), composite-equivalent palette; toggle authentic/sharp (F11 cycles); **U4 check** | S | M | |
| S4.5 | Instrument panel at high resolution: needles as lines/polygons, indicators and sprites upscaled or vector-traced from the original sprite data; **U4 check** | S | L | |
| S4.6 | Text at high resolution: the 16×5 game font rendered as scalable glyphs (vector from the font bits), panel and menu text; editor text mode with a sharp font | S | M | |
| S4.7 | Widescreen / aspect: extend the horizontal field of view (projection scale and clip planes in `transform.c`), panel layout for 16:9; options 4:3 / 16:10 / 16:9; **U4 check** | O | M | |
| S4.8 | Gamepad and joystick (SDL3 gamepad API): analog elevator/aileron/rudder/throttle written into the control variables with the original key steps' scaling; dead zone; hot-plug | S | M | |
| S4.9 | Mouse yoke (optional, toggle key) and configurable key bindings (`fs1.ini`); in-game help overlay listing the keys | S | M | |
| S4.10 | Smooth frame rate: run the simulation at the original rates, render the 3D view every display frame with interpolated eye position/attitude from the display list; no sim behaviour change | O | L | |
| S4.11 | Settings and save state: `fs1.ini` (display mode, aspect, scale, audio, controls), F5/F9 quick save/load of the whole game state (memory array + registers) | S | M | |
| S4.12 | Release v1.0: packaging, README with screenshots taken by the user, CHANGELOG | H | S | |

Notes:
- S3F.2: the "62 % off" was already gone; the remaining difference was frame timing. The front end injects keys
  at a frame start and a frame ends at the first step past its budget, so the int8_timer native (one step) moved the
  key's latch by 12 cycles. `sound.c` `entry_run` now hands a native back when it spans (or starts past) the frame end.
- S4.2 must keep the authentic path byte-identical: recording is a side channel, and the
  `verify_campaign.py` gate (emulator build) still applies to every natives change.
- S4.7 and S4.10 change what the player sees; they are options (default: authentic behaviour).

## User tasks (cheap for you, expensive for a model)

### U1 — Manual and key card (now, 10 min)
The manual answers rule questions that would otherwise cost reverse-engineering sessions.
1. Find the *Microsoft Flight Simulator* 1.0x manual (PDF) and save it as `docs\manual.pdf`. PDFs are
   git-ignored.
2. If you have Poppler, run `pdftotext -layout docs\manual.pdf docs\manual.txt`. Agents then grep the
   text instead of reading the PDF.

### U2 — Playtest the current build (now, 20 min)
Build: `cmake --build build`, run `build\fs1.exe`. Check:
- start-up and menus;
- engine sound across throttle;
- take-off (release the brake with `.`);
- a landing and a crash;
- the editor (`s`, restart, `l`);
- area changes (editor North/East, e.g. LA 14884/5884);
- war mode;
- Ctrl+Alt+Del.

Report with the U5 format.

### U3 — Rare-path recordings (when S3F.4 asks, 15 min)
Fly the situations S3F.4 lists in the **emulator build** with `--verify all` and send the log lines that
contain `mismatch` (or "none"), for example:
- shoot down an enemy in war mode;
- an engine failure;
- carb ice.

### U4 — Visual checks (when an agent asks)
Open the screenshot or contact sheet it names next to the authentic mode, and reply in one line: `OK`, or
what is wrong and where (e.g. "runway lines 2 px too far left", "panel needle stays at zero"). Agents
do not look at images themselves.

### U5 — Bug reports (from phase 4)
```
Build: <commit hash>   Mode: authentic / sharp, aspect
Steps: <what you did, from launch>
Expected: <original behaviour>
Actual: <what happened; crash message if any>
Files: work\bugs\<n>.png
```
Several bugs in one message; one session then fixes them in a batch.

### U6 — Decisions (answer when convenient; defaults apply otherwise)
1. **Enhanced repo**: phase 4 in this repo (default), or a separate `FS1Enhanced` repo like F-117A/Aces?
2. **Sharp mode colours**: the four composite colours exactly (default), or a richer palette?
3. **Default mode at start**: authentic (default) or sharp?
4. **Widescreen**: extend the field of view (default) or stretch?
5. **Disk backup option**: hide it in the default build (default).

## Decisions
(Settled answers from U6 go here, dated.)

## TODO (parked)
- [ ] Apple II version (docs/ANALYSIS_APPLE2.md) — out of scope.
- [ ] Linux/macOS builds and CI.
