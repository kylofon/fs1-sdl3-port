# Flight Simulator 1: SDL3 port

A port of subLOGIC's *Flight Simulator* for the Apple II (Bruce Artwick, 1980/1983) to modern platforms
using SDL3.

**Status:** Phase 0. The repo scaffold and disk analysis are done. See [docs/PORT_PLAN.md](docs/PORT_PLAN.md).

## You need the original disk

The game is not included. Place your Apple II disk image at:

    original/Flight_Simulator_1_1983_subLOGIC_cr_Midwest_Pirates_Guild.dsk

or pass a path to it as the first argument to `fs1`.

## Building (Windows, MSYS2 MinGW64)

Install the MSYS2 packages `mingw-w64-x86_64-gcc`, `mingw-w64-x86_64-cmake`, `mingw-w64-x86_64-ninja` and
`mingw-w64-x86_64-sdl3`. Then run:

    cmake -S . -B build -G Ninja -DCMAKE_PREFIX_PATH=C:/msys64/mingw64
    cmake --build build
    build/fs1.exe

On other platforms, any SDL3 install that CMake can find through `find_package(SDL3)` works.

## Layout

- `src/`: the port (C11, SDL3)
- `tools/`: Python helpers for inspecting the disk (`dsk_catalog.py`, `dis6502.py`)
- `docs/`: [disk analysis](docs/ANALYSIS.md) and the [port plan](docs/PORT_PLAN.md)
- `original/`: your disk image (gitignored)
