"""
Abstraction of the 6502 processor CPU opcodes.
"""

from functools import partialmethod
from xcomp.model import Op
from xcomp.model import OpCode
from xcomp.model import AddressMode as M


opcode_table = (
    OpCode("adc", M.immediate,   0x69),
    OpCode("adc", M.zeropage,    0x65),
    OpCode("adc", M.zeropage_x,  0x75),
    OpCode("adc", M.absolute,    0x6D),
    OpCode("adc", M.absolute_x,  0x7D),
    OpCode("adc", M.absolute_y,  0x79),
    OpCode("adc", M.indirect_x,  0x61),
    OpCode("adc", M.indirect_y,  0x71),
    OpCode("and", M.immediate,   0x29),
    OpCode("and", M.zeropage,    0x25),
    OpCode("and", M.zeropage_x,  0x35),
    OpCode("and", M.absolute,    0x2D),
    OpCode("and", M.absolute_x,  0x3D),
    OpCode("and", M.absolute_y,  0x39),
    OpCode("and", M.indirect_x,  0x21),
    OpCode("and", M.indirect_y,  0x31),
    OpCode("asl", M.accumulator, 0x0A),
    OpCode("asl", M.zeropage,    0x06),
    OpCode("asl", M.zeropage_x,  0x16),
    OpCode("asl", M.absolute,    0x0E),
    OpCode("asl", M.absolute_x,  0x1E),
    OpCode("bcc", M.relative,    0x90),
    OpCode("bcs", M.relative,    0xB0),
    OpCode("beq", M.relative,    0xF0),
    OpCode("bit", M.zeropage,    0x24),
    OpCode("bit", M.absolute,    0x2C),
    OpCode("bmi", M.relative,    0x30),
    OpCode("bne", M.relative,    0xD0),
    OpCode("bpl", M.relative,    0x10),
    OpCode("brk", M.implied,     0x00),
    OpCode("bvc", M.relative,    0x50),
    OpCode("bvc", M.relative,    0x70),
    OpCode("clc", M.implied,     0x18),
    OpCode("cld", M.implied,     0xD8),
    OpCode("cli", M.implied,     0x58),
    OpCode("clv", M.implied,     0xB8),
    OpCode("cmp", M.immediate,   0xC9),
    OpCode("cmp", M.zeropage,    0xC5),
    OpCode("cmp", M.zeropage_x,  0xD5),
    OpCode("cmp", M.absolute,    0xCD),
    OpCode("cmp", M.absolute_x,  0xDD),
    OpCode("cmp", M.absolute_y,  0xD9),
    OpCode("cmp", M.indirect_x,  0xC1),
    OpCode("cmp", M.indirect_y,  0xD1),
    OpCode("cpx", M.immediate,   0xE0),
    OpCode("cpx", M.zeropage,    0xE4),
    OpCode("cpx", M.absolute,    0xEC),
    OpCode("cpy", M.immediate,   0xC0),
    OpCode("cpy", M.zeropage,    0xC4),
    OpCode("cpy", M.absolute,    0xCC),
    OpCode("dec", M.zeropage,    0xC6),
    OpCode("dec", M.zeropage_x,  0xD6),
    OpCode("dec", M.absolute,    0xCE),
    OpCode("dec", M.absolute_x,  0xDE),
    OpCode("dec", M.implied,     0xCA),
    OpCode("dec", M.implied,     0x88),
    OpCode("eor", M.immediate,   0x49),
    OpCode("eor", M.zeropage,    0x45),
    OpCode("eor", M.zeropage_x,  0x55),
    OpCode("eor", M.absolute,    0x4D),
    OpCode("eor", M.absolute_x,  0x5D),
    OpCode("eor", M.absolute_y,  0x59),
    OpCode("eor", M.indirect_x,  0x41),
    OpCode("eor", M.indirect_y,  0x51),
    OpCode("inc", M.zeropage,    0xE6),
    OpCode("inc", M.zeropage_x,  0xF6),
    OpCode("inc", M.absolute,    0xEE),
    OpCode("inc", M.absolute_x,  0xFE),
    OpCode("inx", M.implied,     0xE8),
    OpCode("iny", M.implied,     0xC8),
    OpCode("jmp", M.absolute,    0x4C),
    OpCode("jmp", M.indirect,    0x6C),
    OpCode("jsr", M.absolute,    0x20),
    OpCode("lda", M.immediate,   0xA9),
    OpCode("lda", M.zeropage,    0xA5),
    OpCode("lda", M.zeropage_x,  0xB5),
    OpCode("lda", M.absolute,    0xAD),
    OpCode("lda", M.absolute_x,  0xBD),
    OpCode("lda", M.absolute_y,  0xB9),
    OpCode("lda", M.indirect_x,  0xA1),
    OpCode("lda", M.indirect_y,  0xB1),
    OpCode("ldx", M.immediate,   0xA2),
    OpCode("ldx", M.zeropage,    0xA6),
    OpCode("ldx", M.zeropage_y,  0xB6),
    OpCode("ldx", M.absolute,    0xAE),
    OpCode("ldx", M.absolute_y,  0xBE),
    OpCode("ldy", M.immediate,   0xA0),
    OpCode("ldy", M.zeropage,    0xA4),
    OpCode("ldy", M.zeropage_x,  0xB4),
    OpCode("ldy", M.absolute,    0xAC),
    OpCode("ldy", M.absolute_x,  0xBC),
    OpCode("lsr", M.accumulator, 0x4A),
    OpCode("lsr", M.zeropage,    0x46),
    OpCode("lsr", M.zeropage_x,  0x56),
    OpCode("lsr", M.absolute,    0x4E),
    OpCode("lsr", M.absolute_x,  0x5E),
    OpCode("nop", M.implied,     0xEA),
    OpCode("ora", M.immediate,   0x09),
    OpCode("ora", M.zeropage,    0x05),
    OpCode("ora", M.zeropage_x,  0x15),
    OpCode("ora", M.absolute,    0x0D),
    OpCode("ora", M.absolute_x,  0x1D),
    OpCode("ora", M.absolute_y,  0x19),
    OpCode("ora", M.indirect_x,  0x01),
    OpCode("ora", M.indirect_y,  0x11),
    OpCode("pha", M.implied,     0x48),
    OpCode("php", M.implied,     0x08),
    OpCode("pla", M.implied,     0x68),
    OpCode("plp", M.implied,     0x28),
    OpCode("rol", M.accumulator, 0x2A),
    OpCode("rol", M.zeropage,    0x26),
    OpCode("rol", M.zeropage_x,  0x36),
    OpCode("rol", M.absolute,    0x2E),
    OpCode("rol", M.absolute_x,  0x3E),
    OpCode("ror", M.accumulator, 0x6A),
    OpCode("ror", M.zeropage,    0x66),
    OpCode("ror", M.zeropage_x,  0x76),
    OpCode("ror", M.absolute,    0x6E),
    OpCode("ror", M.absolute_x,  0x7E),
    OpCode("rti", M.implied,     0x40),
    OpCode("rts", M.implied,     0x60),
    OpCode("sbc", M.immediate,   0xE9),
    OpCode("sbc", M.zeropage,    0xE5),
    OpCode("sbc", M.zeropage_x,  0xF5),
    OpCode("sbc", M.absolute,    0xED),
    OpCode("sbc", M.absolute_x,  0xFD),
    OpCode("sbc", M.absolute_y,  0xF9),
    OpCode("sbc", M.indirect_x,  0xE1),
    OpCode("sbc", M.indirect_y,  0xF1),
    OpCode("sec", M.implied,     0x38),
    OpCode("sed", M.implied,     0xF8),
    OpCode("sei", M.implied,     0x78),
    OpCode("sta", M.zeropage,    0x85),
    OpCode("sta", M.zeropage_x,  0x95),
    OpCode("sta", M.absolute,    0x8D),
    OpCode("sta", M.absolute_x,  0x9D),
    OpCode("sta", M.absolute_y,  0x99),
    OpCode("sta", M.indirect_x,  0x81),
    OpCode("sta", M.indirect_y,  0x91),
    OpCode("stx", M.zeropage,    0x86),
    OpCode("stx", M.zeropage_y,  0x96),
    OpCode("stx", M.absolute,    0x8E),
    OpCode("sty", M.zeropage,    0x84),
    OpCode("sty", M.zeropage_x,  0x94),
    OpCode("sty", M.absolute,    0x8C),
    OpCode("tax", M.implied,     0xAA),
    OpCode("tay", M.implied,     0xA8),
    OpCode("tsx", M.implied,     0xBA),
    OpCode("txa", M.implied,     0x8A),
    OpCode("txs", M.implied,     0x9A),
    OpCode("tya", M.implied,     0x98),
)

