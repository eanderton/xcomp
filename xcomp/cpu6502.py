
from xcomp.model import OpCode
from xcomp.model import AddressMode as M

opcode_table = {
    'adc': (
        (
    )

    }

"""
     "and", "M.immediate",   0x29
     "and", "M.zeropage",    0x25
     "and", "M.zeropage_x",  0x35
     "and", "M.absolute",    0x2D
     "and", "M.absolute_x",  0x3D
     "and", "M.absolute_y",  0x39
     "and", "M.indirect_x",  0x21
     "and", "M.indirect_y",  0x31

     "asl", "M.accumulator", 0x0A
     "asl", "M.zeropage",    0x06
     "asl", "M.zeropage_x",  0x16
     "asl", "M.absolute",    0x0E
     "asl", "M.absolute_x",  0x1E

     "bcc", "M.relative",    0x90


     "bcs", "M.relative",    0xB0


     "beq", "M.relative",    0xF0


     "bit", "M.zeropage",    0x24
     "bit", "M.absolute",    0x2C


     "bmi", "M.relative",    0x30


     "bne", "M.relative",    0xD0


     "bpl", "M.relative",    0x10


     "brk", "M.implied",     0x00

     "bvc", "M.relative",    0x50


     "bvc", "M.relative",    0x70


     "clc", "M.implied",     0x18


     "cld", "M.implied",     0xD8


     "cli", "M.implied",     0x58


     "clv", "M.implied",     0xB8


     "cmp", "M.immediate",   0xC9
     "cmp", "M.zeropage",    0xC5
     "cmp", "M.zeropage_x",  0xD5
     "cmp", "M.absolute",    0xCD
     "cmp", "M.absolute_x",  0xDD
     "cmp", "M.absolute_y",  0xD9
     "cmp", "M.indirect_x",  0xC1
     "cmp", "M.indirect_y",  0xD1


     "cpx", "M.immediate",   0xE0
     "cpx", "M.zeropage",    0xE4
     "cpx", "M.absolute",    0xEC


     "cpy", "M.immediate",   0xC0
     "cpy", "M.zeropage",    0xC4
     "cpy", "M.absolute",    0xCC


     "dec", "M.zeropage",    0xC6
     "dec", "M.zeropage_x",  0xD6
     "dec", "M.absolute",    0xCE
     "dec", "M.absolute_x",  0xDE

     "dec", "M.implied",     0xCA


     "dec", "M.implied",     0x88

     "eor", "M.immediate",   0x49
     "eor", "M.zeropage",    0x45
     "eor", "M.zeropage_x",  0x55
     "eor", "M.absolute",    0x4D
     "eor", "M.absolute_x",  0x5D
     "eor", "M.absolute_y",  0x59
     "eor", "M.indirect_x",  0x41
     "eor", "M.indirect_y",  0x51

     "inc", "M.zeropage",    0xE6
     "inc", "M.zeropage_x",  0xF6
     "inc", "M.absolute",    0xEE
     "inc", "M.absolute_x",  0xFE

     "inx", "M.implied",     0xE8


     "iny", "M.implied",     0xC8


     "jmp", "M.absolute",    0x4C
     "jmp", "M.indirect"     0x6C

     "jsr", "M.absolute",    0x20


     "lda", "M.immediate",   0xA9
     "lda", "M.zeropage",    0xA5
     "lda", "M.zeropage_x",  0xB5
     "lda", "M.absolute",    0xAD
     "lda", "M.absolute_x",  0xBD
     "lda", "M.absolute_y",  0xB9
     "lda", "M.indirect_x",  0xA1
     "lda", "M.indirect_y",  0xB1


     "ldx", "M.immediate",   0xA2
     "ldx", "M.zeropage",    0xA6
     "ldx", "M.zeropage_y",  0xB6
     "ldx", "M.absolute",    0xAE
     "ldx", "M.absolute_y",  0xBE


     "ldy", "M.immediate",   0xA0
     "ldy", "M.zeropage",    0xA4
     "ldy", "M.zeropage_x",  0xB4
     "ldy", "M.absolute",    0xAC
     "ldy", "M.absolute_x",  0xBC


     "lsr", "M.accumulator", 0x4A
     "lsr", "M.zeropage",    0x46
     "lsr", "M.zeropage_x",  0x56
     "lsr", "M.absolute",    0x4E
     "lsr", "M.absolute_x",  0x5E

     "nop", "M.implied",     0xEA


     "ora", "M.immediate",   0x09
     "ora", "M.zeropage",    0x05
     "ora", "M.zeropage_x",  0x15
     "ora", "M.absolute",    0x0D
     "ora", "M.absolute_x",  0x1D
     "ora", "M.absolute_y",  0x19
     "ora", "M.indirect_x",  0x01
     "ora", "M.indirect_y",  0x11


     "pha", "M.implied",     0x48


     "php", "M.implied",     0x08

     "pla", "M.implied",     0x68


     "plp", "M.implied",     0x28

     "rol", "M.accumulator", 0x2A
     "rol", "M.zeropage",    0x26
     "rol", "M.zeropage_x",  0x36
     "rol", "M.absolute",    0x2E
     "rol", "M.absolute_x",  0x3E


     "ror", "M.accumulator", 0x6A
     "ror", "M.zeropage",    0x66
     "ror", "M.zeropage_x",  0x76
     "ror", "M.absolute",    0x6E
     "ror", "M.absolute_x",  0x7E

     "rti", "M.implied",     0x40


     "rts", "M.implied",     0x60


     "sbc", "M.immediate",   0xE9
     "sbc", "M.zeropage",    0xE5
     "sbc", "M.zeropage_x",  0xF5
     "sbc", "M.absolute",    0xED
     "sbc", "M.absolute_x",  0xFD
     "sbc", "M.absolute_y",  0xF9
     "sbc", "M.indirect_x",  0xE1
     "sbc", "M.indirect_y",  0xF1


     "sec", "M.implied",     0x38


     "sed", "M.implied",     0xF8


     "sei", "M.implied",     0x78


     "sta", "M.zeropage",    0x85
     "sta", "M.zeropage_x",  0x95
     "sta", "M.absolute",    0x8D
     "sta", "M.absolute_x",  0x9D
     "sta", "M.absolute_y",  0x99
     "sta", "M.indirect_x",  0x81
     "sta", "M.indirect_y",  0x91


     "stx", "M.zeropage",    0x86
     "stx", "M.zeropage_y",  0x96
     "stx", "M.absolute",    0x8E


     "sty", "M.zeropage",    0x84
     "sty", "M.zeropage_x",  0x94
     "sty", "M.absolute",    0x8C


     "tax", "M.implied",     0xAA


     "tay", "M.implied",     0xA8


     "tsx", "M.implied",     0xBA

     "txa", "M.implied",     0x8A

     "txs", "M.implied",     0x9A

     "tya", "M.implied",     0x98

"""
