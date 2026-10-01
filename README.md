# Flight Simulator 1: SDL3 port

A port of *Microsoft Flight Simulator* 1.0x (IBM PC, 1982, by Bruce Artwick / subLOGIC) to modern
platforms using SDL3.

**Status:** Phase 1. The original program boots and flies inside an embedded minimal PC
(8088 + CGA + PIT/PIC + keyboard + speaker, high-level BIOS, no IBM ROM).
See [docs/PORT_PLAN.md](docs/PORT_PLAN.md).

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
| C, N, V, T | Select COM frequency, NAV frequency, OBI course, transponder digit (press again for the next field) |
| `-` / `=` | Decrease / increase the selected item |
| Num Lock / Scroll Lock | Radar (top-down) view on / off; `-`/`=` zoom the radar |
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
| A, D, 0 | No visible effect found yet |

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
Native replacements of original routines (phase 3): `--list-natives` prints them, `--native-off NAME|all`
runs the original code instead, `--native-on NAME|all` enables a default-off one, and `--verify NAME|all`
runs both the original and the native on every call and reports differences
(`python tools/verify_campaign.py` does this over all campaign sessions; see [docs/PHASE3_PLAN.md](docs/PHASE3_PLAN.md)).

## You need the original disk

The game is not included. Put your PC booter disk image at:

    original/Microsoft Flight Simulator v1.05 (198x)(Microsoft Corporation).ima

or next to `fs1.exe`, or pass a path to it as the first argument. The program finds it whether you start it
from the project root, from `build/`, or by double-clicking. A 160K raw sector image (40×8×512) is expected.
An Apple II `.dsk` of subLOGIC's Flight Simulator is also recognised, but is only a reference.

## Building (Windows, MSYS2 MinGW64)

Install the MSYS2 packages `mingw-w64-x86_64-gcc`, `mingw-w64-x86_64-cmake`, `mingw-w64-x86_64-ninja` and
`mingw-w64-x86_64-sdl3`. Then run:

    cmake -S . -B build -G Ninja -DCMAKE_PREFIX_PATH=C:/msys64/mingw64
    cmake --build build
    build/fs1.exe

On other platforms, any SDL3 install that CMake can find through `find_package(SDL3)` works.

## Cloud sessions

See [docs/CLOUD.md](docs/CLOUD.md) for building and verifying on a headless Linux machine.

## Layout

- `src/`: the port (C11, SDL3)
- `tools/`: Python helpers
  - `pc_loadstream.py` decodes the PC boot loader stream and dumps the loaded memory image
  - `dsk_catalog.py` and `dis6502.py` are for the Apple II reference image
- `docs/`: [PC disk analysis](docs/ANALYSIS_PC.md), [port plan](docs/PORT_PLAN.md),
  [Apple II notes](docs/ANALYSIS_APPLE2.md)
- `original/`: your disk images (gitignored)
- `extracted/`: generated memory dumps (gitignored)
