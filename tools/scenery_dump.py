"""Disassemble the scenery bytecode of IBM PC MS Flight Simulator 1.05.

The scenery is a program for the interpreter `scenery_interp` (0050:3CC0). The opcode
reference is docs/SCENERY_FORMAT.md. This tool prints a program as a listing, with one
opcode per line, labels for branch targets and coordinates as signed numbers.

Sources:
  * Areas 0-4 are read straight from the disk image. Area i starts at track area_tracks[i]
    (0F 12 15 18 1A) and is stored like the boot stream: one 01 record {01, word length,
    length-3 bytes}, read across track boundaries (4 KB per track). The game copies the
    record body to DS:3A84 (scenery_base), so addresses in the listing are DS offsets.
  * The eight horizon programs (table at DS:1D4F) are part of the data segment, so they
    are read from a runtime memory dump (build/fs1 --frames 600 --keys "120:A,180:B"
    --dump-on-exit writes extracted/mem_dump.bin; DS = 0618, linear 0x6180).

Decoding follows the control flow from the entry point (branches, calls, skip-if tests).
Bytes it does not reach are then decoded linearly as dead code, so that every byte of an
area is accounted for; the summary line reports the coverage.

usage: scenery_dump.py [--area N ...] [--horizon] [--stats] [--check] [--bytes] [--text]
                       [--image IMA] [--mem MEM_DUMP] [--symbols docs/symbols.txt]

  --area N    dump area N (repeatable; default: all five areas)
  --horizon   also dump the horizon programs (needs the memory dump)
  --stats     print only the summary and opcode counts, no listing
  --check     print the world-space extent of the geometry of each origin block
  --bytes     show the raw bytes of each instruction
  --text      show embedded ATIS texts and demo key scripts

The output is derived from the user's own disk image: don't commit it.
"""
import argparse
import os
import re
import struct
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_IMAGE = os.path.join(ROOT, "original", "Microsoft Flight Simulator v1.05 (198x)(Microsoft Corporation).ima")
DEFAULT_MEM = os.path.join(ROOT, "extracted", "mem_dump.bin")
DEFAULT_SYMS = os.path.join(ROOT, "docs", "symbols.txt")

TRACK = 8 * 512
AREA_TRACKS = [0x0F, 0x12, 0x15, 0x18, 0x1A]   # DS:03B4, set by the boot stream (04 records)
SCENERY_BASE = 0x3A84                           # DS:03F0
DS_LINEAR = 0x6180
HORIZON_TABLE, HORIZON_COUNT = 0x1D4F, 8

# Operand kinds: b byte, n count byte, i point-cache slot, c condition byte, w word,
# s signed word (coordinate), r rel16 branch (relative to the opcode's own address),
# v DS variable address. None = laid out by a special case in decode_one.
OPS = {
    0x00: ("dot", "sss"),
    0x01: ("move", "sss"),
    0x02: ("line", "sss"),
    0x05: ("viewpoint", "ssswww"),
    0x06: ("line2d", "bbbb"),
    0x08: ("clear_view", ""),
    0x0B: ("jump", "r"),
    0x0C: ("colour_dusk", "w"),
    0x0D: ("capture", "w"),
    0x0E: ("proj_scale", "ww"),
    0x10: ("cga_regs", ""),
    0x11: ("nop", ""),
    0x12: ("colour", "b"),
    0x15: ("draw_captured", ""),
    0x17: ("demo_script", None),
    0x18: ("call", "r"),
    0x19: ("return", ""),
    0x1A: ("copy", "vv"),
    0x1B: ("colour_dark_a", ""),
    0x1C: ("colour_dark_b", ""),
    0x1D: ("nav_station", None),
    0x1E: ("com_station", None),
    0x20: ("if_in", "rvss"),
    0x21: ("if_in", "rvssvss"),
    0x22: ("if_in", "rvssvssvss"),
    0x23: ("if_bits", "rvw"),
    0x24: ("origin", None),
    0x25: ("store", "vw"),
    0x28: ("jump_if", "crvv"),
    0x29: ("close", ""),
    0x2A: ("dotted", "ssssssn"),
    0x2B: ("dashed", "ssssssn"),
    0x2D: ("poly_end", ""),
    0x2E: ("colour_night", "w"),
    0x2F: ("poly_begin", ""),
    0x31: ("cache_point", "isss"),
    0x32: ("move_cached", "i"),
    0x33: ("line_cached", "i"),
    0x34: ("skip1", "b"),
    0x35: ("dot_cached", "i"),
    0x40: ("move_flat", "ss"),
    0x41: ("line_flat", "ss"),
    0x79: ("end", ""),
}
SIZES = {"b": 1, "n": 1, "i": 1, "c": 1, "w": 2, "s": 2, "r": 2, "v": 2}
NO_FALL = {0x0B, 0x17, 0x19, 0x1E, 0x79}   # never continue with the next byte
COND = {0: "==", 2: ">", 4: "<"}           # op 28: signed compare, jump table DS:3176
SHIFT = {0: 0, 2: 4, 4: 8, 6: 12, 8: 16}   # op 24: shift selector, jump table DS:316C

