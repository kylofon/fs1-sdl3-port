# Subphase notes

Phase 3 subphases can run concurrently, one agent per subphase on its own branch. To avoid merge
conflicts in shared files:

- **Code.** Natives go only in that subphase's area file `src/natives/<area>.c` (listed in
  `src/natives/areas.h`). Do not edit `src/native.c`, `areas.h` or other areas' files; if a framework
  change is needed, describe it in the notes instead.
- **Notes.** Findings go in `docs/subphases/3.N.md`: what was replaced, formats learned, new symbols
  (in `docs/symbols.txt` syntax), verify results and anything for the user to test. Do not edit
  `docs/PROGRAM_MAP.md`, `docs/symbols.txt` or `docs/PHASE3_PLAN.md`; the coordinator merges notes into them.
- **Branch.** Use branch `phase3/3.N-short-name`, rebased on `main`, with one commit (or a few) and a PR
  whose description is the notes file.
- **Gate.** `python3 tools/verify_campaign.py` prints OK, with every native of the subphase enabled.
- **Shared helpers.** Helpers that other areas will need go in a header next to the area file
  (e.g. `src/natives/fixmath.h` from 3.1) and are listed in the notes.
