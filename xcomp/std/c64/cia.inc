;
; Support for the C64 CIA1 and CIA2 chips
; https://www.c64-wiki.com/wiki/CIA
;

; Adress area: $DC00-$DCFF, 56320-56575 Tasks: Keyboard, Joystick, Paddles, Datasette, IRQ control 
.struct cia1 $DC00
    ; data ports
    .var pra byte ; data port A

    .def pra.joy2_dir $0F
    .def pra.joy2_fire $10

    .var prb byte ; data port B

    .def prb.joy1_dir $0F
    .def prb.joy1_fire $10
    .def prb.timer_a $40
    .def prb.timer_b $80

    ; data direction
    ; Bit X: 0=Input (read only), 1=Output (read and write) 
    .var ddra byte ; data direction port A 
    .var ddrb byte ; data direction port B

    ; timer A/B
    .var talo byte ; timer A low byte
    .var tahi byte ; timer A high byte
    .var tblo byte ; timer B low byte
    .var tbhi byte ; timer B high byte

    ; real-time clock
    .var tod_10ths byte ; timer in BCD tenths of a second (low nybble only)
    .var tod_sec byte ; timer in BCD seconds
    .var tod_min byte ; timer in BCD minutes
    .var tod_hr byte ; time in BCD hours
    
    ; The byte within this register will be shifted bitwise to or 
    ; from the SP-pin with every positive slope at the CNT-pin. 
    .var sdr byte ; serial shift register
    
    ; interrupt control and status register
    .var icr byte

    ; reading bits indicates interrupt source
    ; NOTE: Flags will be cleared after reading the register!
    .def icr.read.underflow_timer_a $01
    .def icr.read.underflow_timer_b $02 
    .def icr.read.alarm $04 ; time of day and alarm time is equal
    .def icr.read.sdr $08 ; SDR full or empty, so full byte was transferred, depending of operating mode serial bus
    .def icr.read.irq $10 ; IRQ Signal occured at FLAG-pin (cassette port Data input, serial bus SRQ IN)
    .def icr.read.int $80 ; IRQ An interrupt occured, so at least one bit of INT MASK and INT DATA is set in both registers.

    ; writing bits releases an interrupt on a condition
    .def icr.write.timer_a $01 ; release on timer A underflow
    .def icr.write.timer_b $02 ; release on timer B underflow
    .def icr.write.clock $04   ; release if clock == alarmtime
    .def icr.write.byte $08    ; release if a complete byte has been received/sent.
    .def icr.write.flag $10    ; a positive slope occurs at the FLAG-Pin.
    .def icr.write.source $80  ; Source bit. 0 = set bits 0..4 are clearing the according mask bit. 1 = set bits 0..4 are setting the according mask bit. If all bits 0..4 are cleared, there will be no change to the mask.

    ; control timer A
    .var cra byte

    .def cra.startstop $01  ; 0 = Stop timer; 1 = Start timer
    .def cra.underflow $02  ; 1 = Indicates a timer underflow at port B in bit 6.
    .def cra.overflow $04   ; 0 = Through a timer overflow, bit 6 of port B will get high for one cycle , 1 = Through a timer underflow, bit 6 of port B will be inverted
    .def cra.restart $08    ; 0 = Timer-restart after underflow (latch will be reloaded), 1 = Timer stops after underflow.
    .def cra.latch $10      ; 1 = Load latch into the timer once.
    .def cra.count $20      ; 0 = Timer counts system cycles, 1 = Timer counts positive slope at CNT-pin
    .def cra.direction $40  ; Direction of the serial shift register, 0 = SP-pin is input (read), 1 = SP-pin is output (write)
    .def cra.clock_rate $80 ; Real Time Clock, 0 = 60 Hz, 1 = 50 Hz

    ; control timer B 
    .var crb byte

    .def crb.startstop $01  ; 0 = Stop timer; 1 = Start timer
    .def crb.underflow $02  ; 1 = Indicates a timer underflow at port B in bit 7.
    .def crb.overflow $04   ; 0 = Through a timer overflow, bit 7 of port B will get high for one cycle , 1 = Through a timer underflow, bit 7 of port B will be inverted
    .def crb.restart $08    ; 0 = Timer-restart after underflow (latch will be reloaded), 1 = Timer stops after underflow.
    .def crb.latch   $10    ; 1 = Load latch into the timer once.
    .def crb.counter.mask  $60
    .def crb.counter.system $00 ; Timer counts System cycle
    .def crb.counter.positive $20 ; Timer counts positive slope on CNT-pin
    .def crb.counter.underflow $40 ;  Timer counts underflow of timer A
    .def crb.counter.underflow_high $60 ;  Timer counts underflow of timer A if the CNT-pin is high
    .def crb.clock_set $80  ; 0 = Writing into the TOD register sets the clock time, 1 = Writing into the TOD register sets the alarm time. 

.end

