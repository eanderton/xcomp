.include "std/c64-const.inc"

; PRG BASIC stub for LOAD/RUN
.pragma c64_prg_start $0801
.text $0801
LINE_10:
    .word LINE_END
    .word 10 ; line number 
    .byte TOK_SYS, SPACE, $32, $30, $36, $32 ; "SYS 2062" - jmp to $080E
    .byte $00 ; EOL
LINE_END:
    .word $0000 ; end of BASIC program (next line is $0000)