# Variables the scenery touches that are not (yet) in docs/symbols.txt; names proposed in
# docs/subphases/3.7.md. symbols.txt wins when it has a name.
EXTRA_VARS = {
    0x0406: "ground_service", 0x0412: "time_of_day", 0x0416: "overlay_fill",
    0x041D: "blink_bits", 0x0900: "altimeter_value", 0x090A: "field_elevation",
    0x0915: "heading_offset", 0x0917: "mag_variation", 0x1A19: "marker_a", 0x1A1B: "marker_b",
    0x1A1D: "ils_param_a", 0x1A1F: "ils_course", 0x1D48: "sky_pattern", 0x1D4A: "ground_pattern",
    0x1E24: "utc_offset", 0x1E53: "bomb_score", 0x31CE: "fill_pattern",
}


def load_vars(path):
    names, dwords = {}, set()
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            m = re.match(r"\s*var\s+0618:([0-9A-Fa-f]{4})\s+(\S+)(?:\s+(\w+))?", line.split("#", 1)[0])
            if m:
                a = int(m.group(1), 16)
                names[a] = m.group(2)
                if m.group(3) == "dword":
                    dwords.add(a)
    for a, n in EXTRA_VARS.items():
        names.setdefault(a, n)
    for a in dwords:   # the integer word of 16.16 positions
        names.setdefault(a + 2, names[a] + ".hi")
    return names


def read_area(img, area):
    """Returns the body of the area's 01 record, read the way boot_stream_byte does."""
    track, pos = AREA_TRACKS[area], 0

    def byte():
        nonlocal track, pos
        if pos == TRACK:
            track, pos = track + 1, 0
        b = img[track * TRACK + pos]
        pos += 1
        return b

    kind = byte()
    if kind != 1:
        raise ValueError(f"area {area}: record type {kind:02X}, expected 01")
    n = byte() | byte() << 8
    return bytes(byte() for _ in range(n - 3))


class Insn:
    __slots__ = ("op", "size", "vals", "targets", "dead")

    def __init__(self, op, size, vals, targets, dead):
        self.op, self.size, self.vals, self.targets, self.dead = op, size, vals, targets, dead


