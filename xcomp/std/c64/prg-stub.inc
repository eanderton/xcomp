.include "std/c64-const.inc"

; PRG BASIC stub for LOAD/RUN
.pragma c64_prg_start $0801
.text $0801
.scope 
LINE_10:
    .word LINE_END
    .word 10 ; line number 
    .byte TOK_SYS, " 2062", $00 ; jmp to $080E
LINE_END:
    .word $0000 ; end of BASIC program (next line is $0000)
.end