; Adress range: $DD00-$DDFF, 56576-56831 Tasks: Serial bus, RS-232, VIC memory, NMI control 
.struct cia2 $DD00
    .var pra byte ; data port A

    ; Bit 0..1: Select the position of the VIC-memory
    .def pra.vic2.mask $03 
    .def pra.vic2.bank3 $00 ; Bank 3: $C000-$FFFF, 49152-65535
    .def pra.vic2.bank2 $01 ; Bank 2: $8000-$BFFF, 32768-49151
    .def pra.vic2.bank1 $02 ; Bank 1: $4000-$7FFF, 16384-32767
    .def pra.vic2.bank0 $03 ; Bank 0: $0000-$3FFF, 0-16383 (standard)
    .def pra.rs232 $4 ; RS-232: TXD Output, userport: Data PA 2 (pin M)
    
    .def pra.bus.atn_out $08   ; (0=High/Inactive, 1=Low/Active)
    .def pra.bus.clock_out $10 ; (0=High/Inactive, 1=Low/Active)
    .def pra.bus.data_out $20  ; (0=High/Inactive, 1=Low/Active)
    .def pra.bus.clock_in $40  ; (0=Low/Active, 1=High/Inactive)
    .def pra.bus.data_in $80   ; (0=Low/Active, 1=High/Inactive)

    .var prb byte ; data port B

    ; Bit 0..7: userport Data PB 0-7 (Pins C,D,E,F,H,J,K,L)
    .def prb.read.rx $01
    .def prb.read.ri $08
    .def prb.read.dcd $10
    .def prb.read.user_j $20
    .def prb.read.cts $40
    .def prb.read.dsr $80

    ; Bit 1..5: RS-232: writing
    .def prb.write.rts $02
    .def prb.write.dtr $04
    .def prb.write.ri  $08
    .def prb.write.dcd $10
    .def prb.write.user_j $20

    ; data direction
    ; Bit X: 0=Input (read only), 1=Output (read and write) 
    .var ddra byte ; data direction port A 
    .var ddrb byte ; data direction port B

    ; timer A/B
    .var talo byte ; timer A low byte
    .var tahi byte ; timer A high byte
    .var tblo byte ; timer B low byte
    .var tbhi byte ; timer B high byte

    ; real-time clock
    .var tod_10ths byte ; timer in BCD tenths of a second (low nybble only)
    .var tod_sec byte ; timer in BCD seconds
    .var tod_min byte ; timer in BCD minutes
    .var tod_hr byte ; time in BCD hours
    
    ; The byte within this register will be shifted bitwise to or 
    ; from the SP-pin with every positive slope at the CNT-pin. 
    .var sdr byte ; serial shift register
    
    ; interrupt control and status register
    .var icr byte

    .def icr.nmi.flag $10 ; 1 = NMI Signal occured at FLAG-pin (RS-232 data received)
    .def icr.nmi.data $80 ; NMI An interrupt occured, so at least one bit of INT MASK and INT DATA is set in both registers.

    ; control timer A
    .var cra byte

    .def cra.startstop $01  ; 0 = Stop timer; 1 = Start timer
    .def cra.underflow $02  ; 1 = Indicates a timer underflow at port B in bit 6.
    .def cra.overflow $04   ; 0 = Through a timer overflow, bit 6 of port B will get high for one cycle , 1 = Through a timer underflow, bit 6 of port B will be inverted
    .def cra.restart $08    ; 0 = Timer-restart after underflow (latch will be reloaded), 1 = Timer stops after underflow.
    .def cra.latch $10      ; 1 = Load latch into the timer once.
    .def cra.count $20      ; 0 = Timer counts system cycles, 1 = Timer counts positive slope at CNT-pin
    .def cra.direction $40  ; Direction of the serial shift register, 0 = SP-pin is input (read), 1 = SP-pin is output (write)
    .def cra.clock_rate $80 ; Real Time Clock, 0 = 60 Hz, 1 = 50 Hz

    ; control timer B 
    .var crb byte

    .def crb.startstop $01  ; 0 = Stop timer; 1 = Start timer
    .def crb.underflow $02  ; 1 = Indicates a timer underflow at port B in bit 7.
    .def crb.overflow $04   ; 0 = Through a timer overflow, bit 7 of port B will get high for one cycle , 1 = Through a timer underflow, bit 7 of port B will be inverted
    .def crb.restart $08    ; 0 = Timer-restart after underflow (latch will be reloaded), 1 = Timer stops after underflow.
    .def crb.latch   $10    ; 1 = Load latch into the timer once.
    .def crb.counter.mask  $60
    .def crb.counter.system $00 ; Timer counts System cycle
    .def crb.counter.positive $20 ; Timer counts positive slope on CNT-pin
    .def crb.counter.underflow $40 ;  Timer counts underflow of timer A
    .def crb.counter.underflow_high $60 ;  Timer counts underflow of timer A if the CNT-pin is high
    .def crb.clock_set $80  ; 0 = Writing into the TOD register sets the clock time, 1 = Writing into the TOD register sets the alarm time. 
.end


; expects a value of 0-3 to select the bank number
.macro set_vic_bank bank_no
    lda cia.pra
    and ~cia.pra.vic2.mask
    ora ~bank_no & cia.pra.vic2.mask
    sta
.end
