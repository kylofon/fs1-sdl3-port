# Flight Simulator 1: SDL3 port

A port of *Microsoft Flight Simulator* 1.0x (IBM PC, 1982, by Bruce Artwick / subLOGIC) to modern
platforms using SDL3.

**Status:** Phase 1. The original program boots and flies inside an embedded minimal PC
(8088 + CGA + PIT/PIC + keyboard + speaker, high-level BIOS, no IBM ROM).
See [docs/PORT_PLAN.md](docs/PORT_PLAN.md).

## Playing

At the menu, pick **A** (colour composite) for the authentic colours, then **B** (regular flight).

| Key | Action |
|---|---|
| Numeric keypad / arrows / Home, End, PgUp, PgDn, Ins, Del | The original's keypad flight controls |
| Letters, digits, F1–F10 | As in the original manual |
| F10 | Toggle the monitor between composite (artifact colour) and RGB |
| F11 | Emulation speed x1 / x2 / x4 / x8 (sound only plays at x1) |
| F12 | Dump memory to `extracted/mem_dump.bin` |

Dev options: `--frames N` quits after N frames of 1/60 s, `--screenshot FILE.bmp` saves the last frame,
and `--type TEXT` types TEXT one key per second.

## You need the original disk

The game is not included. Put your PC booter disk image at:

    original/Microsoft Flight Simulator v1.05 (198x)(Microsoft Corporation).ima

or pass a path to it as the first argument to `fs1`. A 160K raw sector image (40×8×512) is expected.
An Apple II `.dsk` of subLOGIC's Flight Simulator is also recognised, but is only a reference.

## Building (Windows, MSYS2 MinGW64)

Install the MSYS2 packages `mingw-w64-x86_64-gcc`, `mingw-w64-x86_64-cmake`, `mingw-w64-x86_64-ninja` and
`mingw-w64-x86_64-sdl3`. Then run:

    cmake -S . -B build -G Ninja -DCMAKE_PREFIX_PATH=C:/msys64/mingw64
    cmake --build build
    build/fs1.exe

On other platforms, any SDL3 install that CMake can find through `find_package(SDL3)` works.

## Layout

- `src/`: the port (C11, SDL3)
- `tools/`: Python helpers
  - `pc_loadstream.py` decodes the PC boot loader stream and dumps the loaded memory image
  - `dsk_catalog.py` and `dis6502.py` are for the Apple II reference image
- `docs/`: [PC disk analysis](docs/ANALYSIS_PC.md), [port plan](docs/PORT_PLAN.md),
  [Apple II notes](docs/ANALYSIS_APPLE2.md)
- `original/`: your disk images (gitignored)
- `extracted/`: generated memory dumps (gitignored)
