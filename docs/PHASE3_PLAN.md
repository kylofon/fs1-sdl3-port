# Phase 3 plan: replace the original routines with native C

Each subphase is small, done by one agent, and ends with a commit. The next subphase starts only after
the user clears the previous one.

## Rules for every subphase

- **One subphase, one agent, one commit.** The commit message names the subphase, e.g. `3.4: draw_line in C`.
- **Binding replacements.** A replaced routine is bound to its `0050:xxxx` address in the CPU trap
  table. When the CPU reaches that address, the C function runs instead of the original, then returns
  as the original would.
- **Toggle per routine.** Every replacement can be switched off with `--native-off NAME`, which runs the
  original instead. This allows A/B comparison.
- **Differential check.** `--verify NAME` runs both the original and the C version from the same CPU
  and memory state, and reports the first difference in registers, flags it is documented to set, or
  memory. Each subphase must pass `--verify` over the trace campaign sessions (`tools/verify_campaign.py`).
- **Pixel-exact.** The game must still look and behave the same: screenshots match pixel for pixel
  against the original unless the subphase says otherwise.
- **Docs.** [PROGRAM_MAP.md](PROGRAM_MAP.md) and [symbols.txt](symbols.txt) are updated with anything
  learned along the way.
- **Testing.** The user tests the game after each subphase.

## Status

Subphases run concurrently, one agent each (see [subphases/README.md](subphases/README.md)). Every merge is
checked on top of main with all natives enabled (`verify_campaign.py` must print OK).
Symbols from the notes are merged with `python tools/merge_symbols.py`.

| Subphase | State | PR | Notes |
|---|---|---|---|
| 3.0 | merged | – | framework |
| 3.1 | merged | #6 | [3.1](subphases/3.1.md) |
| 3.2 | merged | #5 | [3.2](subphases/3.2.md) |
| 3.3 | merged | #3 | [3.3](subphases/3.3.md) |
| 3.4 | merged | #4 | [3.4](subphases/3.4.md) |
| 3.6 | merged | #2 | [3.6](subphases/3.6.md) |
| 3.7 | merged | #1 | [3.7](subphases/3.7.md), [SCENERY_FORMAT](SCENERY_FORMAT.md) |
| 3.8 | merged | #9 | [3.8](subphases/3.8.md) |
| 3.9 | merged | #8 | [3.9](subphases/3.9.md) |
| 3.13 | merged | #10 | [3.13](subphases/3.13.md) |
| 3.10 | merged | #7 | [3.10](subphases/3.10.md) |
| 3.5, 3.11, 3.12, 3.14, 3.17 | in progress | | |

## Subphases

