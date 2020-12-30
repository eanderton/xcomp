; Copyright (c) 2020, Eric Anderton
; All rights reserved.
; Published under the BSD license.  See LICENSE For details.
;
; Defines for the C64 Kernal
;

.struct kernal $E000
    .var __code__ $2000
    .def acptr   $FFA5 ; Input byte from serial port
    .def chkin   $FFC6 ; Open channel for input
    .def chkout  $FFC9 ; Open a channel for output
    .def chrin   $FFCF ; Get a character from the input channel
    .def chrout  $FFD2 ; Output a character
    .def ciout   $FFA8 ; Transmit a byte over the serial bus
    .def cint    $FF81 ; Initialize the screen editor and VIC-II Chip
    .def clall   $FFE7 ; Close all open files
    .def close   $FFC3 ; Close a logical file
    .def clrchn  $FFCC ; Clear all I/O channels
    .def getin   $FFE4 ; Get a character
    .def iobase  $FFF3 ; Define I/O memory page
    .def ioinit  $FF84 ; Initialize I/O devices
    .def listen  $FFB1 ; Command a device on the serial bus to listen
    .def load    $FFD5 ; Load RAM from device
    .def membot  $FF9C ; Set bottom of memory
    .def memtop  $FF99 ; Set the top of RAM
    .def open    $FFC0 ; Open a logical file
    .def plot    $FFF0 ; Set or retrieve cursor location
    .def ramtas  $FF87 ; Perform RAM test
    .def rdtim   $FFDE ; Read system clock
    .def readst  $FFB7 ; Read status word
    .def restor  $FF8A ; Set the top of RAM
    .def save    $FFD8 ; Save memory to a device
    .def scnkey  $FF9F ; Scan the keyboard
    .def screen  $FFED ; Return screen format
    .def second  $FF93 ; Send secondary address for LISTEN
    .def setlfs  $FFBA ; Set up a logical file
    .def setmsg  $FF90 ; Set system message output
    .def setnam  $FFBD ; Set up file name
    .def settim  $FFDB ; Set the system clock
    .def settmo  $FFA2 ; Set IEEE bus card timeout flag
    .def stop    $FFE1 ; Check if STOP key is pressed
    .def talk    $FFB4 ; Command a device on the serial bus to talk
    .def tksa    $FF96 ; Send a secondary address to a device commanded to talk
    .def udtim   $FFEA ; Update the system clock
    .def unlsn   $FFAE ; Send an UNLISTEN command
    .def untlk   $FFAB ; Send an UNTALK command
    .def vector  $FF8D ; Manage RAM vectors 
.end
