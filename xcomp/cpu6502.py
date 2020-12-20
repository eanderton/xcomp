# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

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

# 8 bit mods that have a 16 bit equivalent
addressmode_8to16 = {
    AddressMode.absolute:   AddressMode.absolute,
    AddressMode.absolute_x: AddressMode.absolute_x,
    AddressMode.absolute_y: AddressMode.absolute_y,
    AddressMode.indirect:   AddressMode.indirect,
    AddressMode.relative:   AddressMode.relative,  # special case
    AddressMode.zeropage:   AddressMode.absolute,
    AddressMode.zeropage_x: AddressMode.absolute_x,
    AddressMode.zeropage_y: AddressMode.absolute_y,
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


opcode_xref = {
    "adc": {
        AddressMode.immediate  : 0x69,
        AddressMode.zeropage   : 0x65,
        AddressMode.zeropage_x : 0x75,
        AddressMode.absolute   : 0x6d,
        AddressMode.absolute_x : 0x7d,
        AddressMode.absolute_y : 0x79,
        AddressMode.indirect_x : 0x61,
        AddressMode.indirect_y : 0x71,
    },
    "and": {
        AddressMode.immediate  : 0x29,
        AddressMode.zeropage   : 0x25,
        AddressMode.zeropage_x : 0x35,
        AddressMode.absolute   : 0x2d,
        AddressMode.absolute_x : 0x3d,
        AddressMode.absolute_y : 0x39,
        AddressMode.indirect_x : 0x21,
        AddressMode.indirect_y : 0x31,
    },
    "asl": {
        AddressMode.accumulator: 0x0a,
        AddressMode.zeropage   : 0x06,
        AddressMode.zeropage_x : 0x16,
        AddressMode.absolute   : 0x0e,
        AddressMode.absolute_x : 0x1e,
    },
    "bcc": {
        AddressMode.relative   : 0x90,
    },
    "bcs": {
        AddressMode.relative   : 0xb0,
    },
    "beq": {
        AddressMode.relative   : 0xf0,
    },
    "bit": {
        AddressMode.zeropage   : 0x24,
        AddressMode.absolute   : 0x2c,
    },
    "bmi": {
        AddressMode.relative   : 0x30,
    },
    "bne": {
        AddressMode.relative   : 0xd0,
    },
    "bpl": {
        AddressMode.relative   : 0x10,
    },
    "brk": {
        AddressMode.implied    : 0x00,
    },
    "bvc": {
        AddressMode.relative   : 0x70,
    },
    "clc": {
        AddressMode.implied    : 0x18,
    },
    "cld": {
        AddressMode.implied    : 0xd8,
    },
    "cli": {
        AddressMode.implied    : 0x58,
    },
    "clv": {
        AddressMode.implied    : 0xb8,
    },
    "cmp": {
        AddressMode.immediate  : 0xc9,
        AddressMode.zeropage   : 0xc5,
        AddressMode.zeropage_x : 0xd5,
        AddressMode.absolute   : 0xcd,
        AddressMode.absolute_x : 0xdd,
        AddressMode.absolute_y : 0xd9,
        AddressMode.indirect_x : 0xc1,
        AddressMode.indirect_y : 0xd1,
    },
    "cpx": {
        AddressMode.immediate  : 0xe0,
        AddressMode.zeropage   : 0xe4,
        AddressMode.absolute   : 0xec,
    },
    "cpy": {
        AddressMode.immediate  : 0xc0,
        AddressMode.zeropage   : 0xc4,
        AddressMode.absolute   : 0xcc,
    },
    "dec": {
        AddressMode.zeropage   : 0xc6,
        AddressMode.zeropage_x : 0xd6,
        AddressMode.absolute   : 0xce,
        AddressMode.absolute_x : 0xde,
        AddressMode.implied    : 0x88,
    },
    "dex": {
        AddressMode.implied    : 0xca,
    },
    "dey": {
        AddressMode.implied    : 0x88,
    },
    "eor": {
        AddressMode.immediate  : 0x49,
        AddressMode.zeropage   : 0x45,
        AddressMode.zeropage_x : 0x55,
        AddressMode.absolute   : 0x4d,
        AddressMode.absolute_x : 0x5d,
        AddressMode.absolute_y : 0x59,
        AddressMode.indirect_x : 0x41,
        AddressMode.indirect_y : 0x51,
    },
    "inc": {
        AddressMode.zeropage   : 0xe6,
        AddressMode.zeropage_x : 0xf6,
        AddressMode.absolute   : 0xee,
        AddressMode.absolute_x : 0xfe,
    },
    "inx": {
        AddressMode.implied    : 0xe8,
    },
    "iny": {
        AddressMode.implied    : 0xc8,
    },
    "jmp": {
        AddressMode.absolute   : 0x4c,
        AddressMode.indirect   : 0x6c,
    },
    "jsr": {
        AddressMode.absolute   : 0x20,
    },
    "lda": {
        AddressMode.immediate  : 0xa9,
        AddressMode.zeropage   : 0xa5,
        AddressMode.zeropage_x : 0xb5,
        AddressMode.absolute   : 0xad,
        AddressMode.absolute_x : 0xbd,
        AddressMode.absolute_y : 0xb9,
        AddressMode.indirect_x : 0xa1,
        AddressMode.indirect_y : 0xb1,
    },
    "ldx": {
        AddressMode.immediate  : 0xa2,
        AddressMode.zeropage   : 0xa6,
        AddressMode.zeropage_y : 0xb6,
        AddressMode.absolute   : 0xae,
        AddressMode.absolute_y : 0xbe,
    },
    "ldy": {
        AddressMode.immediate  : 0xa0,
        AddressMode.zeropage   : 0xa4,
        AddressMode.zeropage_x : 0xb4,
        AddressMode.absolute   : 0xac,
        AddressMode.absolute_x : 0xbc,
    },
    "lsr": {
        AddressMode.accumulator: 0x4a,
        AddressMode.zeropage   : 0x46,
        AddressMode.zeropage_x : 0x56,
        AddressMode.absolute   : 0x4e,
        AddressMode.absolute_x : 0x5e,
    },
    "nop": {
        AddressMode.implied    : 0xea,
    },
    "ora": {
        AddressMode.immediate  : 0x09,
        AddressMode.zeropage   : 0x05,
        AddressMode.zeropage_x : 0x15,
        AddressMode.absolute   : 0x0d,
        AddressMode.absolute_x : 0x1d,
        AddressMode.absolute_y : 0x19,
        AddressMode.indirect_x : 0x01,
        AddressMode.indirect_y : 0x11,
    },
    "pha": {
        AddressMode.implied    : 0x48,
    },
    "php": {
        AddressMode.implied    : 0x08,
    },
    "pla": {
        AddressMode.implied    : 0x68,
    },
    "plp": {
        AddressMode.implied    : 0x28,
    },
    "rol": {
        AddressMode.accumulator: 0x2a,
        AddressMode.zeropage   : 0x26,
        AddressMode.zeropage_x : 0x36,
        AddressMode.absolute   : 0x2e,
        AddressMode.absolute_x : 0x3e,
    },
    "ror": {
        AddressMode.accumulator: 0x6a,
        AddressMode.zeropage   : 0x66,
        AddressMode.zeropage_x : 0x76,
        AddressMode.absolute   : 0x6e,
        AddressMode.absolute_x : 0x7e,
    },
    "rti": {
        AddressMode.implied    : 0x40,
    },
    "rts": {
        AddressMode.implied    : 0x60,
    },
    "sbc": {
        AddressMode.immediate  : 0xe9,
        AddressMode.zeropage   : 0xe5,
        AddressMode.zeropage_x : 0xf5,
        AddressMode.absolute   : 0xed,
        AddressMode.absolute_x : 0xfd,
        AddressMode.absolute_y : 0xf9,
        AddressMode.indirect_x : 0xe1,
        AddressMode.indirect_y : 0xf1,
    },
    "sec": {
        AddressMode.implied    : 0x38,
    },
    "sed": {
        AddressMode.implied    : 0xf8,
    },
    "sei": {
        AddressMode.implied    : 0x78,
    },
    "sta": {
        AddressMode.zeropage   : 0x85,
        AddressMode.zeropage_x : 0x95,
        AddressMode.absolute   : 0x8d,
        AddressMode.absolute_x : 0x9d,
        AddressMode.absolute_y : 0x99,
        AddressMode.indirect_x : 0x81,
        AddressMode.indirect_y : 0x91,
    },
    "stx": {
        AddressMode.zeropage   : 0x86,
        AddressMode.zeropage_y : 0x96,
        AddressMode.absolute   : 0x8e,
    },
    "sty": {
        AddressMode.zeropage   : 0x84,
        AddressMode.zeropage_x : 0x94,
        AddressMode.absolute   : 0x8c,
    },
    "tax": {
        AddressMode.implied    : 0xaa,
    },
    "tay": {
        AddressMode.implied    : 0xa8,
    },
    "tsx": {
        AddressMode.implied    : 0xba,
    },
    "txa": {
        AddressMode.implied    : 0x8a,
    },
    "txs": {
        AddressMode.implied    : 0x9a,
    },
    "tya": {
        AddressMode.implied    : 0x98,
    },
}

opcodes = {
        0x69: ("adc", AddressMode.immediate),
        0x65: ("adc", AddressMode.zeropage),
        0x75: ("adc", AddressMode.zeropage_x),
        0x6d: ("adc", AddressMode.absolute),
        0x7d: ("adc", AddressMode.absolute_x),
        0x79: ("adc", AddressMode.absolute_y),
        0x61: ("adc", AddressMode.indirect_x),
        0x71: ("adc", AddressMode.indirect_y),
        0x29: ("and", AddressMode.immediate),
        0x25: ("and", AddressMode.zeropage),
        0x35: ("and", AddressMode.zeropage_x),
        0x2d: ("and", AddressMode.absolute),
        0x3d: ("and", AddressMode.absolute_x),
        0x39: ("and", AddressMode.absolute_y),
        0x21: ("and", AddressMode.indirect_x),
        0x31: ("and", AddressMode.indirect_y),
        0x0a: ("asl", AddressMode.accumulator),
        0x06: ("asl", AddressMode.zeropage),
        0x16: ("asl", AddressMode.zeropage_x),
        0x0e: ("asl", AddressMode.absolute),
        0x1e: ("asl", AddressMode.absolute_x),
        0x90: ("bcc", AddressMode.relative),
        0xb0: ("bcs", AddressMode.relative),
        0xf0: ("beq", AddressMode.relative),
        0x24: ("bit", AddressMode.zeropage),
        0x2c: ("bit", AddressMode.absolute),
        0x30: ("bmi", AddressMode.relative),
        0xd0: ("bne", AddressMode.relative),
        0x10: ("bpl", AddressMode.relative),
        0x00: ("brk", AddressMode.implied),
        0x70: ("bvc", AddressMode.relative),
        0x18: ("clc", AddressMode.implied),
        0xd8: ("cld", AddressMode.implied),
        0x58: ("cli", AddressMode.implied),
        0xb8: ("clv", AddressMode.implied),
        0xc9: ("cmp", AddressMode.immediate),
        0xc5: ("cmp", AddressMode.zeropage),
        0xd5: ("cmp", AddressMode.zeropage_x),
        0xcd: ("cmp", AddressMode.absolute),
        0xdd: ("cmp", AddressMode.absolute_x),
        0xd9: ("cmp", AddressMode.absolute_y),
        0xc1: ("cmp", AddressMode.indirect_x),
        0xd1: ("cmp", AddressMode.indirect_y),
        0xe0: ("cpx", AddressMode.immediate),
        0xe4: ("cpx", AddressMode.zeropage),
        0xec: ("cpx", AddressMode.absolute),
        0xc0: ("cpy", AddressMode.immediate),
        0xc4: ("cpy", AddressMode.zeropage),
        0xcc: ("cpy", AddressMode.absolute),
        0xc6: ("dec", AddressMode.zeropage),
        0xd6: ("dec", AddressMode.zeropage_x),
        0xce: ("dec", AddressMode.absolute),
        0xde: ("dec", AddressMode.absolute_x),
        0x88: ("dec", AddressMode.implied),
        0xca: ("dex", AddressMode.implied),
        0x88: ("dey", AddressMode.implied),
        0x49: ("eor", AddressMode.immediate),
        0x45: ("eor", AddressMode.zeropage),
        0x55: ("eor", AddressMode.zeropage_x),
        0x4d: ("eor", AddressMode.absolute),
        0x5d: ("eor", AddressMode.absolute_x),
        0x59: ("eor", AddressMode.absolute_y),
        0x41: ("eor", AddressMode.indirect_x),
        0x51: ("eor", AddressMode.indirect_y),
        0xe6: ("inc", AddressMode.zeropage),
        0xf6: ("inc", AddressMode.zeropage_x),
        0xee: ("inc", AddressMode.absolute),
        0xfe: ("inc", AddressMode.absolute_x),
        0xe8: ("inx", AddressMode.implied),
        0xc8: ("iny", AddressMode.implied),
        0x4c: ("jmp", AddressMode.absolute),
        0x6c: ("jmp", AddressMode.indirect),
        0x20: ("jsr", AddressMode.absolute),
        0xa9: ("lda", AddressMode.immediate),
        0xa5: ("lda", AddressMode.zeropage),
        0xb5: ("lda", AddressMode.zeropage_x),
        0xad: ("lda", AddressMode.absolute),
        0xbd: ("lda", AddressMode.absolute_x),
        0xb9: ("lda", AddressMode.absolute_y),
        0xa1: ("lda", AddressMode.indirect_x),
        0xb1: ("lda", AddressMode.indirect_y),
        0xa2: ("ldx", AddressMode.immediate),
        0xa6: ("ldx", AddressMode.zeropage),
        0xb6: ("ldx", AddressMode.zeropage_y),
        0xae: ("ldx", AddressMode.absolute),
        0xbe: ("ldx", AddressMode.absolute_y),
        0xa0: ("ldy", AddressMode.immediate),
        0xa4: ("ldy", AddressMode.zeropage),
        0xb4: ("ldy", AddressMode.zeropage_x),
        0xac: ("ldy", AddressMode.absolute),
        0xbc: ("ldy", AddressMode.absolute_x),
        0x4a: ("lsr", AddressMode.accumulator),
        0x46: ("lsr", AddressMode.zeropage),
        0x56: ("lsr", AddressMode.zeropage_x),
        0x4e: ("lsr", AddressMode.absolute),
        0x5e: ("lsr", AddressMode.absolute_x),
        0xea: ("nop", AddressMode.implied),
        0x09: ("ora", AddressMode.immediate),
        0x05: ("ora", AddressMode.zeropage),
        0x15: ("ora", AddressMode.zeropage_x),
        0x0d: ("ora", AddressMode.absolute),
        0x1d: ("ora", AddressMode.absolute_x),
        0x19: ("ora", AddressMode.absolute_y),
        0x01: ("ora", AddressMode.indirect_x),
        0x11: ("ora", AddressMode.indirect_y),
        0x48: ("pha", AddressMode.implied),
        0x08: ("php", AddressMode.implied),
        0x68: ("pla", AddressMode.implied),
        0x28: ("plp", AddressMode.implied),
        0x2a: ("rol", AddressMode.accumulator),
        0x26: ("rol", AddressMode.zeropage),
        0x36: ("rol", AddressMode.zeropage_x),
        0x2e: ("rol", AddressMode.absolute),
        0x3e: ("rol", AddressMode.absolute_x),
        0x6a: ("ror", AddressMode.accumulator),
        0x66: ("ror", AddressMode.zeropage),
        0x76: ("ror", AddressMode.zeropage_x),
        0x6e: ("ror", AddressMode.absolute),
        0x7e: ("ror", AddressMode.absolute_x),
        0x40: ("rti", AddressMode.implied),
        0x60: ("rts", AddressMode.implied),
        0xe9: ("sbc", AddressMode.immediate),
        0xe5: ("sbc", AddressMode.zeropage),
        0xf5: ("sbc", AddressMode.zeropage_x),
        0xed: ("sbc", AddressMode.absolute),
        0xfd: ("sbc", AddressMode.absolute_x),
        0xf9: ("sbc", AddressMode.absolute_y),
        0xe1: ("sbc", AddressMode.indirect_x),
        0xf1: ("sbc", AddressMode.indirect_y),
        0x38: ("sec", AddressMode.implied),
        0xf8: ("sed", AddressMode.implied),
        0x78: ("sei", AddressMode.implied),
        0x85: ("sta", AddressMode.zeropage),
        0x95: ("sta", AddressMode.zeropage_x),
        0x8d: ("sta", AddressMode.absolute),
        0x9d: ("sta", AddressMode.absolute_x),
        0x99: ("sta", AddressMode.absolute_y),
        0x81: ("sta", AddressMode.indirect_x),
        0x91: ("sta", AddressMode.indirect_y),
        0x86: ("stx", AddressMode.zeropage),
        0x96: ("stx", AddressMode.zeropage_y),
        0x8e: ("stx", AddressMode.absolute),
        0x84: ("sty", AddressMode.zeropage),
        0x94: ("sty", AddressMode.zeropage_x),
        0x8c: ("sty", AddressMode.absolute),
        0xaa: ("tax", AddressMode.implied),
        0xa8: ("tay", AddressMode.implied),
        0xba: ("tsx", AddressMode.implied),
        0x8a: ("txa", AddressMode.implied),
        0x9a: ("txs", AddressMode.implied),
        0x98: ("tya", AddressMode.implied),
}