| # | Subphase | Scope | Done when |
|---|---|---|---|
| **3.0** (done) | Replacement framework | Trap table in the CPU core (`native.c`/`native.h`). Native routines can read and write the CPU state and game memory and return like RET. Adds `--native-off`, `--verify`, `tools/verify_campaign.py`, and a test that a trivial pass-through native matches the original. | The framework is in place, a dummy native passes `--verify` across all campaign sessions, and the game is unchanged. |
| **3.1** | Maths helpers | `sincos`, `sin_quadrant`, `div_q15` | `--verify` is clean for all three across the campaign |
| **3.2** | Number formatting | `fmt_signed_dec`, the editor's `editor_digits_to_bin` and `editor_bin_to_digits` | `--verify` clean; the editor shows the same values |
| **3.3** | Back buffer primitives | `clear_view_buffer`, `blit_view_to_screen`, `plot_pixel`, `fill_rows` | `--verify` clean; screenshots identical |
| **3.4** | Line drawing | `draw_line` (including the alternate path at 5060, which gets documented here), `draw_line_list` | `--verify` clean; screenshots identical |
| **3.5** | Horizon | `fill_sloped_horizon`, `horizon_fill`, `draw_sky_ground` | `--verify` clean; screenshots identical in all attitudes, including inverted |
| **3.6** | 3D transform and clipping | `build_view_matrix`, `rotate_point`, `world_to_eye_delta`, the outcode and clipping routines, `project_dot`, `clip_project_line` | `--verify` clean |
| **3.7** | Scenery opcodes: research | Document every scenery-interpreter opcode (format, operands, effect) and the scenery data layout of all 5 areas. Write `tools/scenery_dump.py` to print an area's scenery program. Analysis only, no code replaced. | Every opcode reached in traces is documented in a new `docs/SCENERY_FORMAT.md` |
| **3.8** | Scenery interpreter | `scenery_interp` and all of its opcodes in C | `--verify` clean; screenshots identical in all 5 areas, radar view and war mode |
| **3.9** | Text and font | Locate the font, then reimplement `print_str` and its variants, `print_str_list`, `clear_screen` | `--verify` clean; the menus and panel text are identical |
| **3.10** | Indicators and needles | `draw_indicator`, `indicator_erase`, `blit_or`, `draw_needle` | `--verify` clean; the panel is identical |
| **3.11** | Gauge updaters | `upd_airspeed`, `upd_altimeter`, `gauge_upd_*`, `panel_update_mask`, `upd_obi`, the remaining panel routines | `--verify` clean |
| **3.12** | Radio navigation: research and C | Map and reimplement VOR, ILS, markers and the COM/ATIS messages (`com_tune` and the related routines) | `--verify` clean; NAV/OBI/OMI behave the same on the ILS approaches |
| **3.13** | Flight model: forces | `flight_forces`, `fix_loop_over`, `control_coupling`, `wing_cl_offsets` | `--verify` clean; recorded flights replay identically |
| **3.14** | Flight model: integration and environment | `flight_integrate`, `flight_params`, `apply_wind`, `compute_wind`, `engine_update`, `slew_update` | `--verify` clean; replays identical; crash detection unchanged |
| **3.15** | Game state in C structs | Move the aircraft, controls and panel state out of raw memory offsets into C structs, with an accessor layer. Native routines switch to using the structs. | All natives use the structs; `--verify` still clean |
| **3.16** | Editor, presets, menus | `editor_*`, `usermode_*`, `startup_menus`, and preset saving via a host file instead of disk track 26h | The editor works the same; presets are saved to a file next to the exe |
| **3.17** | War mode | `war_frame` and the enemy, gun and bomb routines | `--verify` clean; war-mode replay identical |
| **3.18** | Keyboard and controls | `key_dispatch` and all key handlers in C; scancodes come from SDL directly instead of through the emulated keyboard | All keys behave the same (key test harness) |
| **3.19** | Sound | Engine-note and tone generation in C straight to SDL audio, replacing the emulated timer and speaker path | Sounds match by ear and in a waveform comparison |
| **3.20** | Scenery loading | Parse the scenery tracks from the `.ima` at startup; replace `select_scenery_area` and the disk streaming | All 5 areas load with no emulated disk access |
| **3.21** | Main loop and timer in C | `main_loop` and `int8_timer` logic in C, with a fixed simulation timestep matching the original rates | The game runs with the 8086 core executing nothing during flight |
| **3.22** | Retire the emulator | Remove `cpu8086.c`, `pc.c` and the BIOS layer; keep the original-code path only as an optional verification build | The default build has no x86 emulation; everything works |

## How to add a native (framework from 3.0)

The registry is the `entries[]` table in `src/native.c`; helpers are in `src/native.h`.

1. Write `static void n_NAME(Pc *pc)`. It reads and writes `pc->cpu` registers and game memory
   (`ds_read16`/`ds_write16` for DS=0618, `mem_read16`/`mem_write16` for any segment; they go through
   `cpu_read*`/`cpu_write*`, so tracing and the verify write log see them). Leave every register as the
   original leaves it and end with `native_ret(pc)` (or `native_retf` for a far routine).
2. Add an entry: `{ .name = "NAME", .seg = GAME_CS, .off = 0xXXXX, .fn = n_NAME, .enabled = true, .cycles = N }`.
   Optional: `.far = true`, `.flag_mask = F_ZF | F_CF ...` (flags it guarantees; default none),
   `.ignore`/`.ignore_count` (linear ranges of write-only scratch memory left out of the comparison).
3. `.cycles` is what one call charges to the emulated clock (default `NATIVE_CALL_CYCLES` = 100). Set it to
   the original's cost so the timeline and screenshots stay identical; `--verify` prints the measured
   range (`original-cycles MIN..MAX`). For routines whose cost varies, timing-dependent details may differ.
4. Run `python tools/verify_campaign.py NAME` (or no argument for all). It must print `OK`.
   Compare screenshots with `--native-off NAME` against the default.

The dispatch costs nothing while no native is enabled: `cpu_step` checks `hook_map` (NULL then), and
otherwise one CS compare and one byte lookup per instruction.

How `--verify` works: at the entry address the original is single-stepped (no interrupts, cap 5,000,000
steps) until it returns (SP above its entry value, IP at the return address), with an undo log of all RAM
writes made through `cpu_write8`. The writes are undone, the CPU and device state (PIC, PIT, keyboard,
CGA, speaker) are restored, and the native runs with its own log. Registers, segment registers, IP, SP,
masked flags and every byte in either log are compared; the first difference is logged with the call
number (first 10 per native). Then the original's result, cycles and device state are put back, so a
`--verify` run follows the same timeline as a run with the native off. Memory written behind
`cpu_write8` (BIOS HLE services) is not tracked. Natives reached while the original runs execute as
original code. While a native or a verified call runs, IRQs are held until it returns.

## After phase 3 (phase 4 preview)

These are listed for context and are not part of phase 3:
- vector rendering at window resolution
- a high-resolution panel
- gamepad support
- widescreen
- save states

Phase 4 gets its own subphase list once phase 3 is done.
