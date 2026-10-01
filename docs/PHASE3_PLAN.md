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

## Subphases

| # | Subphase | Scope | Done when |
|---|---|---|---|
| **3.0** | Replacement framework | Trap table in the CPU core (`native.c`/`native.h`). Native routines can read and write the CPU state and game memory and return like RET. Adds `--native-off`, `--verify`, `tools/verify_campaign.py`, and a test that a trivial pass-through native matches the original. | The framework is in place, a dummy native passes `--verify` across all campaign sessions, and the game is unchanged. |
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

## After phase 3 (phase 4 preview)

These are listed for context and are not part of phase 3:
- vector rendering at window resolution
- a high-resolution panel
- gamepad support
- widescreen
- save states

Phase 4 gets its own subphase list once phase 3 is done.
