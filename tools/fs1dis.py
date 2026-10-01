"""Coverage-guided disassembler for MS Flight Simulator 1.05 (CS=0050 program).

usage: python tools/fs1dis.py [--image extracted/boot_mem.bin] [--trace extracted/trace.bin]
                              [--symbols docs/symbols.txt] [--out extracted]

Writes (to the gitignored extracted/ folder, since they contain the game's code):
  fs1.asm        annotated listing of segment 0050
  callgraph.txt  every subroutine with size, callers, callees and the variables it touches
  vars.txt       every DS variable referenced, with readers and writers

Code is found from the runtime trace (tools/trace_campaign.py), then extended by
recursive descent through static branch targets ("static" = never executed in traces).
Memory operands without a segment override are assumed to use DS=0618, which holds
for the game's main code; symbol names from docs/symbols.txt replace raw offsets.
"""
import argparse
import collections
import os
import re

import capstone
from capstone import x86

CS = 0x0050
DS = 0x0618
CODE_END = 0x6360  # end of the 01-block (linear 0x6860) as an offset in CS

T_EXEC, T_CALL, T_JUMP, T_INT, T_READ, T_WRITE, T_SMC = 1, 2, 4, 8, 0x10, 0x20, 0x40


def load_symbols(path):
    code, var = {}, {}
    if not os.path.exists(path):
        return code, var
    for line in open(path, encoding="utf-8"):
        line = line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        m = re.match(r"\s*(code|var)\s+([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+(\S+)(?:\s+(\w+))?\s*(?:;\s*(.*))?$", line)
        if not m:
            continue
        kind, seg, off, name, typ, comment = m.groups()
        entry = (name, typ or "", comment or "")
        (code if kind == "code" else var)[int(off, 16)] = entry
    return code, var


