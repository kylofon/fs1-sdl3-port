# Changelog

## 0.1.0 (2026-10-03)

First release: a faithful C/SDL3 port of *Microsoft Flight Simulator* 1.05 for the IBM PC (1982).

- Every routine of the original program is reimplemented in C and was verified against the original
  running on an 8086 emulator. The release build has no 8086 interpreter.
- The whole game: the display menu, regular flight, the instrument panel and radios, the radar view and the
  view directions, the scenery, the Esc editor (positions, slew, …), the Europe 1917 war game, the engine
  note and tones.
- The 160K PC booter disk image is read at run time; copy protection and disk handling are not needed.
  Any 160K `.ima` next to `fs1.exe` is found.
- CGA composite artifact colours (menu option A) or RGB (F11 toggles); resizable window; F12 runs faster
  (x2/x4/x8, no sound).
- Arrows, Home/End/PgUp/PgDn, Ins and Del stand in for the numeric keypad; Left Shift + keypad key picks a
  view direction.
- The disk backup menu option returns to the menu (no floppy to write to).
