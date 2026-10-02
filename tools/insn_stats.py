"""Count the original (non-native) instructions executed in campaign sessions, per routine.

usage: python tools/insn_stats.py [SESSIONS] [--from FRAME] [-- EXTRA_ARGS...]

SESSIONS is a comma-separated list of campaign session names (default: demo,flight_keys,war,
editor_values). Each runs with --stats-from FRAME (default 300, after the start-up menus)
and --stats-out; the executed addresses are attributed to the routine (nearest preceding
non-loc_ label in extracted/fs1.asm, segment 0050) and the top routines are printed.
EXTRA_ARGS go to fs1.exe as is, e.g. -- --native-off main_loop.
"""
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trace_campaign import EXE, HEADLESS_ENV, ROOT, sessions  # noqa: E402

ASM = os.path.join(ROOT, "extracted", "fs1.asm")


def routine_starts():
    starts, label = [], None
    for line in open(ASM, encoding="utf-8", errors="replace"):
        m = re.match(r"^([A-Za-z_][\w+]*):", line)
        if m:
            label = m.group(1)
            continue
        m = re.match(r"^\s+([0-9A-F]{4})\s", line)
        if m and label:
            if not label.startswith("loc_"):
                starts.append((int(m.group(1), 16), label))
            label = None
    starts.sort()
    return starts


def name_of(starts, linear):
    if not 0x500 <= linear < 0x500 + 0x10000:
        return f"(outside 0050: {linear:05X})" if linear < 0xF0000 else "(BIOS)"
    off = linear - 0x500
    lo, hi = 0, len(starts)
    while lo < hi:
        mid = (lo + hi) // 2
        if starts[mid][0] <= off:
            lo = mid + 1
        else:
            hi = mid
    return starts[lo - 1][1] if lo else f"{off:04X}"


def main():
    argv = sys.argv[1:]
    extra = []
    if "--" in argv:
        i = argv.index("--")
        argv, extra = argv[:i], argv[i + 1:]
    start = 300
    if "--from" in argv:
        i = argv.index("--from")
        start = int(argv[i + 1])
        del argv[i:i + 2]
    names = (argv[0] if argv else "demo,flight_keys,war,editor_values").split(",")
    starts = routine_starts()
    for name, args, frames in sessions():
        if name not in names:
            continue
        out = os.path.join(tempfile.gettempdir(), f"fs1_stats_{name}.txt")
        cmd = [EXE, "--frames", str(frames), "--stats-from", str(start), "--stats-out", out] + extra + args
        r = subprocess.run(cmd, cwd=ROOT, env=HEADLESS_ENV, capture_output=True, text=True, timeout=3600)
        total = re.search(r"stats: from frame \d+: original instructions (\d+), native calls (\d+)", r.stdout + r.stderr)
        per = Counter()
        for line in open(out):
            a, n = line.split()
            per[name_of(starts, int(a, 16))] += int(n)
        print(f"{name}: frames {start}..{frames}: original instructions {total.group(1)}, native calls {total.group(2)}")
        for routine, n in per.most_common(15):
            print(f"    {routine:28} {n:>12}")


if __name__ == "__main__":
    main()
