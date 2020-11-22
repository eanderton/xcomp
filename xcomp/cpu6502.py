"""
Abstraction of the 6502 processor CPU opcodes.
"""

from attr import attrib, attrs, Factory
from typing import *
from functools import partialmethod
from enum import Enum, auto

class AddressMode(Enum):
    accumulator = auto()
    absolute = auto()
    absolute_x = auto()
    absolute_y = auto()
    immediate = auto()
    implied = auto()
    indirect = auto()
    indirect_x = auto()
    indirect_y = auto()
    relative = auto()
    zeropage = auto()
    zeropage_x = auto()
    zeropage_y = auto()
    unknown = auto()

# grammar parameter specs by addressing mode
addressmode_params = {
    AddressMode.accumulator: ['"a"'],
    AddressMode.absolute:    ['expr16'],
    AddressMode.absolute_x:  ['expr16', 'comma', '"x"'],
    AddressMode.absolute_y:  ['expr16', 'comma', '"y"'],
    AddressMode.immediate:   ['hash', 'expr8'],
    AddressMode.implied:     [],
    AddressMode.indirect:    ['lparen', 'expr16', 'rparen'],
    AddressMode.indirect_x:  ['lparen', 'expr8', 'comma', '"x"', 'rparen'],
    AddressMode.indirect_y:  ['lparen', 'expr8', 'rparen', 'comma', '"y"'],
    AddressMode.relative:    ['expr8'],
    AddressMode.zeropage:    ['expr8'],
    AddressMode.zeropage_x:  ['expr8', 'comma', '"x"'],
    AddressMode.zeropage_y:  ['expr8', 'comma', '"y"'],
}

addressmode_args = {
    AddressMode.accumulator: 0,
    AddressMode.absolute:    1,
    AddressMode.absolute_x:  1,
    AddressMode.absolute_y:  1,
    AddressMode.immediate:   1,
    AddressMode.implied:     0,
    AddressMode.indirect:    1,
    AddressMode.indirect_x:  1,
    AddressMode.indirect_y:  1,
    AddressMode.relative:    1,
    AddressMode.zeropage:    1,
    AddressMode.zeropage_x:  1,
    AddressMode.zeropage_y:  1,
}

addressmode_arg_width = {
    AddressMode.accumulator: 0,
    AddressMode.absolute:    2,
    AddressMode.absolute_x:  2,
    AddressMode.absolute_y:  2,
    AddressMode.immediate:   1,
    AddressMode.implied:     0,
    AddressMode.indirect:    2,
    AddressMode.indirect_x:  1,
    AddressMode.indirect_y:  1,
    AddressMode.relative:    1,
    AddressMode.zeropage:    1,
    AddressMode.zeropage_x:  1,
    AddressMode.zeropage_y:  1,
}

opcode_templates = {
    AddressMode.accumulator: 'A',
    AddressMode.absolute:    '{arg16}',
    AddressMode.absolute_x:  '{arg16}, X',
    AddressMode.absolute_y:  '{arg16}, Y',
    AddressMode.immediate:   '#{arg8}',
    AddressMode.implied:     '',
    AddressMode.indirect:    '({arg16})',
    AddressMode.indirect_x:  '({arg8}, X)',
    AddressMode.indirect_y:  '({arg8}), Y',
    AddressMode.relative:    '{arg8}',
    AddressMode.zeropage:    '{arg8}',
    AddressMode.zeropage_x:  '{arg8}, X',
    AddressMode.zeropage_y:  '{arg8}, Y',
}


@attrs(auto_attribs=True)
class OpCode(object):
    name: str
    mode: AddressMode
    value: int

    @property
    def arg_width(self):
        return addressmode_arg_width[self.mode]

