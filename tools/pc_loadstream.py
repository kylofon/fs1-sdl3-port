"""Decode the boot-time load stream of the IBM PC MS Flight Simulator 1.0x booter disk.

The boot sector (relocated to 0050:0000) reads whole tracks (8 x 512 B) starting at
track 1 into B800:0000 and interprets the bytes as a command stream:

  01 LL LL data[LL-3]                  copy data to 0000:DI (DI carries over, starts 0x0700)
  02 LL LL SS SS data[LL-5]            copy data to SSSS:0000
  03 w w(SS) w(SP) w(CX) w(AX)         set SS:SP, DS=AX, call 0050:5600 (overlay init)
  04 w(II VV)                          table[0x3B4 + II] = VV
  other                                 jmp 0050:5C9F (start game)

usage: pc_loadstream.py IMAGE [--dump OUTDIR]
"""
import os
import sys

SECTOR, SPT = 512, 8
TRACK = SECTOR * SPT


class Stream:
    def __init__(self, img):
        self.img, self.track, self.pos = img, 1, 0

    def byte(self):
        if self.pos == TRACK:
            self.track, self.pos = self.track + 1, 0
        b = self.img[self.track * TRACK + self.pos]
        self.pos += 1
        return b

    def word(self):
        lo = self.byte()
        return lo | self.byte() << 8

    def where(self):
        return f"T{self.track:02d}+{self.pos:04X}"


def main(path, dump=None):
    img = open(path, "rb").read()
    s = Stream(img)
    mem = bytearray(0x100000)
    di = 0x0700
    while True:
        at = s.where()
        op = s.byte()
        if op == 1:
            n = s.word() - 3
            data = bytes(s.byte() for _ in range(n))
            mem[di:di + n] = data
            print(f"{at} 01 copy  {n:5d} bytes -> 0000:{di:04X}")
            di += n
        elif op == 2:
            n = s.word() - 5
            seg = s.word()
            data = bytes(s.byte() for _ in range(n))
            mem[seg * 16:seg * 16 + n] = data
            print(f"{at} 02 copy  {n:5d} bytes -> {seg:04X}:0000 (linear {seg * 16:05X})")
            di = n
        elif op == 3:
            w0, ss, sp, cx, ax = (s.word() for _ in range(5))
            print(f"{at} 03 call  0050:5600  SS:SP={ss:04X}:{sp:04X} DS={ax:04X} CX={cx:04X} ({w0:04X})")
        elif op == 4:
            s.word()
            w = s.word()
            print(f"{at} 04 table [{0x3B4 + (w & 0xFF):04X}] = {w >> 8:02X}  (scenery area {w & 0xFF} starts at track {w >> 8})")
        else:
            print(f"{at} {op:02X} end -> jmp 0050:5C9F (linear {0x500 + 0x5C9F:05X}); stream stopped at track {s.track}")
            break
        if s.track >= 40:
            print("ran off the end of the disk")
            break
    if dump:
        os.makedirs(dump, exist_ok=True)
        open(os.path.join(dump, "boot_mem.bin"), "wb").write(mem[:0xC0000])
        print(f"wrote {dump}/boot_mem.bin (linear 00000-BFFFF after load)")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[a.index("--dump") + 1] if "--dump" in a else None)
