; Copyright (c) 2020, Eric Anderton
; All rights reserved.
; Published under the BSD license.  See LICENSE For details.
;
; C64 Sound Interface Device (SID)
; https://www.c64-wiki.com/wiki/SID
;

.struct sid $d400
    ; constants common to all voices    
    
    ; ADSR envelope masks
    .def decay $0F
    .def attack $F0
    .def release $0F
    .def sustain $F0
 
    ; voice control bits
    .def ctrl.gate $01
    .def ctrl.sync $02  ; synchronize with voice 3
    .def ctrl.ringmod $04  ; ring modulation with voice 3
    .def ctrl.test $08
    .def ctrl.triangle  $01
    .def ctrl.sawtooth  $02
    .def ctrl.pulse  $04
    .def ctrl.noise $80
    
    .var voice1.freq word
    .var voice1.duty word  ; pulse wave duty cycle: 12 bits wide
    .var voice1.ctrl byte
    .var voice1.ad byte
    .var voice1.sr byte

    .var voice2.freq word
    .var voice2.duty word  ; pulse wave duty cycle: 12 bits wide
    .var voice2.ctrl byte
    .var voice2.ad byte
    .var voice2.sr byte

    .var voice3.freq word
    .var voice3.duty word  ; pulse wave duty cycle: 12 bits wide
    .var voice3.ctrl byte
    .var voice3.ad byte
    .var voice3.sr byte

    ; filter cutoff frequency is organized into a fine adjustment
    ; four bits in the low byte, and a coarse adjustment in the 
    ; high 8 bits.
    .var cutoff_lo byte  ; 4 bits wide
    .var cutoff_hi byte
    .var resonance byte  ; filter resonance and routing

    .def resonance.voice1 $01
    .def resonance.voice2 $02
    .def resonance.voice3 $04
    .def resonance.ext $08
    .def resonance.value $F0

    .var filter byte

    .def filter.volume $0F
    .def filter.lowp $10
    .def filter.band $20
    .def filter.hi $40
    .def fitler.mute3 $80  ; mute voice 3

    ; read-only registers
    .var paddlex byte
    .var paddley byte
    .var osc3 byte  ; oscillator voice 3 value
    .var env3 byte  ; envelope voice 3 value   
.end

.def sid_mirror $D500