class Disassembler:
    def __init__(self, image, trace, code_syms, var_syms):
        self.mem = image
        self.trace = trace
        self.code_syms = code_syms
        self.var_syms = var_syms
        self.md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_16)
        self.md.detail = True
        self.insns = {}          # offset -> capstone insn
        self.executed = set()
        self.call_targets = set()
        self.jump_targets = set()
        self.int_targets = set()

    def lin(self, off):
        return CS * 16 + off

    def tflags(self, off):
        return self.trace[self.lin(off)] if self.trace else 0

    def decode(self, off):
        if off in self.insns:
            return self.insns[off]
        base = self.lin(off)
        for insn in self.md.disasm(bytes(self.mem[base:base + 16]), off, 1):
            self.insns[off] = insn
            return insn
        return None

    def run(self):
        work = []
        for off in range(0, CODE_END):
            f = self.tflags(off)
            if f & T_EXEC:
                self.executed.add(off)
                work.append(off)
            if f & T_CALL:
                self.call_targets.add(off)
            if f & T_JUMP:
                self.jump_targets.add(off)
            if f & T_INT:
                self.int_targets.add(off)
        for off in self.code_syms:
            if off < CODE_END:
                work.append(off)
                self.call_targets.add(off)
        seen = set()
        while work:
            off = work.pop()
            while 0 <= off < CODE_END and off not in seen:
                seen.add(off)
                insn = self.decode(off)
                if insn is None:
                    break
                nxt = off + insn.size
                kind = self.flow(insn)
                target = self.static_target(insn)
                if target is not None and target < CODE_END:
                    if kind == "call":
                        self.call_targets.add(target)
                    else:
                        self.jump_targets.add(target)
                    work.append(target)
                if kind in ("ret", "jmp", "hlt"):
                    break
                off = nxt

    @staticmethod
    def flow(insn):
        m = insn.mnemonic
        if m.startswith("ret") or m == "iret":
            return "ret"
        if m == "call" or m == "lcall":
            return "call"
        if m in ("jmp", "ljmp"):
            return "jmp"
        if m == "hlt":
            return "hlt"
        if m.startswith("j") or m.startswith("loop"):
            return "jcc"
        return ""

    @staticmethod
    def static_target(insn):
        if insn.mnemonic in ("call", "jmp") or insn.mnemonic.startswith("j") or insn.mnemonic.startswith("loop"):
            ops = insn.operands
            if len(ops) == 1 and ops[0].type == x86.X86_OP_IMM:
                return ops[0].imm & 0xFFFF
        return None

    # ---- naming ----

    def code_name(self, off):
        if off in self.code_syms:
            return self.code_syms[off][0]
        if off in self.int_targets:
            return f"int_{off:04X}"
        if off in self.call_targets:
            return f"sub_{off:04X}"
        return f"loc_{off:04X}"

    def mem_refs(self, insn):
        """DS-relative absolute/base+disp memory operands (offset, access) for cross-references."""
        refs = []
        for op in insn.operands:
            if op.type != x86.X86_OP_MEM:
                continue
            seg = op.mem.segment
            if seg not in (0, x86.X86_REG_DS):
                continue
            if op.mem.base in (x86.X86_REG_BP,):
                continue
            disp = op.mem.disp & 0xFFFF
            if op.mem.base == 0 and op.mem.index == 0:
                refs.append((disp, op.access))
            elif disp >= 0x100:
                refs.append((disp, op.access))  # table base
        return refs

    def var_name(self, off):
        if off in self.var_syms:
            return self.var_syms[off][0]
        sizes = {"word": 2, "dword": 4, "table": 64, "text": 16}
        for base in range(off - 1, off - 64, -1):
            if base in self.var_syms:
                if off - base < sizes.get(self.var_syms[base][1], 1):
                    return f"{self.var_syms[base][0]}+{off - base}"
                return None
        return None

    def render(self, insn):
        text = f"{insn.mnemonic} {insn.op_str}".strip()
        target = self.static_target(insn)
        if target is not None and target < CODE_END:
            text = re.sub(r"0x[0-9a-f]+$", self.code_name(target), text)

        def repl(m):
            val = int(m.group(1), 16)
            name = self.var_name(val)
            return f"[{m.group(0)[1:-1].replace(m.group(1), name)}]" if name else m.group(0)

        if "[" in text and not re.search(r"\b(ss|es|cs):", text):
            text = re.sub(r"\[[^\]]*?(0x[0-9a-f]+)[^\]]*\]", repl, text)
        return text

    # ---- outputs ----

    def write_listing(self, path):
        with open(path, "w", encoding="utf-8") as out:
            out.write(f"; MS Flight Simulator 1.05 - segment {CS:04X} (generated by tools/fs1dis.py)\n")
            out.write("; columns: offset  bytes  instruction  ; flags (S = never executed in traces)\n\n")
            off = 0
            while off < CODE_END:
                if off in self.insns and (off in self.executed or self.is_reachable(off)):
                    insn = self.insns[off]
                    if off in self.call_targets or off in self.int_targets or off in self.code_syms:
                        comment = self.code_syms.get(off, ("", "", ""))[2]
                        out.write(f"\n{self.code_name(off)}:{'  ; ' + comment if comment else ''}\n")
                    elif off in self.jump_targets:
                        out.write(f"{self.code_name(off)}:\n")
                    raw = " ".join(f"{b:02X}" for b in insn.bytes)
                    flags = "" if off in self.executed else "S"
                    if any(self.tflags(off + i) & T_SMC for i in range(insn.size)):
                        flags += " SMC"
                    out.write(f"    {off:04X}  {raw:<20} {self.render(insn):<44} ; {flags}\n")
                    off += insn.size
                else:
                    start = off
                    while off < CODE_END and not (off in self.insns and (off in self.executed or self.is_reachable(off))):
                        off += 1
                    self.write_data(out, start, off)

    def is_reachable(self, off):
        return off in self.insns and self._reach_ok(off)

    def _reach_ok(self, off):
        # decoded by recursive descent; insns dict only holds descended code
        return True

    def write_data(self, out, start, end):
        out.write(f"; ---- data {start:04X}-{end - 1:04X} ({end - start} bytes)\n")
        for row in range(start, end, 16):
            chunk = self.mem[self.lin(row):self.lin(min(row + 16, end))]
            text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            out.write(f"    {row:04X}  db {', '.join(f'{b:02X}h' for b in chunk):<88} ; {text}\n")

    def subroutines(self):
        """Group instructions into subroutines: from each call target until the next call target."""
        starts = sorted(o for o in self.call_targets | self.int_targets | set(self.code_syms) if o < CODE_END)
        subs = []
        for i, s in enumerate(starts):
            end = starts[i + 1] if i + 1 < len(starts) else CODE_END
            body = [o for o in sorted(self.insns) if s <= o < end]
            subs.append((s, end, body))
        return subs

    def write_callgraph(self, path, vars_path):
        callers = collections.defaultdict(set)
        info = []
        var_rw = collections.defaultdict(lambda: [set(), set()])
        for s, end, body in self.subroutines():
            callees, reads, writes = set(), set(), set()
            executed = sum(1 for o in body if o in self.executed)
            for o in body:
                insn = self.insns[o]
                t = self.static_target(insn)
                if self.flow(insn) == "call" and t is not None:
                    callees.add(t)
                    callers[t].add(s)
                for disp, access in self.mem_refs(insn):
                    if access & capstone.CS_AC_READ:
                        reads.add(disp)
                        var_rw[disp][0].add(s)
                    if access & capstone.CS_AC_WRITE:
                        writes.add(disp)
                        var_rw[disp][1].add(s)
            info.append((s, end, len(body), executed, callees, reads, writes))
        with open(path, "w", encoding="utf-8") as out:
            for s, end, n, executed, callees, reads, writes in info:
                comment = self.code_syms.get(s, ("", "", ""))[2]
                out.write(f"{self.code_name(s)}  {s:04X}-{end - 1:04X}  {n} insns ({executed} executed)"
                          f"{'  ; ' + comment if comment else ''}\n")
                out.write(f"    called by: {', '.join(self.code_name(c) for c in sorted(callers[s])) or '-'}\n")
                out.write(f"    calls:     {', '.join(self.code_name(c) for c in sorted(callees)) or '-'}\n")
                fmt = lambda vs: ", ".join(self.var_name(v) or f"{v:04X}" for v in sorted(vs)) or "-"
                out.write(f"    reads:     {fmt(reads)}\n    writes:    {fmt(writes)}\n\n")
        with open(vars_path, "w", encoding="utf-8") as out:
            for v in sorted(var_rw):
                r, w = var_rw[v]
                name = self.var_name(v) or ""
                comment = self.var_syms.get(v, ("", "", ""))[2]
                out.write(f"{DS:04X}:{v:04X} {name:<20} R:{len(r):3d} W:{len(w):3d}  {comment}\n")
                out.write(f"    read by:    {', '.join(self.code_name(c) for c in sorted(r)) or '-'}\n")
                out.write(f"    written by: {', '.join(self.code_name(c) for c in sorted(w)) or '-'}\n")


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", default=os.path.join(root, "extracted", "boot_mem.bin"))
    ap.add_argument("--trace", default=os.path.join(root, "extracted", "trace.bin"))
    ap.add_argument("--symbols", default=os.path.join(root, "docs", "symbols.txt"))
    ap.add_argument("--out", default=os.path.join(root, "extracted"))
    a = ap.parse_args()

    image = bytearray(open(a.image, "rb").read())
    image += bytes(0x100000 - len(image))
    trace = open(a.trace, "rb").read() if os.path.exists(a.trace) else None
    code_syms, var_syms = load_symbols(a.symbols)
    d = Disassembler(image, trace, code_syms, var_syms)
    d.run()
    os.makedirs(a.out, exist_ok=True)
    d.write_listing(os.path.join(a.out, "fs1.asm"))
    d.write_callgraph(os.path.join(a.out, "callgraph.txt"), os.path.join(a.out, "vars.txt"))
    code_bytes = sum(i.size for i in d.insns.values())
    exec_bytes = sum(d.insns[o].size for o in d.executed if o in d.insns)
    print(f"decoded {len(d.insns)} instructions ({code_bytes} bytes), {exec_bytes} bytes executed in traces; "
          f"{len(d.call_targets)} subroutines, {len(d.int_targets)} interrupt entries")


if __name__ == "__main__":
    main()
