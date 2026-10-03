# Flight Simulator 1 port — agent rules (keep this file short: it is loaded every session)

Faithful C/SDL3 port of Microsoft Flight Simulator 1.05 (IBM PC, 1982); phases 0–3 done (every routine
in C, verified against the original). State and subtasks: `PLAN.md`.

Token budget rules:
- Work on ONE subtask per session (PLAN.md id, e.g. `S4.3`). Read only PLAN.md "Status" + that
  subtask, not the whole file. When done: update its status cell (`done YYYY-MM-DD`, `U4 pending`),
  run `python tools/plan_site.py`, commit. Longer notes go in the "Notes:" list under the table.
- Never read large files whole. `Grep` first, then `Read` with offset/limit. `extracted/fs1.asm`,
  `docs/symbols.txt`, `src/game/state.h` and the big natives (`src/natives/*.c`) are searched, never dumped.
- Do not re-derive facts already in `docs/PROGRAM_MAP.md`, `docs/SCENERY_FORMAT.md`,
  `docs/subphases/3.*.md` or `docs/symbols.txt`. Game state: use `src/game/state.h` accessors
  (`python tools/gen_state.py` after editing symbols.txt).
- Tools print short summaries (counts, first lines, errors); outputs go to `work/` or `extracted/`.
- Do not view images or screenshots unless asked. Visual checks are the user's job (PLAN.md U4):
  write the PNG, then ask the user what they see.
- Two builds: default `build/` (no 8086 interpreter) and `build-emu/` (`-DFS1_EMULATOR=ON`, the original
  code + `--verify`). Any change to a native must keep `python tools/verify_campaign.py` OK (emulator build).
- Windows: build with `C:\msys64\mingw64\bin` first on PATH (`scripts/cloud_setup.sh` does the setup).
- Wide searches → `Explore` agent on Haiku.
- Game data is never committed (`original/`, `extracted/`).
- Commits end with the attribution line from the session's instructions.
- No test HTML pages; implement, then tell the user what to test.
