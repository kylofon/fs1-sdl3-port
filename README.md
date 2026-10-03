# Flight Simulator 1: SDL3 port

A port of *Microsoft Flight Simulator* 1.0x (IBM PC, 1982, by Bruce Artwick / subLOGIC) to modern
platforms using SDL3.

**Status:** Phase 3 done (3.22); first release v0.1.0. Every routine of the original program is reimplemented in C, and the
default build runs the game from boot to quit without an 8086 interpreter: a C scheduler calls the C
routines and raises the timer and keyboard interrupts between them, the boot loader is decoded in C, and
the engine note and tones are made from the game's sound model. The 8088 memory image and register file
remain as the routines' data model, and the screen is drawn from the CGA memory. The original code still
runs, for verification, in the optional emulator build (an embedded minimal PC: 8088 + CGA + PIT/PIC +
keyboard + speaker, high-level BIOS, no IBM ROM).
See [PLAN.md](PLAN.md) for the roadmap and per-subtask model/effort. Phase 3 detail is in [docs/PHASE3_PLAN.md](docs/PHASE3_PLAN.md).

**Plan and tracker:** [PLAN.md](PLAN.md) (subtasks, model per subtask, user tasks); `python tools/plan_site.py` renders it with token usage to `site/index.html`.

## How to play (Windows)

You need an image of the original IBM PC booter disk of *Microsoft Flight Simulator* 1.05 (a 160K `.ima`
file). It is not included.

