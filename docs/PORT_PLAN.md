# SDL3 port plan

## Which version to port

| | Apple II `.dsk` (subLOGIC FS1) | **IBM PC `.ima` (MS Flight Simulator 1.05)** |
|---|---|---|
| Codebase | Earlier, simpler subLOGIC product | Artwick's 1982 PC program, the root of the MSFS series |
| Content | One area, WWI ace mode | 4 scenery areas, ~20 airports, ATIS, ILS/VOR, weather, WWI war mode |
| CPU / tooling | 6502; weak decompiler support | 8086 real mode; Ghidra, IDA and objdump all handle it well |
| Load format | Cracker's RWTS and an undocumented custom loader | **Already fully decoded** (`tools/pc_loadstream.py`) |
| Hardware surface | Hi-res bitmap quirks, paddles, Disk II | CGA mode 4, PIT, PIC, port 60h, speaker, `int 13h` |
| Strings | Custom glyph encoding | Plain ASCII |

**Decision: port the PC version.** The Apple II image stays in `original/` as a historical reference
only. [ANALYSIS_APPLE2.md](ANALYSIS_APPLE2.md) keeps its notes.

## Constraints that shape the approach

- **No DOS and no files.** It's a booter with a bytecode loader. The loader is decoded, so we can either
  run the real boot sector or build the post-load memory image directly.
- **Bare-metal code.** It hooks IRQ0 and IRQ1, reprograms the PIT, and writes CGA memory directly. The
  emulated surface is small, but the timing (PIT rate, CPU speed) defines the original's feel.
- **Bitmap output.** The 3D wireframe is rasterized into interlaced CGA memory. A good port should
  ultimately draw *vectors* through SDL.
- **Possible key-track copy protection.** A sector dump can't reproduce it, so it must be found and
  handled.
- **Copyright.** The repo never contains disk images or extracted code. Everything is derived at run
  time from a user-supplied image.

## Approach: emulate first, then replace routines one by one

### Phase 1: Reference harness (the original runs under SDL3)

A minimal PC/XT core built for this one game:

- `cpu8086.c`: 8086/8088 real-mode core with approximate 4.77 MHz cycle costs, plus a trap table keyed
  on CS:IP. Write our own, about 1,500 lines. Alternatively vendor a permissively licensed core such as
  8086tiny (MIT); GPL cores are out.
- `pc.c`: 1 MB address space; i8259 PIC (IRQ0/IRQ1, EOI on port 20h); i8253 PIT (ch0 interrupt
  rate, ch2 square wave); 8255 port 61h; and the keyboard (SDL scancode to XT set-1 make/break codes,
  IRQ1, port 60h).
- **BIOS at high level, no IBM ROM.** Implement only what's used: `int 13h` AH=00/02 (plus a stub for
  AH=05) reading the `.ima`, and a minimal BIOS data area (`0040:003F` motor flags, …). Boot the
  real boot sector at `0000:7C00` so the loader runs exactly as on hardware.
- `cga.c`: mode 4, 320×200 interlaced, with palette/intensity from `3D9`. RGB output first, then
  composite artifact colour (option A) as an "authentic" mode. Show it at 4:3 aspect, not square pixels.
- Audio: PIT ch2 frequency combined with the port 61h gate, as a square wave into an
  `SDL_AudioStream`.
- Debug: dump memory, log executed CS:IP coverage, and record and replay input deterministically.

**Exit criteria:** it boots to the display menu, then the demo and regular flight work in all
4 scenery areas, plus the war mode. Copy protection is identified and handled.

**Status:**
- Done: boots through the real boot sector, display menu, regular flight. Composite artifact colour
  works, and so does the RGB/mono rendering.
- Findings:
  - The game uses CGA 640�200 in every mode: `3D8`=`1A` for the colour choices, `1E` for B/W.
    Colour comes purely from NTSC artifacts (sky `0111` = light blue, ground `1011` = green).
  - The decoder's hue reference is 340�.
  - So far nothing hits the key-track protection.
