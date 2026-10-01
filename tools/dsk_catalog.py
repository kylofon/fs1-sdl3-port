"""List the DOS 3.3 catalog of an Apple II .dsk image and per-track usage."""
import sys

TYPES = {0: 'T', 1: 'I', 2: 'A', 4: 'B', 8: 'S', 0x10: 'R', 0x20: 'a', 0x40: 'b'}

def main(path):
    d = open(path, "rb").read()
    sec = lambda t, s: d[(t * 16 + s) * 256:(t * 16 + s + 1) * 256]
    v = sec(17, 0)
    print(f"VTOC: catalog {v[1]}/{v[2]} DOS rel {v[3]} vol {v[6]} tracks {v[0x34]} sectors {v[0x35]}")
    t, s, seen = v[1], v[2], set()
    while t and (t, s) not in seen and t < 35:
        seen.add((t, s))
        c = sec(t, s)
        for i in range(7):
            e = c[0x0b + i * 35:0x0b + (i + 1) * 35]
            if e[0] in (0, 0xff):
                continue
            name = bytes(b & 0x7f for b in e[3:33]).decode(errors="replace").rstrip()
            lock = '*' if e[2] & 0x80 else ' '
            print(f"{lock}{TYPES.get(e[2] & 0x7f, '?')} TS {e[0]:2d}/{e[1]:2d} {int.from_bytes(e[33:35], 'little'):4d} sectors  {name}")
        t, s = c[1], c[2]
    print("non-empty sectors per track:")
    print(" ".join(f"{tr}:{sum(1 for s in range(16) if any(sec(tr, s)))}" for tr in range(35)))

if __name__ == "__main__":
    main(sys.argv[1])
