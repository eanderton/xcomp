; Macro definitions for frequently used inline code

.macro set_mem16, m16, c16
    lda #<(c16)
    sta m16
    lda #>(c16)
    sta m16+1
.endmacro

.macro add_mem16, m16, c16
  clc
  lda m16
  adc #<(c16)
  sta m16
  lda m16+1
  adc #>(c16)
  sta m16+1
.endmacro

.macro pushy tya pha .endmacro
.macro pully pla tay .endmacro

.macro pushx txa pha .endmacro
.macro pullx pla tax .endmacro