1. Open the [latest release](https://github.com/kylofon/fs1-sdl3-port/releases/latest) and download
   `fs1port-…-win64.zip`.
2. Unzip all of its files into a folder, and put your disk image in the same folder:

   ```text
   Flight Simulator 1   ├── fs1.exe
   ├── SDL3.dll
   ├── (the other files from the zip)
   └── Microsoft Flight Simulator v1.05 (198x)(Microsoft Corporation).ima   <- your disk image
   ```

3. Double-click `fs1.exe`. Any 160K `.ima` in that folder is found; you can also drag a disk image onto
   `fs1.exe`. If Windows says "Windows protected your PC", click **More info**, then **Run anyway**.

Changes per release: [CHANGELOG.md](CHANGELOG.md). Licence: MIT ([LICENSE](LICENSE)); the bundled DLLs are
listed in `licenses/THIRD-PARTY.txt` in the zip.

## Playing

At the menu, pick **A** (colour composite) for the authentic colours, then **B** (regular flight).

Arrows, Home/End/PgUp/PgDn, Ins and Del stand in for the numeric keypad. Bindings were
verified by scripted key presses against the running game, except where marked *untested*.

| Key | Action |
|---|---|
| KP8 / ↑, KP2 / ↓ | Elevator: nose down / nose up |
| KP4 / ←, KP6 / → | Ailerons left / right (rudder follows while auto-coordination is on) |
| KP0 / Ins, KP+ | Rudder left / right (ailerons follow while auto-coordination is on) |
| KP5 | Centre ailerons and rudder |
| KP7 / Home, KP1 / End | Elevator trim down / up |
| F2, F4, F6, F8, F10 | Throttle: full, increase, small increase, decrease, cut |
| F1, F3, F5, F7, F9 | Flaps: up, 10°, 20°, 30°, 40° |
| G | Landing gear (no effect on the ground) |
| . (Del) | Brakes (on the ground) |
| H / L | Carburettor heat / lights toggle |
| 1 2 3 4 5 | Magnetos: off, left, right, both, start |
| 0 | Magnetos to position 5 (engine off, label shows "LN") |
| D | Set the heading gyro to the compass |
| A | Clear the altimeter correction |
| C, N, V, T | Select COM frequency, NAV frequency, OBI course, transponder digit (press again for the next field) |
| `-` / `=` | Decrease / increase the selected item |
| Num Lock | Radar (top-down) view on/off toggle (port: sends Scroll Lock when the radar is on); `-`/`=` zoom the radar |
| Scroll Lock | Radar view off |
| Scroll Lock, then a keypad key | Choose the view direction (with the radar off) |
| Left Shift + keypad key | Same as Scroll Lock, then that key (port addition) |
| P | Pause |
| KP\* | Restart the flight from the initial position |
| Esc | "MFS Edit Mode" editor (positions, slew, Europe 1917 war mode, …) |
| Ctrl+Alt+Del | Reboot to the display menu |
| Tab | Shifts the picture horizontally on a real monitor (no visible effect here) |
| KP9 / PgUp, KP3 / PgDn | Slew mode: bank / turn (no effect in normal flight) |
| Alt | Slew mode: snap the aircraft to a fixed attitude |
| Space | War mode: fire guns |
| X | War mode: drop a bomb |
| W | War mode: cycle the status line between SCORE / AMMO / BOMBS |

In the Esc editor, Enter moves the `-->` cursor to the next field. Type a value and press Enter to set it,
then press Esc to return to flight. Slew is the 4th field and Europe 1917 (war mode) is the 7th.

Port keys (F1–F10 belong to the game):

| Key | Action |
|---|---|
| F11 | Toggle the monitor between composite (artifact colour) and RGB |
| F12 | Emulation speed x1 / x2 / x4 / x8 (sound only plays at x1) |
| Ctrl+F12 | Dump memory to `extracted/mem_dump.bin` |

Dev options: `--frames N` quits after N frames of 1/60 s, `--screenshot FILE.bmp` saves the last frame,
`--shot-at N` also saves `FILE_N.bmp` at frame N, `--keys "300:F2,400:Keypad 8*30"` scripts key presses,
`--type TEXT` types TEXT one key per second, `--rgb` starts in RGB mode, `--dump-on-exit` dumps memory,
and `--trace FILE` accumulates an execution/data trace map (see [docs/PROGRAM_MAP.md](docs/PROGRAM_MAP.md)).
Native replacements of original routines (phase 3): `--list-natives` prints them and `--stats` prints how
many original instructions ran (always 0 in the default build). The options that run original code need the
emulator build (below): `--native-off NAME|all` runs the original code instead, `--verify NAME|all` runs
both the original and the native on every call and reports differences (`python tools/verify_campaign.py`
does this over all campaign sessions; see [docs/PHASE3_PLAN.md](docs/PHASE3_PLAN.md)), `--trace FILE`,
`--csched` runs the emulator build with the default build's C scheduler, and `--check-boot` compares the
C boot with the original loader.

## You need the original disk

The game is not included. Put your PC booter disk image at:

    original/Microsoft Flight Simulator v1.05 (198x)(Microsoft Corporation).ima

or next to `fs1.exe` (any 160K `.ima` there is found), or pass a path to it as the first argument. The program finds it whether you start it
from the project root, from `build/`, or by double-clicking. A 160K raw sector image (40×8×512) is expected.
An Apple II `.dsk` of subLOGIC's Flight Simulator is also recognised, but is only a reference.

## Building (Windows, MSYS2 MinGW64)

Install the MSYS2 packages `mingw-w64-x86_64-gcc`, `mingw-w64-x86_64-cmake`, `mingw-w64-x86_64-ninja` and
`mingw-w64-x86_64-sdl3`. Then run:

    cmake -S . -B build -G Ninja -DCMAKE_PREFIX_PATH=C:/msys64/mingw64
    cmake --build build
    build/fs1.exe

Release zip: `python tools/package.py` builds `build/` and writes `release/fs1port-v<version>-win64.zip`,
`RELEASE_NOTES.md` and `SHA256SUMS.txt` (the version is `project(... VERSION)` in `CMakeLists.txt`).

On other platforms, any SDL3 install that CMake can find through `find_package(SDL3)` works.

### Build options

| CMake option | Default | What it builds |
|---|---|---|
| `FS1_EMULATOR` | `OFF` | `ON` adds the 8086 interpreter (`src/cpu8086.c`), the emulated PIC/PIT/ports and BIOS, the original boot loader, and the options that run original code (`--verify`, `--native-off`, `--trace`, `--csched`, `--check-boot`). This build starts on the emulated PC with all natives on, as before 3.22. |

The verification tools (`tools/verify_campaign.py`, `trace_campaign.py`, `insn_stats.py`, `scenery_sessions.py`,
the cycle-table generators) need the emulator build. They use `build-emu/` (or the executable named by the
`FS1_EXE` environment variable):

    cmake -S . -B build-emu -G Ninja -DCMAKE_PREFIX_PATH=C:/msys64/mingw64 -DFS1_EMULATOR=ON
    cmake --build build-emu
    python tools/verify_campaign.py

## Cloud sessions

See [docs/CLOUD.md](docs/CLOUD.md) for building and verifying on a headless Linux machine.

## Layout

- `src/`: the port (C11, SDL3)
  - `sched.c`: the C scheduler and the boot in C; `natives/`: the original routines in C, one file per area
  - `cpu_core.c`: the 8086 register file and memory accessors (the natives' data model)
  - `cpu8086.c`, and the emulated hardware in `pc.c`: the emulator build only
- `tools/`: Python helpers
  - `pc_loadstream.py` decodes the PC boot loader stream and dumps the loaded memory image
  - `dsk_catalog.py` and `dis6502.py` are for the Apple II reference image
- `docs/`: [PC disk analysis](docs/ANALYSIS_PC.md), [original port plan](docs/PORT_PLAN.md) (phase 1–4 design),
  [Apple II notes](docs/ANALYSIS_APPLE2.md)
- `original/`: your disk images (gitignored)
- `extracted/`: generated memory dumps (gitignored)
