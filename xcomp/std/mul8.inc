; Copyright (c) 2020, Eric Anderton
; All rights reserved.
; Published under the BSD license.  See LICENSE For details.
;
; mul8 - 8x8 bit multiplier
;
; - mul8_arg1 byte argument one to multiply
; - mul8_arg2 byte augument two to multiply (destroyed by operation)
; - mul8_result word result of multiplication

.zero
    .var mul8_arg1 byte
    .var mul8_arg2 byte
    .var mul8_result word

.text
mul8:
.scope
        lda #0          ;Initialize RESULT to 0
        ldx #8          ;There are 8 bits in NUM2
loop1: 
        lsr mul8_arg2   ;Get low bit of NUM2
        bcc loop2       ;0 or 1?
        clc             ;If 1, add NUM1
        adc mul8_arg1
loop2:
        ror a           ;"Stairstep" shift (catching carry from add)
        ror mul8_result
        dex
        bne loop1
        sta mul8_result+1
        rts
.end
