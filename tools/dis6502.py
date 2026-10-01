"""Minimal NMOS 6502 disassembler.  usage: dis6502.py FILE OFFSET LENGTH LOADADDR"""
import sys

OPS = {}
def _def(mode, table):
    for op, mn in table.items():
        OPS[op] = (mn, mode)

_def('imp', {0x00:'BRK',0x08:'PHP',0x18:'CLC',0x28:'PLP',0x38:'SEC',0x40:'RTI',0x48:'PHA',0x58:'CLI',0x60:'RTS',0x68:'PLA',0x78:'SEI',0x88:'DEY',0x8A:'TXA',0x98:'TYA',0x9A:'TXS',0xA8:'TAY',0xAA:'TAX',0xB8:'CLV',0xBA:'TSX',0xC8:'INY',0xCA:'DEX',0xD8:'CLD',0xE8:'INX',0xEA:'NOP',0xF8:'SED'})
_def('acc', {0x0A:'ASL',0x2A:'ROL',0x4A:'LSR',0x6A:'ROR'})
_def('imm', {0x09:'ORA',0x29:'AND',0x49:'EOR',0x69:'ADC',0xA0:'LDY',0xA2:'LDX',0xA9:'LDA',0xC0:'CPY',0xC9:'CMP',0xE0:'CPX',0xE9:'SBC'})
_def('zp',  {0x05:'ORA',0x06:'ASL',0x24:'BIT',0x25:'AND',0x26:'ROL',0x45:'EOR',0x46:'LSR',0x65:'ADC',0x66:'ROR',0x84:'STY',0x85:'STA',0x86:'STX',0xA4:'LDY',0xA5:'LDA',0xA6:'LDX',0xC4:'CPY',0xC5:'CMP',0xC6:'DEC',0xE4:'CPX',0xE5:'SBC',0xE6:'INC'})
_def('zpx', {0x15:'ORA',0x16:'ASL',0x35:'AND',0x36:'ROL',0x55:'EOR',0x56:'LSR',0x75:'ADC',0x76:'ROR',0x94:'STY',0x95:'STA',0xB4:'LDY',0xB5:'LDA',0xD5:'CMP',0xD6:'DEC',0xF5:'SBC',0xF6:'INC'})
_def('zpy', {0x96:'STX',0xB6:'LDX'})
_def('abs', {0x0D:'ORA',0x0E:'ASL',0x20:'JSR',0x2C:'BIT',0x2D:'AND',0x2E:'ROL',0x4C:'JMP',0x4D:'EOR',0x4E:'LSR',0x6D:'ADC',0x6E:'ROR',0x8C:'STY',0x8D:'STA',0x8E:'STX',0xAC:'LDY',0xAD:'LDA',0xAE:'LDX',0xCC:'CPY',0xCD:'CMP',0xCE:'DEC',0xEC:'CPX',0xED:'SBC',0xEE:'INC'})
_def('abx', {0x1D:'ORA',0x1E:'ASL',0x3D:'AND',0x3E:'ROL',0x5D:'EOR',0x5E:'LSR',0x7D:'ADC',0x7E:'ROR',0x9D:'STA',0xBC:'LDY',0xBD:'LDA',0xDD:'CMP',0xDE:'DEC',0xFD:'SBC',0xFE:'INC'})
_def('aby', {0x19:'ORA',0x39:'AND',0x59:'EOR',0x79:'ADC',0x99:'STA',0xB9:'LDA',0xBE:'LDX',0xD9:'CMP',0xF9:'SBC'})
_def('ind', {0x6C:'JMP'})
_def('izx', {0x01:'ORA',0x21:'AND',0x41:'EOR',0x61:'ADC',0x81:'STA',0xA1:'LDA',0xC1:'CMP',0xE1:'SBC'})
_def('izy', {0x11:'ORA',0x31:'AND',0x51:'EOR',0x71:'ADC',0x91:'STA',0xB1:'LDA',0xD1:'CMP',0xF1:'SBC'})
_def('rel', {0x10:'BPL',0x30:'BMI',0x50:'BVC',0x70:'BVS',0x90:'BCC',0xB0:'BCS',0xD0:'BNE',0xF0:'BEQ'})

SIZE = {'imp':1,'acc':1,'imm':2,'zp':2,'zpx':2,'zpy':2,'izx':2,'izy':2,'rel':2,'abs':3,'abx':3,'aby':3,'ind':3}
FMT = {'imp':'','acc':'A','imm':'#${:02X}','zp':'${:02X}','zpx':'${:02X},X','zpy':'${:02X},Y','izx':'(${:02X},X)','izy':'(${:02X}),Y','abs':'${:04X}','abx':'${:04X},X','aby':'${:04X},Y','ind':'(${:04X})'}

def disasm(buf, base):
    pc = 0
    while pc < len(buf):
        op = buf[pc]
        if op not in OPS:
            print(f"{base+pc:04X}  {op:02X}         .byte ${op:02X}")
            pc += 1
            continue
        mn, mode = OPS[op]
        n = SIZE[mode]
        raw = buf[pc:pc+n]
        if len(raw) < n:
            break
        if mode == 'rel':
            arg = f"${(base + pc + 2 + (raw[1] - 256 if raw[1] > 127 else raw[1])) & 0xFFFF:04X}"
        elif n == 3:
            arg = FMT[mode].format(raw[1] | raw[2] << 8)
        elif n == 2:
            arg = FMT[mode].format(raw[1])
        else:
            arg = FMT[mode]
        print(f"{base+pc:04X}  {' '.join(f'{b:02X}' for b in raw):9}  {mn} {arg}")
        pc += n

if __name__ == "__main__":
    f, off, ln, base = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0), int(sys.argv[4], 0)
    disasm(open(f, "rb").read()[off:off+ln], base)
