;
; C64 VIC-II memory map and related constants
;

.struct vic2 $D000
    .def sprite0_bit 0x01
    .def sprite1_bit 0x02
    .def sprite2_bit 0x04
    .def sprite3_bit 0x08
    .def sprite4_bit 0x10
    .def sprite5_bit 0x20
    .def sprite6_bit 0x40
    .def sprite7_bit 0x80

    ; sprite x/y coordinates
    .var m0x byte
    .var m0y byte
    .var m1x byte
    .var m1y byte
    .var m2x byte
    .var m2y byte
    .var m3x byte
    .var m3y byte
    .var m4x byte
    .var m4y byte
    .var m5x byte
    .var m5y byte
    .var m6x byte
    .var m6y byte
    .var m7x byte
    .var m7y byte

    .var msbx byte  ; MSB of x coordinates
    .var cr1 byte   ; control register 1

    .def cr1.rst8 $80
    .def cr1.ecm $40
    .def cr1.bmm $20
    .def cr1.den $10
    .def cr1.rsel $08
    .def cr1.yscroll $07

    .var rst byte   ; raster counter
    .var lpx byte   ; light pen x
    .var lpy byte   ; light pen y
    .var sprite_enable byte   ; sprite enable bits
    .var cr2 byte   ; control register 1

    .def cr2.res $20
    .def cr2.mcm $10
    .def cr2.csel $08
    .def cr2.xscroll $07

    .var sprite_y_expansion byte   ; sprite y expansion
    .var mem byte   ; memory pointers
    
    .def mem.vm13 $80
    .def mem.vm12 $40 
    .def mem.vm11 $20
    .def mem.vm10 $10
    .def mem.cb13 $08
    .def mem.cb12 $04
    .def mem.cb11 $02
    
    .var int byte   ; interrupt register

    .def int.irq $80
    .def int.ilp $08
    .def int.immc $04
    .def int.imbc $02
    .def int.irst $01

    .var int_enable byte ; interrupt enable

    .def int_enable.elp $08
    .def int_enable.emmc $04
    .def int_enable.embc $02
    .def int_enable.erst $01

    .var sprite_data_priority byte
    .var sprite_multicolor byte
    .var sprite_x_expansion byte
    .var sprite_collision byte
    .var sprite_data_collision byte

    .var ec byte    ; border color
    .var b0c byte   ; background color 0
    .var b1c byte 
    .var b2c byte
    .var b3c byte
    .var mm0 byte   ; sprite multicolor 0
    .var mm1 byte
    .var m0c byte   ; color sprite 0
    .var m1c byte
    .var m2c byte
    .var m3c byte
    .var m4c byte
    .var m5c byte
    .var m6c byte
    .var m7c byte
.end

; VIC-II 16k memory bank
.struct vic2_bank $1000
    .var char_rom $1fff
.end

; VIC-II bank base addresses
.def vic2_bank0 $0000
.def vic2_bank1 $4000
.def vic2_bank2 $8000
.def vic2_bank3 $C000
