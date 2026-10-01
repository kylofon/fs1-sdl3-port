# Flight Simulator 1: SDL3 port

A port of *Microsoft Flight Simulator* 1.0x (IBM PC, 1982, by Bruce Artwick / subLOGIC) to modern
platforms using SDL3.

**Status:** Phase 0. The repo scaffold, disk analysis and loader decoding are done.
See [docs/PORT_PLAN.md](docs/PORT_PLAN.md).

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
