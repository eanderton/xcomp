; Copyright (c) 2020, Eric Anderton
; All rights reserved.
; Published under the BSD license.  See LICENSE For details.
; Macro definitions for frequently used inline code

.macro set_mem16, m16, c16
    lda #<(c16)
    sta m16
    lda #>(c16)
    sta m16+1
.end

.macro add_mem16, m16, c16
    clc
    lda m16
    adc #<(c16)
    sta m16
    lda m16+1
    adc #>(c16)
    sta m16+1
.end

.macro pushy
    tya
    pha 
.end

.macro pully
    pla
    tay
.end

.macro pushx
    txa
    pha
.end

.macro pullx
    pla
    tax
.end
