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
    .var mem byte   ; memory offsets
   
    ; bit 0: bitmap offset in VIC-II bank
    ; 0 = $0000
    ; 1 = $2000
    .def mem.bitmap $01

    ; bits 1-3: character memory in VIC-II bank
    ; in alternating 8 and 2 page offsets
    ; $D018 = %xxxx000x -> charmem is at $0000
    ; $D018 = %xxxx001x -> charmem is at $0800
    ; $D018 = %xxxx010x -> charmem is at $1000
    ; $D018 = %xxxx011x -> charmem is at $1800
    ; $D018 = %xxxx100x -> charmem is at $2000
    ; $D018 = %xxxx101x -> charmem is at $2800
    ; $D018 = %xxxx110x -> charmem is at $3000
    ; $D018 = %xxxx111x -> charmem is at $3800
    .def mem.char $0E
    
    ; bits 4-7: screen offset in VIC-II bank
    ; in 4 page ($0400) increments ($0000 through $3C00)
    ; $D018 = %0000xxxx -> screenmem is at $0000
    ; $D018 = %0001xxxx -> screenmem is at $0400
    ; $D018 = %0010xxxx -> screenmem is at $0800
    ; $D018 = %0011xxxx -> screenmem is at $0c00
    ; $D018 = %0100xxxx -> screenmem is at $1000
    ; $D018 = %0101xxxx -> screenmem is at $1400
    ; $D018 = %0110xxxx -> screenmem is at $1800
    ; $D018 = %0111xxxx -> screenmem is at $1c00
    ; $D018 = %1000xxxx -> screenmem is at $2000
    ; $D018 = %1001xxxx -> screenmem is at $2400
    ; $D018 = %1010xxxx -> screenmem is at $2800
    ; $D018 = %1011xxxx -> screenmem is at $2c00
    ; $D018 = %1100xxxx -> screenmem is at $3000
    ; $D018 = %1101xxxx -> screenmem is at $3400
    ; $D018 = %1110xxxx -> screenmem is at $3800
    ; $D018 = %1111xxxx -> screenmem is at $3c00
    .def mem.screen $F0

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
