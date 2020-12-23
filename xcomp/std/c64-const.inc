; PETSCII values
.def COLON $3A
.def SPACE  $20     

; BASIC Tokens
.def TOK_REM    $8F
.def TOK_SYS    $9E

; Registers
.def CCHROUT    $FFD2             ; Output character to current output device

; VIC II
.def VIC_BORDER_COLOR  $d020
.def VIC_MX8  $D010

.def VIC_CR1  $D011
.def RST8     %10000000
.def ECM      %01000000
.def BMM      %00100000
.def DEN      %00010000
.def RSEL     %00001000
.def YSCROLL  %00000111

.def VIC_RASTER  $D012
.def VIC_RSTCMP  $D013

.def VIC_CR2  $D016
.def RES      %00100000
.def MCM      %00010000
.def CSEL     %00001000
.def XSCROLL  %00000111

.def VIC_VMCB  $D018
.def SCREEN_PTR  %11110000
.def CHARSET_PTR  %00001110

.def CIA2_DATA_A  $DD00

.def SID_VOICE3_FREQ_LO  $D40E
.def SID_VOICE3_FREQ_HI  $D40F
.def SID_VOICE3_CTRL  $D412
.def SID_VOICE3_VALUE  $D41B

; Memory
.def VIC_BANK0  $0000
.def VIC_BANK1  $4000
.def VIC_BANK2  $8000
.def VIC_BANK3  $C000

.def CHAR_RAM  $0400
.def COLOR_RAM  $0800
.def BITMAP_RAM  $2000

.struct basic_rom $A000
    .var data $2000
.end

.struct char_rom $D000
    .var data $2000
.end

.struct kernel_rom $E000
    .var data $2000
.end
