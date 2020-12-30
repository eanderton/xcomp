; Published to the public domain on the NESDev Wiki:
; https://wiki.nesdev.com/w/index.php/Nesdev_wiki:General_disclaimer
; https://wiki.nesdev.com/w/index.php/Random_number_generator
;
; Pseudorandom number generator basedona linear feedback shift register.
;
; Returns a random 8-bit number in A (0-255), clobbers Y (0).
;
; Requires a 2-byte value on the zero page called "seed".
; Initialize seed to any value except 0 before the first call to prng.
; (A seed value of 0 will cause prng to always return 0.)
;
; This is a 16-bit Galois linear feedback shift register with polynomial $0039.
; The sequence of numbers it generates will repeat after 65535 calls.
;
; Execution time is 69 cycles

.data
    .var prng_seed word 

.text
prng:
	lda prng_seed+1
	tax ; store copy of high byte
	; compute seed+1 ($39>>1 = %11100)
	lsr a; shift to consume zeroes on left...
	lsr a
	lsr a
	sta prng_seed+1 ; now recreate the remaining bits in reverse order... %111
	lsr a
	eor prng_seed+1
	lsr a
	eor prng_seed+1
	eor prng_seed+0 ; recombine with original low byte
	sta prng_seed+1
	; compute seed+0 ($39 = %111001)
	txa ; original high byte
	sta prng_seed+0
	asl a
	eor prng_seed+0
	asl a
	eor prng_seed+0
	asl a
	asl a
	asl a
	eor prng_seed+0
	sta prng_seed+0
	rts