class Program:
    """A scenery program inside a 64 KB image of DS, decoded from one or more entry points."""

    def __init__(self, ds, lo, hi, var_names):
        self.ds, self.lo, self.hi, self.vars = ds, lo, hi, var_names
        self.insns = {}      # addr -> Insn
        self.data = {}       # addr -> (end, kind): embedded data (demo script, ATIS text)
        self.labels = {}     # addr -> label
        self.errors = []

    def w(self, a):
        return struct.unpack_from("<H", self.ds, a)[0]

    def s(self, a):
        return struct.unpack_from("<h", self.ds, a)[0]

    def decode_one(self, a):
        """Returns (op, size, vals, targets, data) for the instruction at a."""
        op = self.ds[a]
        if op not in OPS:
            raise ValueError(f"invalid opcode {op:02X}")
        kinds = OPS[op][1]
        if op == 0x17:     # rel16 to the next instruction; the bytes between are a demo script
            end = (a + self.s(a + 1)) & 0xFFFF
            return op, 3, [end], [end], (a + 3, end, "demo")
        if op == 0x1D:     # BCD frequency, then the station's east and north (16.16)
            return op, 11, [self.w(a + 1), *struct.unpack_from("<ii", self.ds, a + 3)], [], None
        if op == 0x1E:     # rel16 length, BCD frequency, 4 runways, 4 temperatures, ATIS text
            end = (a + self.s(a + 1)) & 0xFFFF
            return op, 13, [end, self.w(a + 3), bytes(self.ds[a + 5:a + 13])], [end], (a + 13, end, "atis")
        if op == 0x24:     # shift selector, then origin east, altitude, north (16.16)
            return op, 14, [self.ds[a + 1], *struct.unpack_from("<iii", self.ds, a + 2)], [], None
        vals, targets, p = [], [], a + 1
        for k in kinds:
            v = self.s(p) if k in "sr" else self.w(p) if k in "wv" else self.ds[p]
            if k == "r":
                v = (a + v) & 0xFFFF
                targets.append(v)
            vals.append(v)
            p += SIZES[k]
        return op, p - a, vals, targets, None

    def trace(self, entries, dead=False):
        work = list(entries)
        while work:
            a = work.pop()
            while a not in self.insns:
                if not (self.lo <= a < self.hi):
                    self.errors.append(f"{a:04X}: outside the program")
                    break
                try:
                    op, size, vals, targets, data = self.decode_one(a)
                except ValueError as e:
                    self.errors.append(f"{a:04X}: {e}")
                    break
                if a + size > self.hi:
                    self.errors.append(f"{a:04X}: instruction runs past the end")
                    break
                self.insns[a] = Insn(op, size, vals, targets, dead)
                if data:
                    self.data[data[0]] = data[1:]
                for t in targets:
                    self.labels.setdefault(t, None)
                    work.append(t)
                if op in NO_FALL:
                    break
                a += size

    def gaps(self):
        cov = bytearray(self.hi - self.lo)
        for a, i in self.insns.items():
            cov[a - self.lo:a - self.lo + i.size] = b"\1" * i.size
        for a, (end, _k) in self.data.items():
            cov[a - self.lo:end - self.lo] = b"\2" * (end - a)
        out, i = [], 0
        while i < len(cov):
            j = i
            while j < len(cov) and cov[j] == 0:
                j += 1
            if j > i:
                out.append((self.lo + i, self.lo + j))
            i = j + 1
        return cov, out

    def decode_dead(self):
        """Decodes unreached bytes linearly; returns the gaps that still don't decode."""
        for _ in range(8):
            _c, gaps = self.gaps()
            if not gaps:
                break
            errs = len(self.errors)
            for s, _e in gaps:
                self.trace([s], dead=True)
            self.errors = self.errors[:errs] + [f"dead code: {e}" for e in self.errors[errs:]]
        return self.gaps()[1]

    def name_labels(self, prefix, fixed=None):
        for a in self.labels:
            self.labels[a] = f"{prefix}{a:04X}"
        self.labels.update(fixed or {})

    def var(self, v):
        return self.vars.get(v, f"[{v:04X}]")

    def lab(self, t):
        return self.labels.get(t) or f"{t:04X}"

    def fmt(self, a):
        i = self.insns[a]
        op, v = i.op, i.vals
        name = f"{OPS[op][0]:<14}"
        xyz = lambda l: ", ".join(f"{x:6d}" for x in l)
        if op in (0x00, 0x01, 0x02, 0x40, 0x41):
            return name + xyz(v)
        if op == 0x31:
            return name + f"#{v[0]:<3d} {xyz(v[1:])}"
        if op in (0x32, 0x33, 0x35):
            return name + f"#{v[0]}"
        if op in (0x2A, 0x2B):
            return name + f"{xyz(v[:3])}  ->  {xyz(v[3:6])}  n={v[6]}"
        if op == 0x12:
            return name + f"{v[0]:X}"
        if op in (0x0C, 0x0D, 0x2E):
            return name + f"{v[0]:04X}"
        if op in (0x0B, 0x18):
            return name + self.lab(v[0])
        if op == 0x17:
            return name + f"{v[0] - a - 3} bytes, continue at {self.lab(v[0])}"
        if op == 0x1A:
            return name + f"{self.var(v[0])} = {self.var(v[1])}"
        if op == 0x25:
            return name + f"{self.var(v[0])} = {v[1]:04X}"
        if op in (0x20, 0x21, 0x22):
            conds = [f"{self.var(v[k])} in [{v[k + 1]}, {v[k + 2]}]" for k in range(1, len(v), 3)]
            return name + " and ".join(conds) + f" else {self.lab(v[0])}"
        if op == 0x23:
            return name + f"{self.var(v[1])} & {v[2]:04X} else {self.lab(v[0])}"
        if op == 0x28:
            return name + f"{self.var(v[2])} {COND.get(v[0], f'?{v[0]}')} {self.var(v[3])} goto {self.lab(v[1])}"
        if op == 0x24:
            return (name + f">>{SHIFT.get(v[0], '?'):<2}  east {v[1] / 65536:9.3f}  alt {v[2] / 65536:7.3f}"
                    f"  north {v[3] / 65536:9.3f}")
        if op == 0x1D:
            return name + f"NAV 1{v[0] >> 8:02X}.{v[0] & 0xFF:02X}  east {v[1] / 65536:.2f}  north {v[2] / 65536:.2f}"
        if op == 0x1E:
            return (name + f"COM 1{v[1] >> 8:02X}.{v[1] & 0xFF:02X}  runways {list(v[2][:4])}  temps {list(v[2][4:])}"
                    f"  ATIS {v[0] - a - 13} bytes, continue at {self.lab(v[0])}")
        if op == 0x05:
            return name + f"eye {v[0]}, {v[1]}, {v[2]}  pitch {v[3]:04X} bank {v[4]:04X} heading {v[5]:04X}"
        if op == 0x06:
            return name + f"({v[0]}, {v[1]}) - ({v[2]}, {v[3]})"
        if op == 0x0E:
            return name + f"{v[0]:04X} {v[1]:04X}"
        if op == 0x34:
            return name + f"{v[0]:02X}"
        return OPS[op][0]

    def data_text(self, a, end, kind):
        raw = self.ds[a:end]
        if kind == "demo":   # scancodes; 80h+n waits n steps; 7Fh restarts
            return " ".join("wait" + str(b - 0x80) if b >= 0x80 else "restart" if b == 0x7F else f"{b:02X}"
                            for b in raw)
        out = []             # ATIS: ASCII, 80h+k inserts fragment k (DS:362D), 00 ends
        for b in raw:
            out.append(f"{{{b - 0x80}}}" if b >= 0x80 else "|" if b == 0 else chr(b) if b >= 0x20 else f"<{b:02X}>")
        return "".join(out)

    def listing(self, out, show_bytes=False, show_text=False):
        _c, gaps = self.gaps()
        gap_at = dict(gaps)
        for a in sorted(set(self.insns) | set(self.data) | set(gap_at)):
            if self.labels.get(a):
                out.write(f"{self.labels[a]}:\n")
            if a in self.insns:
                i = self.insns[a]
                mark = "!" if i.dead else " "
                if show_bytes:
                    b = " ".join(f"{x:02X}" for x in self.ds[a:a + i.size])
                    b = b[:37] + "..." if len(b) > 40 else b
                    out.write(f"   {mark}{a:04X}  {b:<40}  {self.fmt(a)}\n")
                else:
                    out.write(f"   {mark}{a:04X}  {self.fmt(a)}\n")
            elif a in self.data:
                end, kind = self.data[a]
                out.write(f"    {a:04X}  .{kind} {end - a} bytes\n")
                if show_text:
                    out.write(f"          {self.data_text(a, end, kind)}\n")
            else:
                out.write(f"    {a:04X}  .undecoded {gap_at[a] - a} bytes\n")

    def frames(self):
        """Yields (origin insn addr, shift, origin, points) for each origin (op 24) block.

        A block is everything reachable from the origin instruction (through jumps, calls
        and both sides of tests) before the next origin, return or end."""
        for a0, i0 in sorted(self.insns.items()):
            if i0.op != 0x24:
                continue
            shift, oe, oy, on = SHIFT.get(i0.vals[0], 0), *i0.vals[1:]
            pts, seen, work = [], set(), [(a0 + i0.size, ())]
            while work:
                a, stack = work.pop()
                if a in seen or a not in self.insns:
                    continue
                seen.add(a)
                i = self.insns[a]
                v = i.vals
                if i.op == 0x24 or i.op == 0x79:
                    continue
                if i.op in (0x00, 0x01, 0x02):
                    pts.append(tuple(v))
                elif i.op == 0x31:
                    pts.append(tuple(v[1:]))
                elif i.op in (0x40, 0x41):
                    pts.append((v[0], 0, v[1]))
                elif i.op in (0x2A, 0x2B):
                    pts += [tuple(v[:3]), tuple(v[3:6])]
                if i.op == 0x18:
                    work.append((v[0], stack + (a + i.size,)))
                    continue
                if i.op == 0x19:
                    if stack:
                        work.append((stack[-1], stack[:-1]))
                    continue
                for t in i.targets:
                    work.append((t, stack))
                if i.op not in NO_FALL:
                    work.append((a + i.size, stack))
            k = (1 << shift) / 65536.0
            yield a0, shift, (oe / 65536.0, oy / 65536.0, on / 65536.0), [
                (oe / 65536.0 + x * k, oy / 65536.0 + y * k, on / 65536.0 + z * k) for x, y, z in pts]