opcode_table = (
    OpCode("adc", AddressMode.immediate,   0x69),
    OpCode("adc", AddressMode.zeropage,    0x65),
    OpCode("adc", AddressMode.zeropage_x,  0x75),
    OpCode("adc", AddressMode.absolute,    0x6D),
    OpCode("adc", AddressMode.absolute_x,  0x7D),
    OpCode("adc", AddressMode.absolute_y,  0x79),
    OpCode("adc", AddressMode.indirect_x,  0x61),
    OpCode("adc", AddressMode.indirect_y,  0x71),
    OpCode("and", AddressMode.immediate,   0x29),
    OpCode("and", AddressMode.zeropage,    0x25),
    OpCode("and", AddressMode.zeropage_x,  0x35),
    OpCode("and", AddressMode.absolute,    0x2D),
    OpCode("and", AddressMode.absolute_x,  0x3D),
    OpCode("and", AddressMode.absolute_y,  0x39),
    OpCode("and", AddressMode.indirect_x,  0x21),
    OpCode("and", AddressMode.indirect_y,  0x31),
    OpCode("asl", AddressMode.accumulator, 0x0A),
    OpCode("asl", AddressMode.zeropage,    0x06),
    OpCode("asl", AddressMode.zeropage_x,  0x16),
    OpCode("asl", AddressMode.absolute,    0x0E),
    OpCode("asl", AddressMode.absolute_x,  0x1E),
    OpCode("bcc", AddressMode.relative,    0x90),
    OpCode("bcs", AddressMode.relative,    0xB0),
    OpCode("beq", AddressMode.relative,    0xF0),
    OpCode("bit", AddressMode.zeropage,    0x24),
    OpCode("bit", AddressMode.absolute,    0x2C),
    OpCode("bmi", AddressMode.relative,    0x30),
    OpCode("bne", AddressMode.relative,    0xD0),
    OpCode("bpl", AddressMode.relative,    0x10),
    OpCode("brk", AddressMode.implied,     0x00),
    OpCode("bvc", AddressMode.relative,    0x50),
    OpCode("bvc", AddressMode.relative,    0x70),
    OpCode("clc", AddressMode.implied,     0x18),
    OpCode("cld", AddressMode.implied,     0xD8),
    OpCode("cli", AddressMode.implied,     0x58),
    OpCode("clv", AddressMode.implied,     0xB8),
    OpCode("cmp", AddressMode.immediate,   0xC9),
    OpCode("cmp", AddressMode.zeropage,    0xC5),
    OpCode("cmp", AddressMode.zeropage_x,  0xD5),
    OpCode("cmp", AddressMode.absolute,    0xCD),
    OpCode("cmp", AddressMode.absolute_x,  0xDD),
    OpCode("cmp", AddressMode.absolute_y,  0xD9),
    OpCode("cmp", AddressMode.indirect_x,  0xC1),
    OpCode("cmp", AddressMode.indirect_y,  0xD1),
    OpCode("cpx", AddressMode.immediate,   0xE0),
    OpCode("cpx", AddressMode.zeropage,    0xE4),
    OpCode("cpx", AddressMode.absolute,    0xEC),
    OpCode("cpy", AddressMode.immediate,   0xC0),
    OpCode("cpy", AddressMode.zeropage,    0xC4),
    OpCode("cpy", AddressMode.absolute,    0xCC),
    OpCode("dec", AddressMode.zeropage,    0xC6),
    OpCode("dec", AddressMode.zeropage_x,  0xD6),
    OpCode("dec", AddressMode.absolute,    0xCE),
    OpCode("dec", AddressMode.absolute_x,  0xDE),
    OpCode("dec", AddressMode.implied,     0xCA),
    OpCode("dec", AddressMode.implied,     0x88),
    OpCode("eor", AddressMode.immediate,   0x49),
    OpCode("eor", AddressMode.zeropage,    0x45),
    OpCode("eor", AddressMode.zeropage_x,  0x55),
    OpCode("eor", AddressMode.absolute,    0x4D),
    OpCode("eor", AddressMode.absolute_x,  0x5D),
    OpCode("eor", AddressMode.absolute_y,  0x59),
    OpCode("eor", AddressMode.indirect_x,  0x41),
    OpCode("eor", AddressMode.indirect_y,  0x51),
    OpCode("inc", AddressMode.zeropage,    0xE6),
    OpCode("inc", AddressMode.zeropage_x,  0xF6),
    OpCode("inc", AddressMode.absolute,    0xEE),
    OpCode("inc", AddressMode.absolute_x,  0xFE),
    OpCode("inx", AddressMode.implied,     0xE8),
    OpCode("iny", AddressMode.implied,     0xC8),
    OpCode("jmp", AddressMode.absolute,    0x4C),
    OpCode("jmp", AddressMode.indirect,    0x6C),
    OpCode("jsr", AddressMode.absolute,    0x20),
    OpCode("lda", AddressMode.immediate,   0xA9),
    OpCode("lda", AddressMode.zeropage,    0xA5),
    OpCode("lda", AddressMode.zeropage_x,  0xB5),
    OpCode("lda", AddressMode.absolute,    0xAD),
    OpCode("lda", AddressMode.absolute_x,  0xBD),
    OpCode("lda", AddressMode.absolute_y,  0xB9),
    OpCode("lda", AddressMode.indirect_x,  0xA1),
    OpCode("lda", AddressMode.indirect_y,  0xB1),
    OpCode("ldx", AddressMode.immediate,   0xA2),
    OpCode("ldx", AddressMode.zeropage,    0xA6),
    OpCode("ldx", AddressMode.zeropage_y,  0xB6),
    OpCode("ldx", AddressMode.absolute,    0xAE),
    OpCode("ldx", AddressMode.absolute_y,  0xBE),
    OpCode("ldy", AddressMode.immediate,   0xA0),
    OpCode("ldy", AddressMode.zeropage,    0xA4),
    OpCode("ldy", AddressMode.zeropage_x,  0xB4),
    OpCode("ldy", AddressMode.absolute,    0xAC),
    OpCode("ldy", AddressMode.absolute_x,  0xBC),
    OpCode("lsr", AddressMode.accumulator, 0x4A),
    OpCode("lsr", AddressMode.zeropage,    0x46),
    OpCode("lsr", AddressMode.zeropage_x,  0x56),
    OpCode("lsr", AddressMode.absolute,    0x4E),
    OpCode("lsr", AddressMode.absolute_x,  0x5E),
    OpCode("nop", AddressMode.implied,     0xEA),
    OpCode("ora", AddressMode.immediate,   0x09),
    OpCode("ora", AddressMode.zeropage,    0x05),
    OpCode("ora", AddressMode.zeropage_x,  0x15),
    OpCode("ora", AddressMode.absolute,    0x0D),
    OpCode("ora", AddressMode.absolute_x,  0x1D),
    OpCode("ora", AddressMode.absolute_y,  0x19),
    OpCode("ora", AddressMode.indirect_x,  0x01),
    OpCode("ora", AddressMode.indirect_y,  0x11),
    OpCode("pha", AddressMode.implied,     0x48),
    OpCode("php", AddressMode.implied,     0x08),
    OpCode("pla", AddressMode.implied,     0x68),
    OpCode("plp", AddressMode.implied,     0x28),
    OpCode("rol", AddressMode.accumulator, 0x2A),
    OpCode("rol", AddressMode.zeropage,    0x26),
    OpCode("rol", AddressMode.zeropage_x,  0x36),
    OpCode("rol", AddressMode.absolute,    0x2E),
    OpCode("rol", AddressMode.absolute_x,  0x3E),
    OpCode("ror", AddressMode.accumulator, 0x6A),
    OpCode("ror", AddressMode.zeropage,    0x66),
    OpCode("ror", AddressMode.zeropage_x,  0x76),
    OpCode("ror", AddressMode.absolute,    0x6E),
    OpCode("ror", AddressMode.absolute_x,  0x7E),
    OpCode("rti", AddressMode.implied,     0x40),
    OpCode("rts", AddressMode.implied,     0x60),
    OpCode("sbc", AddressMode.immediate,   0xE9),
    OpCode("sbc", AddressMode.zeropage,    0xE5),
    OpCode("sbc", AddressMode.zeropage_x,  0xF5),
    OpCode("sbc", AddressMode.absolute,    0xED),
    OpCode("sbc", AddressMode.absolute_x,  0xFD),
    OpCode("sbc", AddressMode.absolute_y,  0xF9),
    OpCode("sbc", AddressMode.indirect_x,  0xE1),
    OpCode("sbc", AddressMode.indirect_y,  0xF1),
    OpCode("sec", AddressMode.implied,     0x38),
    OpCode("sed", AddressMode.implied,     0xF8),
    OpCode("sei", AddressMode.implied,     0x78),
    OpCode("sta", AddressMode.zeropage,    0x85),
    OpCode("sta", AddressMode.zeropage_x,  0x95),
    OpCode("sta", AddressMode.absolute,    0x8D),
    OpCode("sta", AddressMode.absolute_x,  0x9D),
    OpCode("sta", AddressMode.absolute_y,  0x99),
    OpCode("sta", AddressMode.indirect_x,  0x81),
    OpCode("sta", AddressMode.indirect_y,  0x91),
    OpCode("stx", AddressMode.zeropage,    0x86),
    OpCode("stx", AddressMode.zeropage_y,  0x96),
    OpCode("stx", AddressMode.absolute,    0x8E),
    OpCode("sty", AddressMode.zeropage,    0x84),
    OpCode("sty", AddressMode.zeropage_x,  0x94),
    OpCode("sty", AddressMode.absolute,    0x8C),
    OpCode("tax", AddressMode.implied,     0xAA),
    OpCode("tay", AddressMode.implied,     0xA8),
    OpCode("tsx", AddressMode.implied,     0xBA),
    OpCode("txa", AddressMode.implied,     0x8A),
    OpCode("txs", AddressMode.implied,     0x9A),
    OpCode("tya", AddressMode.implied,     0x98),
)

# opcodes by name and addressing mode
opcode_xref = {}
for op in opcode_table:
    opcode_xref.setdefault(op.name, {})[op.mode] = op

# opcodes by machinecode
opcode_disasm = {x.value: x for x in opcode_table}


