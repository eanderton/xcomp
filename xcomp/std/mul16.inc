;
; mul16 - 16x16 bit multiplier
;
; - mul16_arg1 word argument to multiply
; - mul16_arg2 word argument to multiply (destroyed by operation)
; - mul16_result long word result of multiplication

.zero
  .var mul16_arg1 word
  .var mul16_arg2 word
  .var mul16_result word+word

.text
mul16:
.scope
        lda #0              ;initialize mul16_result to 0
        sta mul16_result+2
        ldx #16             ;there are 16 bits in mul16_arg2
loop1:
        lsr mul16_arg2+1    ;get low bit of mul16_arg2
        ror mul16_arg2
        bcc loop2              ;0 or 1?
        tay                 ;if 1, add mul16_arg1 (hi byte of mul16_result is in a)
        clc
        lda mul16_arg1
        adc mul16_result+2
        sta mul16_result+2
        tya
        adc mul16_arg1+1
loop2:
        ror a               ;"stairstep" shift
        ror mul16_result+2
        ror mul16_result+1
        ror mul16_result
        dex
        bne loop1
        sta mul16_result+3
        rts
.end
