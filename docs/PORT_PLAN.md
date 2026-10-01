# SDL3 port plan

## Constraints that shape the approach

- **No files and no symbols.** The game is a raw memory image streamed in by a custom loader, so the
  first job is getting a clean RAM snapshot after loading finishes.
- **Tight 6502 code.** 1980s subLOGIC code very likely uses self-modifying code, jump targets computed
  at runtime, and hand-unrolled plot loops. Pure static recompilation would be fragile.
- **The output is a bitmap.** The 3D wireframe is rasterized straight into hi-res memory. That memory
  packs 7 pixels per byte, interleaves its rows, and relies on NTSC artifact colour. A good port should
  end up drawing *vectors* through SDL rather than reproducing the bitmap.
- **Copyright.** The repo must never contain the disk image or extracted code. Everything is derived
  at run or build time from a `.dsk` the user supplies.

## Recommended approach: emulate first, then replace routines one by one

First get the original running inside our own SDL3 program. Then replace it with native C one routine
at a time. At every step there is a working game, plus the original code to diff against.

### Phase 1: Reference harness (the original runs under SDL3)

This is a minimal Apple II core built for this one game, not a general emulator.

- `cpu6502.c`: NMOS 6502 core with cycle counts, plus a hook table so any PC can be trapped.
- `machine.c`: 48K RAM, the `$C0xx` soft switches, the keyboard latch, paddle timers driven by cycle
  count, and a log of speaker toggles.
- **No Apple ROM needed.** Trap the few monitor entry points the code uses (`$FCA8`, `$FB2F`, `$FC58`,
  `$FE89`, `$FE93`, …) and implement them in C.
- **Disk:** nibblize the `.dsk` on the fly and emulate the Disk II data latch. That is about 150 lines
  and needs no knowledge of the loader. Trapping the loader's read routines and copying sectors
  directly is the fallback.
- `video_hires.c`: converts the hi-res page into a 280×192 RGBA streaming texture. It supports
  monochrome and artifact-colour modes.
- Input: the SDL keyboard drives `$C000`/`$C010`. An SDL gamepad or the mouse drives paddles 0/1 and
  the buttons.
- Audio: speaker toggles, timestamped by cycle, feed a square wave into an `SDL_AudioStream`.
- Debug: `F12` dumps RAM to `extracted/` (gitignored). A log records every PC reached.

**Exit criteria:** the game boots from the `.dsk`, the plane flies, and the WWI "British Ace" mode works.

### Phase 2: Map the program

- Snapshot RAM when the loader jumps to `$A7E2` (the main entry). That image is the program.
- Disassemble it with labels, using either cc65's `da65` (keep its info file in `docs/`) or Ghidra with
  its 6502 support. Record coverage from the harness (PCs executed, code bytes written) to separate code
  from data and to find self-modifying spots.
- Identify the subsystems:
  1. Main loop and frame pacing
  2. Input handling (keys for flaps, throttle, view, radar, …)
  3. Math: multiply and divide, sine/cosine tables, fixed-point formats
  4. Flight model: attitude, velocity, altitude, fuel, stall and crash
  5. 3D pipeline: world database, then transform, clip and project, then line drawing into hi-res
  6. Instrument panel drawing and the text font
  7. War game: enemy planes, bombing, ground targets, radar, scoring

### Phase 3: Replace routines with native C, one at a time

- Replace leaf routines first (line drawer, multiply, plot) with C functions bound in the PC trap table.
- **Differential testing:** run the 6502 original and the C version from the same CPU and RAM state, and
  assert identical registers and memory writes. Replay recorded flights from deterministic input logs.
- Work upwards: projection, then scene rendering, then the flight model, then the main loop. Once the
  main loop is in C, the 6502 core only runs leftover routines. When it runs nothing, delete it.
- Game state migrates from raw 6502 RAM addresses into C structs, with an accessor layer during the
  transition.

### Phase 4: Make it a real port

- Render the 3D view with SDL lines (`SDL_RenderLines`) at window resolution, from the original
  fixed-point world coordinates. An optional "authentic" mode keeps the 280×192 bitmap look.
- Redraw the instrument panel at higher resolution.
- Support analog gamepads and joysticks through the SDL3 gamepad API, and make keys configurable.
- Run the simulation on a fixed timestep that matches the original pacing, decoupled from render FPS.
- Add widescreen and aspect-ratio options, a pause and help overlay, and save states.

## Alternatives considered

| Approach | Why it isn't the primary path |
|---|---|
| Wrap an existing emulator | Fast, but the result is an emulator, not a port. Rendering and controls can't be modernized. |
| Static recompilation (6502 → C) | Self-modifying code and computed jumps make it brittle, and the output is unreadable C that still writes into a bitmap. |
| Clean-room rewrite from watching gameplay | Loses the exact flight model and feel. Phase 3 recovers the exact behaviour for free. |

## Source layout (target)

```
src/
  main.c          SDL3 app callbacks, window, frame loop
  disk.c/.h       .dsk loading, sector access, Disk II nibblizer
  cpu6502.c/.h    6502 core + PC trap table          (Phases 1–3, removed at the end)
  machine.c/.h    memory map, soft switches, I/O    (Phases 1–3)
  video_hires.c   hi-res bitmap → texture           (kept as the "authentic" mode)
  audio.c         speaker → SDL_AudioStream
  input.c         keyboard/gamepad → game controls
  game/           native reimplementation: flight.c, render3d.c, world.c, panel.c, war.c
tools/            Python analysis helpers
docs/             analysis notes, disassembly info files
```