def report(title, prog, args, out):
    cov, gaps = prog.gaps()
    total = prog.hi - prog.lo
    live = sum(i.size for i in prog.insns.values() if not i.dead)
    dead = sum(i.size for i in prog.insns.values() if i.dead)
    data = cov.count(2)
    bad = sum(e - s for s, e in gaps)
    out.write(f"; ==== {title}: DS:{prog.lo:04X}-{prog.hi - 1:04X}, {total} bytes ====\n")
    out.write(f"; {len(prog.insns)} instructions: reachable {live} bytes, dead code {dead} bytes (marked !), "
              f"embedded data {data} bytes, undecoded {bad} bytes -> coverage {100.0 * (total - bad) / total:.2f}%\n")
    for e in prog.errors:
        out.write(f"; note {e}\n")
    if args.check:
        allpts = []
        for a, shift, (oe, oy, on), pts in prog.frames():
            allpts += pts
            if pts:
                xs, ys, zs = zip(*pts)
                out.write(f";   origin {a:04X} >>{shift:<2} at E {oe:8.2f} N {on:8.2f}: {len(pts):3d} points, "
                          f"E {min(xs):8.2f}..{max(xs):8.2f}  N {min(zs):8.2f}..{max(zs):8.2f}  "
                          f"up {min(ys) * 256:7.1f}..{max(ys) * 256:7.1f} m\n")
        if allpts:
            xs, ys, zs = zip(*allpts)
            out.write(f"; all points (position units, 1 = 256 m): E {min(xs):.1f}..{max(xs):.1f}  "
                      f"N {min(zs):.1f}..{max(zs):.1f}\n")
    c = Counter(OPS[i.op][0] for i in prog.insns.values())
    if args.stats:
        out.write("; opcodes: " + ", ".join(f"{k} {n}" for k, n in sorted(c.items(), key=lambda kv: -kv[1])) + "\n")
    else:
        prog.listing(out, args.bytes, args.text)
    out.write("\n")
    return total - bad, total


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--image", default=DEFAULT_IMAGE)
    ap.add_argument("--mem", default=DEFAULT_MEM)
    ap.add_argument("--symbols", default=DEFAULT_SYMS)
    ap.add_argument("--area", type=int, action="append", choices=range(5))
    ap.add_argument("--horizon", action="store_true")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--bytes", action="store_true")
    ap.add_argument("--text", action="store_true")
    a = ap.parse_args()
    out = sys.stdout
    var_names = load_vars(a.symbols)
    img = open(a.image, "rb").read()
    mem = open(a.mem, "rb").read() if os.path.exists(a.mem) else None
    live = mem[DS_LINEAR:DS_LINEAR + 0x10000] if mem else None
    areas = a.area if a.area is not None else list(range(5))
    ok = total = 0
    for n in areas:
        body = read_area(img, n)
        ds = bytearray(0x10000)
        ds[SCENERY_BASE:SCENERY_BASE + len(body)] = body
        if live is not None and live[SCENERY_BASE:SCENERY_BASE + len(body)] == body:
            out.write(f"; area {n} is the one loaded in {a.mem}: identical bytes\n")
        prog = Program(ds, SCENERY_BASE, SCENERY_BASE + len(body), var_names)
        prog.trace([SCENERY_BASE])
        prog.decode_dead()
        prog.name_labels(f"a{n}_")
        k, t = report(f"area {n} (track {AREA_TRACKS[n]:02X})", prog, a, out)
        ok, total = ok + k, total + t
    if areas:
        out.write(f"; areas {','.join(map(str, areas))}: {ok}/{total} bytes decoded ({100.0 * ok / total:.2f}%)\n\n")
    if a.horizon:
        if live is None:
            sys.exit(f"--horizon needs a memory dump ({a.mem})")
        entries = [struct.unpack_from("<H", live, HORIZON_TABLE + 2 * k)[0] for k in range(HORIZON_COUNT)]
        prog = Program(live, min(entries), 0x10000, var_names)
        prog.trace(entries)
        prog.hi = max(x + i.size for x, i in prog.insns.items())   # end of the last program
        prog.name_labels("h_", {e: f"horizon_{k}" for k, e in enumerate(entries)})
        report("horizon programs, octants 0-7 (memory dump)", prog, a, out)


if __name__ == "__main__":
    main()
