;
; PRG BASIC stub for LOAD/RUN
;
.pragma c64_prg_start $0801
.text $0801
    bas 10, basic.sys, "2061"
    .word basic.end_program
