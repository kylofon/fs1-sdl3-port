# Apple II disk analysis (secondary reference)

> Superseded as the port base by the IBM PC version; see [ANALYSIS_PC.md](ANALYSIS_PC.md) and [PORT_PLAN.md](PORT_PLAN.md).
> Note: this is subLOGIC's earlier Apple II *Flight Simulator*, a separate and simpler codebase than Microsoft Flight Simulator 1.0 for the PC.

Image: `original/Flight_Simulator_1_1983_subLOGIC_cr_Midwest_Pirates_Guild.dsk`

| Property | Value |
|---|---|
| Size | 143,360 bytes = 35 tracks × 16 sectors × 256 B |
| Platform | Apple II (48K), 6502 |
| Order | DOS 3.3 logical sector order (`.dsk` / `.do`) |
| Filesystem | **None.** T17/S0 (VTOC) is filled with `$FD`; no catalog. Whole-disk custom loader. |
| Usage | Practically every sector of all 35 tracks is non-empty. |
| Crack | Midwest Pirates Guild (MPG): copy protection removed, standard 16-sector format. The crack intro text is near disk offset `$9790`. |

## Boot chain

1. **Boot0, T0/S0 → `$0800`.** This is a stock DOS 3.3 boot sector. `$08FE`=`$1D` and `$08FF`=`$02`, so it
   reads T0 S1..S2 into `$1D00–$1EFF`. A small patch at `$0860` (a `$0415` screen check and `WAIT` calls)
   then does `JMP $1D00`.
2. **Stage-2 loader at `$1D00`.** This is the cracker's fast loader, an RWTS-style 6-and-2 nibble reader.
   - `$1EC7` finds the `D5 AA 96` address field and the `D5 AA AD` data field.
   - `$1F11` denibblizes through the `$02D6` translate table.
   - `$1E10` reads 10 sectors of track 0 into `$2000–$29FF`, in descending pages from `$29`.
     The sector order table is at `$1F5C`.
   - Zero page and page 3 are saved to `$2A00`/`$2B00` around the read, then restored.
3. **Game loader at `$2000`.** A jump table at `$1EAD` (`JMP $2020`, `$2028`, `$20A6`, `$2119`, `$2031`,
   `$2000`) hands control to the code just loaded from track 0. That code streams the rest of the disk
   (the loop runs until track `$25`) into memory and finishes with `JMP $A7E2`.

   **TODO:** trace this in the harness and record the final memory map.

## Content observations

- There is almost no ASCII text on the disk. FS1 draws all text with its own hi-res font, so strings are
  stored as glyph indices. Only the MPG crack screen is plain high-bit ASCII.
- Long runs of `.U*U*U*` (`$AA $D5` patterns) around disk offsets `$8900–$9600` look like hi-res bitmap
  data. This is probably the instrument panel or the title graphics.
- The boot code calls Apple monitor ROM entry points: `$FCA8 WAIT`, `$FB2F INIT`, `$FC58 HOME`, and
  `$FE89`/`$FE93` to set the I/O hooks. The game proper is expected to drive the hardware directly.

## Hardware the game is expected to touch

| Address | Purpose |
|---|---|
| `$2000–$3FFF`, `$4000–$5FFF` | Hi-res pages 1/2 (double-buffered 3D view) |
| `$C000` / `$C010` | Keyboard data / strobe |
| `$C030` | Speaker toggle (engine sound) |
| `$C050–$C057` | Soft switches: graphics/text, mixed, page, hi-res |
| `$C061–$C063` | Push buttons (joystick fire) |
| `$C064–$C067` / `$C070` | Paddle timers (joystick axes) |
| `$C080–$C08F + slot×16` | Disk II (loader only) |

## Tools

- `python tools/dsk_catalog.py IMAGE` prints the DOS 3.3 catalog and per-track usage.
- `python tools/dis6502.py IMAGE OFFSET LEN LOADADDR` prints a quick linear 6502 disassembly.
  The disk offset of a track/sector is `(T*16+S)*256`.