- Still to verify: demo mode, scenery switching (runtime `int 13h` reads), war mode, sound, and
  long-running timing.

### Phase 2: Map the program

- Load `extracted/boot_mem.bin` into Ghidra (x86 real mode). Seed it with the known entry points
  (`0050:5C9F`, `0050:5600`, the IRQ0 and IRQ1 handlers once they're hooked) and with coverage from the harness.
- Identify and name the subsystems:
  1. Main loop, timer tick, frame pacing
  2. Keyboard handler and the command dispatch for controls
  3. Fixed-point math: multiply/divide, sin/cos tables, angle formats
  4. Flight model: attitude, airspeed, lift and stall, engine, fuel, gear, crash detection
     (`MOUNTAIN CRASH`, `BUILDING CRASH`, `SPLASH!`)
  5. 3D pipeline: scenery database format, transform, clip, project, line draw into CGA
  6. Instrument panel and gauges, text rendering, the radio/VOR/ILS/ATIS logic
  7. War mode (`BEGIN WAR!!`, enemy fire, score, ammo, bombs, radar)
  8. Scenery paging from tracks 15–26
- Write format docs (scenery database, game state layout) in `docs/`. These become the C structs.

### Phase 3: Replace routines with native C, one at a time

- Bind C implementations to CS:IP traps, starting with leaf routines (line draw, multiply, sin/cos,
  plot) and working up through projection, scene rendering, instruments, flight model and the
  main loop.
- **Differential testing:** run the original and the C routine from the same CPU and memory state, and
  assert the same registers and memory writes. Replay recorded flights with deterministic input to catch
  drift.
- Game state moves from fixed memory offsets into C structs, with an accessor layer while both
  coexist.
- Scenery: parse the scenery tracks straight from the `.ima` into C data at startup, replacing the
  `int 13h` paging.
- Finish when the CPU core runs nothing, then delete `cpu8086.c`, `pc.c` and the BIOS layer.

### Phase 4: Make it a real port

- Render the 3D view as SDL lines at window resolution from the original fixed-point coordinates, with an
  optional "authentic CGA" mode. Draw the instrument panel at high resolution.
- Analog gamepad and joystick through the SDL3 gamepad API (yoke, throttle), configurable keys and mouse
  yoke.
- Run the simulation on a fixed timestep that matches the original PIT-driven rate, decoupled from
  render FPS.
- Widescreen, pause and help overlay, save and restore flights.

## Alternatives considered

| Approach | Why it isn't the primary path |
|---|---|
| Run it in DOSBox/PCjs | Works today, but it isn't a port: no modern rendering, controls or code ownership. |
| Static recompilation (x86 → C) | More practical than for the 6502, since the code is call-structured with no BIOS calls. It is still a candidate for Phase 3 *assistance*, but the output keeps the bitmap renderer and raw memory layout. |
| Clean-room rewrite from observed behaviour | Loses the exact flight model and feel. Phase 3 recovers them for free. |

## Source layout (target)

```
src/
  main.c          SDL3 app callbacks, window, frame loop
  disk.c/.h       raw sector images (.ima; .dsk kept for reference)
  cpu8086.c/.h    8086 core + CS:IP trap table          (Phases 1–3, removed at the end)
  pc.c/.h         memory map, PIC, PIT, 8255, keyboard   (Phases 1–3)
  bios.c          HLE int 13h + BIOS data area           (Phases 1–3)
  cga.c           CGA mode 4 → texture (RGB/composite)  (kept as the "authentic" mode)
  audio.c         speaker → SDL_AudioStream
  input.c         keyboard/gamepad → controls
  game/           native reimplementation: flight.c, render3d.c, scenery.c, panel.c, radio.c, war.c
tools/            Python analysis helpers
docs/             analysis notes, format specs, Ghidra notes
```
