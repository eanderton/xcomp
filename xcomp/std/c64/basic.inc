; Copyright (c) 2020, Eric Anderton
; All rights reserved.
; Published under the BSD license.  See LICENSE For details.
;
; Constants used for C64 BASIC v2.0
; https://www.c64-wiki.com/wiki/BASIC_token
; 

; Emits a single line of BASIC code
; - start program at $0801
; - end program with `bas_end` macro
.macro bas, line, tok, text
    .word next_line, line
    .byte tok, text, basic.eol
next_line:
.end

; Terminates a BASIC program in memory
.macro bas_end
    .word basic.end_program
.end

; Useful constants for BASIC programs
.struct basic
    .def eol $00
    .def end_program $0000  ; two bytes

    ; tokens used in compiled BASIC code
    .def end $80
    .def for $81
    .def next $82
    .def data $83
    .def input_ext $84  ; INPUT# from peripheral
    .def input_kbd $85  ; INPUT from keyboard
    .def dim $86
    .def read $87
    .def let $88
    .def goto $89
    .def run $8a
    .def if $8b
    .def restore $8c
    .def gosub $8d
    .def return $8e
    .def rem $8f
    .def stop $90
    .def on $91
    .def wait $92
    .def load $93
    .def save $94
    .def verify $95
    .def def $96
    .def poke $97
    .def print_ext $98 ; PRINT# to file
    .def print $99 ; PRINT to screen
    .def cont $9a
    .def list $9b
    .def clr $9c
    .def cmd $9d
    .def sys $9e
    .def open $9f
    .def close $a0
    .def get $a1
    .def new $a2
    .def tab $a3
    .def to $a4
    .def fn $a5
    .def spc $a6
    .def then $a7
    .def not $a8
    .def step $a9
    .def add $aa
    .def sub $ab
    .def mul $ac
    .def div $ad
    .def power $ae
    .def and $af
    .def or $b0
    .def gt $b1 ; greater-than operator (>)
    .def eq $b2 ; equals operator (=)
    .def lt $b3 ; less-than operator (<)
    .def sgn $b4
    .def int $b5
    .def abs $b6
    .def usr $b7
    .def fre $b8
    .def pos $b9
    .def sqr $ba
    .def rnd $bb
    .def log $bc
    .def exp $bd
    .def cos $be
    .def sin $bf
    .def tan $c0
    .def atn $c1
    .def peek $c2
    .def len $c3
    .def str $c4
    .def val $c5
    .def asc $c6
    .def chr $c7
    .def left $c8
    .def right $c9
    .def mid $ca
    .def go $cb
.end