# opcodes by name and addressing mode
opcode_xref = {}
for op in opcode_table:
    opcode_xref.setdefault(op.name, {})[op.mode] = op

# opcodes by machinecode
opcode_disasm = {x.value: x for x in opcode_table}

# grammar parameter specs by addressing mode
addressmode_params = {
    M.accumulator: ['"a"'],
    M.absolute:    ['expr16'],
    M.absolute_x:  ['expr16', 'comma', '"x"'],
    M.absolute_y:  ['expr16', 'comma', '"y"'],
    M.immediate:   ['hash', 'expr8'],
    M.implied:     [],
    M.indirect:    ['lparen', 'expr16', 'rparen'],
    M.indirect_x:  ['lparen', 'expr8', 'comma', '"x"', 'rparen'],
    M.indirect_y:  ['lparen', 'expr8', 'rparen', 'comma', '"y"'],
    M.relative:    ['expr8'],
    M.zeropage:    ['expr8'],
    M.zeropage_x:  ['expr8', 'comma', '"x"'],
    M.zeropage_y:  ['expr8', 'comma', '"y"'],
}

addressmode_args = {
    M.accumulator: 0,
    M.absolute:    1,
    M.absolute_x:  1,
    M.absolute_y:  1,
    M.immediate:   1,
    M.implied:     0,
    M.indirect:    1,
    M.indirect_x:  1,
    M.indirect_y:  1,
    M.relative:    1,
    M.zeropage:    1,
    M.zeropage_x:  1,
    M.zeropage_y:  1,
}


class Cpu6502Visitor(object):
    def _visit_no_args(self, op, pos, *args):
        return Op(pos, op)

    def _visit_one_arg(self, op, pos, opname, arg):
        return Op(pos, op, arg)


# grammar for 6502 opcodes
grammar = ''

# flag for import-time initializaiton
__setup_complete = False

# amend the module by dynamically building the grammar and parser base class
if not __setup_complete:
    op_names = []
    grammar_parts = []
    for op in opcode_table:
        expr = f'op_{op.name}_{op.mode.name}'
        seq = ' _ '.join([f'"{op.name}"'] + addressmode_params[op.mode])
        op_names.append(expr)
        grammar_parts.append(f'{expr} = {seq}')
        if addressmode_args[op.mode]:
            visit_name = '_visit_one_arg'
        else:
            visit_name = '_visit_no_args'
        fn = partialmethod(getattr(Cpu6502Visitor, visit_name), op)
        setattr(Cpu6502Visitor, f'visit_{expr}', fn)
    grammar_parts.append('oper = ' + ' / '.join(op_names))
    grammar = '\n'.join(grammar_parts)
