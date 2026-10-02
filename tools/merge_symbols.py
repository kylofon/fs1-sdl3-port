"""Merge symbol lines proposed in docs/subphases/3.*.md into docs/symbols.txt.

usage: python tools/merge_symbols.py [--dry-run] [--replace] [NOTES...]   (default: all notes files)

By default only symbols at new addresses are added. Since 3.15, docs/symbols.txt is curated
directly (and generates src/game/state.h), so older notes must not overwrite it; pass
--replace to let a notes file correct existing entries.

Lines in the notes that use symbols.txt syntax (`code SEG:OFF name ...` / `var SEG:OFF name ...`)
are merged by address: an existing entry at the same kind and address is replaced in place
(the notes are newer and usually correct earlier guesses), new ones are appended under a
section per notes file. A name already used at a different address is reported, not merged.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYMBOLS = os.path.join(ROOT, "docs", "symbols.txt")
LINE = re.compile(r"^\s*(code|var)\s+([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+(\S+)")


def key(m):
    return (m.group(1), m.group(2).upper(), m.group(3).upper())


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    notes = args or sorted(glob.glob(os.path.join(ROOT, "docs", "subphases", "3.*.md")),
                           key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])
    lines = open(SYMBOLS, encoding="utf-8").read().split("\n")
    index = {}
    names = {}
    for i, l in enumerate(lines):
        m = LINE.match(l)
        if m:
            index[key(m)] = i
            names[m.group(4)] = key(m)
    replaced = added = skipped = 0
    for path in notes:
        header = f"\n# ---- from {os.path.relpath(path, ROOT).replace(os.sep, '/')} " + "-" * 20
        for l in open(path, encoding="utf-8").read().split("\n"):
            m = LINE.match(l)
            if not m:
                continue
            l = l.strip()
            k, name = key(m), m.group(4)
            if name in names and names[name] != k:
                print(f"{os.path.basename(path)}: name {name} already at {names[name][1]}:{names[name][2]}, "
                      f"skipped {k[1]}:{k[2]}")
                skipped += 1
                continue
            if k in index:
                if "--replace" in sys.argv and lines[index[k]].strip() != l:
                    names.pop(LINE.match(lines[index[k]]).group(4), None)
                    lines[index[k]] = l
                    replaced += 1
            else:
                if header:
                    lines.append(header)
                    header = None
                lines.append(l)
                index[k] = len(lines) - 1
                added += 1
            names[name] = k
    print(f"replaced {replaced}, added {added}, skipped {skipped}")
    if not dry:
        open(SYMBOLS, "w", encoding="utf-8").write("\n".join(lines).rstrip("\n") + "\n")


if __name__ == "__main__":
    main()
