; Copyright (c) 2020, Eric Anderton
; All rights reserved.
; Published under the BSD license.  See LICENSE For details.
;
; PRG BASIC stub for LOAD/RUN
;
.pragma c64_prg_start $0801
.text $0801
    bas 10, basic.sys, "2061"
    bas_end
