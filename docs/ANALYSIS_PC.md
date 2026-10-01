# IBM PC disk analysis: Microsoft Flight Simulator v1.05

Image: `original/Microsoft Flight Simulator v1.05 (198x)(Microsoft Corporation).ima`

| Property | Value |
|---|---|
| Size | 163,840 bytes = 40 tracks × 8 sectors × 512 B (PC-DOS 1.0 160K single-sided geometry) |
| Platform | IBM PC/XT, 8088 real mode, CGA, 64K+ RAM |
| Filesystem | **None.** It's a self-booting disk with no FAT and no directory. The boot sector lacks the `55 AA` signature, which the original PC BIOS didn't check. |
| Title strings | `MICROSOFT FLIGHT SIMULATOR`, `COPYRIGHT 1982 BY BRUCE A. ARTWICK`, `PRODUCED BY MICROSOFT CORPORATION` |
| Empty sectors | T0 S5–8 and T9 S8/T10 S1. Every other sector is used. |

## Boot loader (T0/S1)

The boot sector relocates itself from `0000:7C00` to `0050:0000` and sets SS:SP = `0000:C0B0`. It then
runs a **bytecode-driven loader**:

- It reads whole tracks (8 sectors, `int 13h` AH=02) into a 4 KB buffer at `B800:0000`, which is CGA
  video RAM. The load is visible on screen as noise.
- Reading starts at track 1. An optional verify pass re-reads the track and compares word checksums.
- It interprets the buffer as a command stream. `tools/pc_loadstream.py` decodes it.

| Op | Operands | Effect |
|---|---|---|
| `01` | `len:w`, data | copy `len-3` bytes to `0000:DI` (DI starts at `0700` and carries over) |
| `02` | `len:w`, `seg:w`, data | copy `len-5` bytes to `seg:0000` |
| `03` | `w`, `ss:w`, `sp:w`, `cx:w`, `ds:w` | switch stack and DS, then `call 0050:5600` (init) |
| `04` | `w`, `idx:b`, `val:b` | `byte [0050:03B4+idx] = val` |
| other | – | `jmp 0050:5C9F`, which starts the game |

Decoded stream for v1.05:

```
T01+0000 01 copy  24928 bytes -> 0000:0700          main code  (CS=0050, offsets 0200-6360)
T07+0163 02 copy  16560 bytes -> 0686:0000          data/code segment (linear 06860-0A910)
T11+0218 02 copy   3904 bytes -> B900:0000          CGA RAM: title/panel graphics, even lines
T12+015D 02 copy   3904 bytes -> BB00:0000          CGA RAM: title/panel graphics, odd lines
T13+00A2 03 call  0050:5600  SS:SP=0000:03FE DS=0686
T13+00AD 04 table [03B4..03B8] = 0F 12 15 18 1A    scenery area -> start track
T13+00C6 09 end -> jmp 0050:5C9F
```

The boot sector stays resident at `0050:0000–01FF`. The game reuses its track-read routines (via
`int 13h`) to page in scenery at runtime.

## Disk map

| Tracks | Content |
|---|---|
| 0 | Boot sector + loader |
| 1–13 | Load stream: program code, data, title graphics |
| 15–17 | Scenery area 0: **Chicago** (Meigs, O'Hare, Midway, Champaign, Kankakee) |
| 18–20 | Scenery area 1: **Los Angeles** (LAX, Santa Monica, Van Nuys, John Wayne, Catalina, San Diego) |
| 21–23 | Scenery area 2: **Seattle** (Boeing Field, Sea-Tac, Paine, Olympia, Port Angeles) |
| 24–25 | Scenery area 3: **New York/Boston** (JFK, Logan, Block Island, Martha's Vineyard, Bridgeport) |
| 26 | Scenery area 4: probably the WWI "war" area |
| 27–39 | Mostly `!` (`$21`) filler or additional data. **TODO:** check. |

The scenery blocks contain plain ASCII airport names, ATIS text and ILS approach information.

## Hardware surface

The game code makes **no BIOS calls**. The only `int` instructions are in the resident boot sector
(`int 13h`). Everything else is direct hardware access:

| Device | Use |
|---|---|
| CGA `B800:0000` | Direct writes. Mode 4: 320×200, 4 colours, interlaced even/odd banks at `+0000`/`+2000` |
| CGA ports `3D8`/`3D9` | Mode and palette select. Startup asks: A = composite (artifact colour), B = B/W, C = RGB |
| PIT `40h`/`43h` (ch0) | Reprogrammed timer tick, probably for simulation timing |
| PIT `42h` (ch2) + port `61h` | Speaker (engine sound) |
| Port `60h` + PIC `20h` | Its own IRQ1 keyboard handler with a raw scancode table (`1234567890-=qwertyuiop[]…`) |
| `int 13h` | Track reads for loading and scenery; `AH=05` format for "DISK BACKUP MODE" |

## Copy protection

The strings mention a **key track** (`KEY TRACK I/O ERROR`) and the backup mode formats tracks
(`int 13h AH=05`). A plain `.ima` sector dump can't preserve non-standard track formatting. If the game
checks the key track at boot or at runtime, the check has to be found and satisfied, either by
emulating it at high level or by patching it. **This is the first thing to confirm in Phase 1.**

## Entry point `0050:5C9F`

```
xor ax,ax / mov ds,ax / mov ds,[0120]     ; DS = data segment saved by the loader
call 5600   call 5DA6   call 6254   call 6265   call 5CE9
call 5600   call 5DC3   call 3A52   call 3B36   call 5CCD
cmp byte [0418],1 / jmp 01F0              ; into the main loop
```

The code is ordinary near-call-structured 8086 assembly, so it suits Ghidra and IDA well.

## Tools

- `python tools/pc_loadstream.py IMAGE [--dump extracted]` decodes the load stream. With `--dump` it
  writes the post-load 768K memory image to `extracted/boot_mem.bin` (gitignored).
- To disassemble, use `objdump -D -b binary -m i8086 --adjust-vma=OFFSET FILE` from MSYS2 binutils,
  or load `boot_mem.bin` in Ghidra as `x86:LE:16:Real Mode` at base `0000:0000`.
