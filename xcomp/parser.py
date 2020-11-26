from itertools import chain
from parsimonious.grammar import Grammar, TokenGrammar
from xcomp.model import *
from xcomp.reduce_parser import ReduceParser, Token
from xcomp.cpu6502 import *


grammar = r"""
goal            = (include / macro / def / core_syntax)*

core_syntax     = comment / byte_storage / word_storage / segment /
                  (_ label) / oper / macro_call / _

comment         = ~r";\s*.*(?=\n|$)"

def             = def_tok _ ident _ expr

byte_storage    = byte_tok _ storage
word_storage    = word_tok _ storage
storage         = expr _ (comma_tok _ expr _)*

segment         = period_tok segment_name _ expr?
segment_name    = "zero" / "text" / "data" / "bss"

include         = include_tok _ string

macro           = macro_tok _ macro_params _ macro_body _ endmacro_tok
macro_params    = ident _ (comma_tok _ macro_params _)?
macro_body      = core_syntax*

macro_call      = ident _ macro_args?
macro_args      = expr _ (comma_tok _ expr _)?

label           = ident colon_tok

expr16          = bang_tok expr

expr            = sub / add / negate / lobyte / hibyte / term
negate          = minus_tok _ term
lobyte          = lessthan_tok _ term
hibyte          = morethan_tok _ term
add             = term _ plus_tok _ expr
sub             = term _ sub _ expr

term            = div / mul / exp
mul             = exp _ asterisk_tok _ exp
div             = exp _ slash_tok _ exp

exp             = pow / fact
pow             = fact carrot_tok fact
fact            = ident / string / number / group_expr

group_expr      = lparen_tok _ expr _ rparen_tok

string          = quote_tok ((backslash_tok escape_char) / stringchar)* endquote_tok
stringchar      = ~r'[^\\"]+'
escape_char     = 'r' / 'n' / 't' / 'v' / '"' / '\\'

number          = base2 / base16 / base10
base2           = percent_tok ~r"[01]{1,16}"
base16          = hex_tok ~r"[0-9a-fA-F]{1,4}"
base10          = ~r"(\d+)"

ident           = ~r"[_a-zA-Z][_a-zA-Z0-9]*"

# asm grammar tokens
byte_tok        = ".byte"
word_tok        = ".word"
include_tok     = ".include"
def_tok         = ".def"
macro_tok       = ".macro"
endmacro_tok    = ".endmacro"
bang_tok        = "!"
percent_tok     = "%"
hex_tok         = ~r"\$|0x"
backslash_tok   = "\\"
quote_tok       = "\""
endquote_tok    = "\""
lparen_tok      = "("
rparen_tok      = ")"
plus_tok        = "+"
minus_tok       = "-"
slash_tok       = "/"
carrot_tok      = "^"
pipe_tok        = "|"
ampersand_tok   = "&"
comma_tok       = ","
hash_tok        = "#"
lessthan_tok    = "<"
morethan_tok    = ">"
colon_tok       = ":"
asterisk_tok    = "*"
period_tok      = "."
_               = ~r"\s*"

# 6502 opcode tokens
a_tok           = "a"
x_tok           = "x"
y_tok           = "y"
adc_tok         = "adc"
and_tok         = "and"
asl_tok         = "asl"
bcc_tok         = "bcc"
bcs_tok         = "bcs"
beq_tok         = "beq"
bit_tok         = "bit"
bmi_tok         = "bmi"
bne_tok         = "bne"
bpl_tok         = "bpl"
brk_tok         = "brk"
bvc_tok         = "bvc"
clc_tok         = "clc"
cld_tok         = "cld"
cli_tok         = "cli"
clv_tok         = "clv"
cmp_tok         = "cmp"
cpx_tok         = "cpx"
cpy_tok         = "cpy"
dec_tok         = "dec"
eor_tok         = "eor"
inc_tok         = "inc"
inx_tok         = "inx"
iny_tok         = "iny"
jmp_tok         = "jmp"
jsr_tok         = "jsr"
lda_tok         = "lda"
ldx_tok         = "ldx"
ldy_tok         = "ldy"
lsr_tok         = "lsr"
nop_tok         = "nop"
ora_tok         = "ora"
pha_tok         = "pha"
php_tok         = "php"
pla_tok         = "pla"
plp_tok         = "plp"
rol_tok         = "rol"
ror_tok         = "ror"
rti_tok         = "rti"
rts_tok         = "rts"
sbc_tok         = "sbc"
sec_tok         = "sec"
sed_tok         = "sed"
sei_tok         = "sei"
sta_tok         = "sta"
stx_tok         = "stx"
sty_tok         = "sty"
tax_tok         = "tax"
tay_tok         = "tay"
tsx_tok         = "tsx"
txa_tok         = "txa"
txs_tok         = "txs"
tya_tok         = "tya"

# 6502 instructions
op_adc_immediate = adc_tok _ hash_tok _ expr
op_adc_zeropage = adc_tok _ expr
op_adc_zeropage_x = adc_tok _ expr _ comma_tok _ x_tok
op_adc_absolute = adc_tok _ expr
op_adc_absolute_x = adc_tok _ expr16 _ comma_tok _ x_tok
op_adc_absolute_y = adc_tok _ expr16 _ comma_tok _ y_tok
op_adc_indirect_x = adc_tok _ lparen_tok _ expr _ comma_tok _ x_tok _ rparen_tok
op_adc_indirect_y = adc_tok _ lparen_tok _ expr _ rparen_tok _ comma_tok _ y_tok
op_and_immediate = and_tok _ hash_tok _ expr
op_and_zeropage = and_tok _ expr
op_and_zeropage_x = and_tok _ expr _ comma_tok _ x_tok
op_and_absolute = and_tok _ expr
op_and_absolute_x = and_tok _ expr16 _ comma_tok _ x_tok
op_and_absolute_y = and_tok _ expr16 _ comma_tok _ y_tok
op_and_indirect_x = and_tok _ lparen_tok _ expr _ comma_tok _ x_tok _ rparen_tok
op_and_indirect_y = and_tok _ lparen_tok _ expr _ rparen_tok _ comma_tok _ y_tok
op_asl_accumulator = asl_tok _ a_tok
op_asl_zeropage = asl_tok _ expr
op_asl_zeropage_x = asl_tok _ expr _ comma_tok _ x_tok
op_asl_absolute = asl_tok _ expr
op_asl_absolute_x = asl_tok _ expr16 _ comma_tok _ x_tok
op_bcc_relative = bcc_tok _ expr
op_bcs_relative = bcs_tok _ expr
op_beq_relative = beq_tok _ expr
op_bit_zeropage = bit_tok _ expr
op_bit_absolute = bit_tok _ expr
op_bmi_relative = bmi_tok _ expr
op_bne_relative = bne_tok _ expr
op_bpl_relative = bpl_tok _ expr
op_brk_implied = _ brk_tok
op_bvc_relative = bvc_tok _ expr
op_bvc_relative = bvc_tok _ expr
op_clc_implied = _ clc_tok
op_cld_implied = _ cld_tok
op_cli_implied = _ cli_tok
op_clv_implied = _ clv_tok
op_cmp_immediate = cmp_tok _ hash_tok _ expr
op_cmp_zeropage = cmp_tok _ expr
op_cmp_zeropage_x = cmp_tok _ expr _ comma_tok _ x_tok
op_cmp_absolute = cmp_tok _ expr
op_cmp_absolute_x = cmp_tok _ expr16 _ comma_tok _ x_tok
op_cmp_absolute_y = cmp_tok _ expr16 _ comma_tok _ y_tok
op_cmp_indirect_x = cmp_tok _ lparen_tok _ expr _ comma_tok _ x_tok _ rparen_tok
op_cmp_indirect_y = cmp_tok _ lparen_tok _ expr _ rparen_tok _ comma_tok _ y_tok
op_cpx_immediate = cpx_tok _ hash_tok _ expr
op_cpx_zeropage = cpx_tok _ expr
op_cpx_absolute = cpx_tok _ expr
op_cpy_immediate = cpy_tok _ hash_tok _ expr
op_cpy_zeropage = cpy_tok _ expr
op_cpy_absolute = cpy_tok _ expr
op_dec_zeropage = dec_tok _ expr
op_dec_zeropage_x = dec_tok _ expr _ comma_tok _ x_tok
op_dec_absolute = dec_tok _ expr
op_dec_absolute_x = dec_tok _ expr16 _ comma_tok _ x_tok
op_dec_implied = _ dec_tok
op_dec_implied = _ dec_tok
op_eor_immediate = eor_tok _ hash_tok _ expr
op_eor_zeropage = eor_tok _ expr
op_eor_zeropage_x = eor_tok _ expr _ comma_tok _ x_tok
op_eor_absolute = eor_tok _ expr
op_eor_absolute_x = eor_tok _ expr16 _ comma_tok _ x_tok
op_eor_absolute_y = eor_tok _ expr16 _ comma_tok _ y_tok
op_eor_indirect_x = eor_tok _ lparen_tok _ expr _ comma_tok _ x_tok _ rparen_tok
op_eor_indirect_y = eor_tok _ lparen_tok _ expr _ rparen_tok _ comma_tok _ y_tok
op_inc_zeropage = inc_tok _ expr
op_inc_zeropage_x = inc_tok _ expr _ comma_tok _ x_tok
op_inc_absolute = inc_tok _ expr
op_inc_absolute_x = inc_tok _ expr16 _ comma_tok _ x_tok
op_inx_implied = _ inx_tok
op_iny_implied = _ iny_tok
op_jmp_absolute = jmp_tok _ expr
op_jmp_indirect = jmp_tok _ lparen_tok _ expr _ rparen_tok
op_jsr_absolute = jsr_tok _ expr
op_lda_immediate = lda_tok _ hash_tok _ expr
op_lda_zeropage = lda_tok _ expr
op_lda_zeropage_x = lda_tok _ expr _ comma_tok _ x_tok
op_lda_absolute = lda_tok _ expr
op_lda_absolute_x = lda_tok _ expr16 _ comma_tok _ x_tok
op_lda_absolute_y = lda_tok _ expr16 _ comma_tok _ y_tok
op_lda_indirect_x = lda_tok _ lparen_tok _ expr _ comma_tok _ x_tok _ rparen_tok
op_lda_indirect_y = lda_tok _ lparen_tok _ expr _ rparen_tok _ comma_tok _ y_tok
op_ldx_immediate = ldx_tok _ hash_tok _ expr
op_ldx_zeropage = ldx_tok _ expr
op_ldx_zeropage_y = ldx_tok _ expr _ comma_tok _ y_tok
op_ldx_absolute = ldx_tok _ expr
op_ldx_absolute_y = ldx_tok _ expr16 _ comma_tok _ y_tok
op_ldy_immediate = ldy_tok _ hash_tok _ expr
op_ldy_zeropage = ldy_tok _ expr
op_ldy_zeropage_x = ldy_tok _ expr _ comma_tok _ x_tok
op_ldy_absolute = ldy_tok _ expr
op_ldy_absolute_x = ldy_tok _ expr16 _ comma_tok _ x_tok
op_lsr_accumulator = lsr_tok _ a_tok
op_lsr_zeropage = lsr_tok _ expr
op_lsr_zeropage_x = lsr_tok _ expr _ comma_tok _ x_tok
op_lsr_absolute = lsr_tok _ expr
op_lsr_absolute_x = lsr_tok _ expr16 _ comma_tok _ x_tok
op_nop_implied = _ nop_tok
op_ora_immediate = ora_tok _ hash_tok _ expr
op_ora_zeropage = ora_tok _ expr
op_ora_zeropage_x = ora_tok _ expr _ comma_tok _ x_tok
op_ora_absolute = ora_tok _ expr
op_ora_absolute_x = ora_tok _ expr16 _ comma_tok _ x_tok
op_ora_absolute_y = ora_tok _ expr16 _ comma_tok _ y_tok
op_ora_indirect_x = ora_tok _ lparen_tok _ expr _ comma_tok _ x_tok _ rparen_tok
op_ora_indirect_y = ora_tok _ lparen_tok _ expr _ rparen_tok _ comma_tok _ y_tok
op_pha_implied = _ pha_tok
op_php_implied = _ php_tok
op_pla_implied = _ pla_tok
op_plp_implied = _ plp_tok
op_rol_accumulator = rol_tok _ a_tok
op_rol_zeropage = rol_tok _ expr
op_rol_zeropage_x = rol_tok _ expr _ comma_tok _ x_tok
op_rol_absolute = rol_tok _ expr
op_rol_absolute_x = rol_tok _ expr16 _ comma_tok _ x_tok
op_ror_accumulator = ror_tok _ a_tok
op_ror_zeropage = ror_tok _ expr
op_ror_zeropage_x = ror_tok _ expr _ comma_tok _ x_tok
op_ror_absolute = ror_tok _ expr
op_ror_absolute_x = ror_tok _ expr16 _ comma_tok _ x_tok
op_rti_implied = _ rti_tok
op_rts_implied = _ rts_tok
op_sbc_immediate = sbc_tok _ hash_tok _ expr
op_sbc_zeropage = sbc_tok _ expr
op_sbc_zeropage_x = sbc_tok _ expr _ comma_tok _ x_tok
op_sbc_absolute = sbc_tok _ expr
op_sbc_absolute_x = sbc_tok _ expr16 _ comma_tok _ x_tok
op_sbc_absolute_y = sbc_tok _ expr16 _ comma_tok _ y_tok
op_sbc_indirect_x = sbc_tok _ lparen_tok _ expr _ comma_tok _ x_tok _ rparen_tok
op_sbc_indirect_y = sbc_tok _ lparen_tok _ expr _ rparen_tok _ comma_tok _ y_tok
op_sec_implied = _ sec_tok
op_sed_implied = _ sed_tok
op_sei_implied = _ sei_tok
op_sta_zeropage = sta_tok _ expr
op_sta_zeropage_x = sta_tok _ expr _ comma_tok _ x_tok
op_sta_absolute = sta_tok _ expr
op_sta_absolute_x = sta_tok _ expr16 _ comma_tok _ x_tok
op_sta_absolute_y = sta_tok _ expr16 _ comma_tok _ y_tok
op_sta_indirect_x = sta_tok _ lparen_tok _ expr _ comma_tok _ x_tok _ rparen_tok
op_sta_indirect_y = sta_tok _ lparen_tok _ expr _ rparen_tok _ comma_tok _ y_tok
op_stx_zeropage = stx_tok _ expr
op_stx_zeropage_y = stx_tok _ expr _ comma_tok _ y_tok
op_stx_absolute = stx_tok _ expr
op_sty_zeropage = sty_tok _ expr
op_sty_zeropage_x = sty_tok _ expr _ comma_tok _ x_tok
op_sty_absolute = sty_tok _ expr
op_tax_implied = _ tax_tok
op_tay_implied = _ tay_tok
op_tsx_implied = _ tsx_tok
op_txa_implied = _ txa_tok
op_txs_implied = _ txs_tok
op_tya_implied = _ tya_tok

# 6502 operations
oper = op_adc_immediate / op_adc_zeropage / op_adc_zeropage_x /
       op_adc_absolute / op_adc_absolute_x / op_adc_absolute_y /
       op_adc_indirect_x / op_adc_indirect_y / op_and_immediate /
       op_and_zeropage / op_and_zeropage_x / op_and_absolute /
       op_and_absolute_x / op_and_absolute_y / op_and_indirect_x /
       op_and_indirect_y / op_asl_accumulator / op_asl_zeropage /
       op_asl_zeropage_x / op_asl_absolute / op_asl_absolute_x /
       op_bcc_relative / op_bcs_relative / op_beq_relative /
       op_bit_zeropage / op_bit_absolute / op_bmi_relative /
       op_bne_relative / op_bpl_relative / op_brk_implied /
       op_bvc_relative / op_bvc_relative / op_clc_implied /
       op_cld_implied / op_cli_implied / op_clv_implied /
       op_cmp_immediate / op_cmp_zeropage / op_cmp_zeropage_x /
       op_cmp_absolute / op_cmp_absolute_x / op_cmp_absolute_y /
       op_cmp_indirect_x / op_cmp_indirect_y / op_cpx_immediate /
       op_cpx_zeropage / op_cpx_absolute / op_cpy_immediate /
       op_cpy_zeropage / op_cpy_absolute / op_dec_zeropage /
       op_dec_zeropage_x / op_dec_absolute / op_dec_absolute_x /
       op_dec_implied / op_dec_implied / op_eor_immediate /
       op_eor_zeropage / op_eor_zeropage_x / op_eor_absolute /
       op_eor_absolute_x / op_eor_absolute_y / op_eor_indirect_x /
       op_eor_indirect_y / op_inc_zeropage / op_inc_zeropage_x /
       op_inc_absolute / op_inc_absolute_x / op_inx_implied /
       op_iny_implied / op_jmp_absolute / op_jmp_indirect /
       op_jsr_absolute / op_lda_immediate / op_lda_zeropage /
       op_lda_zeropage_x / op_lda_absolute / op_lda_absolute_x /
       op_lda_absolute_y / op_lda_indirect_x / op_lda_indirect_y /
       op_ldx_immediate / op_ldx_zeropage / op_ldx_zeropage_y /
       op_ldx_absolute / op_ldx_absolute_y / op_ldy_immediate /
       op_ldy_zeropage / op_ldy_zeropage_x / op_ldy_absolute /
       op_ldy_absolute_x / op_lsr_accumulator / op_lsr_zeropage /
       op_lsr_zeropage_x / op_lsr_absolute / op_lsr_absolute_x /
       op_nop_implied / op_ora_immediate / op_ora_zeropage /
       op_ora_zeropage_x / op_ora_absolute / op_ora_absolute_x /
       op_ora_absolute_y / op_ora_indirect_x / op_ora_indirect_y /
       op_pha_implied / op_php_implied / op_pla_implied / op_plp_implied /
       op_rol_accumulator / op_rol_zeropage / op_rol_zeropage_x /
       op_rol_absolute / op_rol_absolute_x / op_ror_accumulator /
       op_ror_zeropage / op_ror_zeropage_x / op_ror_absolute /
       op_ror_absolute_x / op_rti_implied / op_rts_implied /
       op_sbc_immediate / op_sbc_zeropage / op_sbc_zeropage_x /
       op_sbc_absolute / op_sbc_absolute_x / op_sbc_absolute_y /
       op_sbc_indirect_x / op_sbc_indirect_y / op_sec_implied /
       op_sed_implied / op_sei_implied / op_sta_zeropage /
       op_sta_zeropage_x / op_sta_absolute / op_sta_absolute_x /
       op_sta_absolute_y / op_sta_indirect_x / op_sta_indirect_y /
       op_stx_zeropage / op_stx_zeropage_y / op_stx_absolute /
       op_sty_zeropage / op_sty_zeropage_x / op_sty_absolute /
       op_tax_implied / op_tay_implied / op_tsx_implied / op_txa_implied /
       op_txs_implied / op_tya_implied

__ignored       = "comment" / ~r".*_tok" / "_"
"""


class Parser(ReduceParser):

    def __init__(self):
        super().__init__(grammar_ebnf=grammar)

    def visit_segment(self, pos, name, addr=None):
        return Segment(pos, name.text, addr)

    def visit_include(self, pos, filename):
        return Include(pos, filename.value)

    def visit_def(self, pos, name, expr):
        return Define(pos, name.value, expr)

    ### MACRO ###

    def visit_macro(self, pos, params, fragment):
        name, *params = tuple(params.names)
        return Macro(pos, name, params, fragment.body)

    def visit_macro_params(self, pos, param, params=None):
        rest = params.names if params else []
        return Params(pos, [param.value] + rest)

    def visit_macro_body(self, pos, *body):
        return Fragment(pos, body)

    def visit_label(self, pos, name):
        return Label(pos, name.value)

    def visit_macro_call(self, pos, name, args=None):
        args = args or Args(Pos(pos.end, pos.end, pos.context))
        return MacroCall(pos, name.value, args)

    def visit_macro_args(self, pos, argument, args=None):
        rest = args.values if args else []
        return Args(pos, [argument] + rest)

    ### STORAGE ###

    def visit_byte_storage(self, pos, *exprs):
        return Storage(pos, 1, exprs)

    def visit_word_storage(self, pos, *exprs):
        return Storage(pos, 2, exprs)

    ### EXPRESSIONS ###

    visit_expr8 = Expr8
    visit_expr16 = Expr16
    visit_negate = ExprNegate
    visit_lobyte = ExprLobyte
    visit_hibyte = ExprHibyte
    visit_add = ExprAdd
    visit_sub = ExprSub
    visit_div = ExprDiv
    visit_mul = ExprMul

    ### STRING ###

    visit_string = String

    def visit_stringchar(self, pos, lit):
        return lit.text

    def error_endquote_tok(self, pos):
        return "Expected string end quote (\")"

    def visit_escape_char(self, pos, lit):
        return {
            'r': '\r',
            'n': '\n',
            't': '\t',
            'v': '\v',
            '"': '"',
            '\\': '\\',
        }[lit.text]

    def error_escape_char(self, e):
        value = e.text[e.pos:e.pos+1]
        return f"Invalid escape sequence: '\\{value}'"

    ### NUMBER ###

    def visit_base2(self, pos, lit):
        return ExprValue(pos, int(lit.text, base=2), 2)

    def visit_base16(self, pos, lit):
        return ExprValue(pos, int(lit.text, base=16), 16)

    def visit_base10(self, pos, lit):
        return ExprValue(pos, int(lit.text, base=10), 10)

    ### EXPR ###

    def visit_ident(self, pos, lit):
        return ExprName(pos, lit.text)


    def visit_op_adc_immediate(self, pos, arg=None):
        return Op(pos, opcode_xref["adc"][AddressMode.immediate], arg)

    def visit_op_adc_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["adc"][AddressMode.zeropage], arg)

    def visit_op_adc_zeropage_x(self, pos, arg=None):
        return Op(pos, opcode_xref["adc"][AddressMode.zeropage_x], arg)

    def visit_op_adc_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["adc"][AddressMode.absolute], arg)

    def visit_op_adc_absolute_x(self, pos, arg=None):
        return Op(pos, opcode_xref["adc"][AddressMode.absolute_x], arg)

    def visit_op_adc_absolute_y(self, pos, arg=None):
        return Op(pos, opcode_xref["adc"][AddressMode.absolute_y], arg)

    def visit_op_adc_indirect_x(self, pos, arg=None):
        return Op(pos, opcode_xref["adc"][AddressMode.indirect_x], arg)

    def visit_op_adc_indirect_y(self, pos, arg=None):
        return Op(pos, opcode_xref["adc"][AddressMode.indirect_y], arg)

    def visit_op_and_immediate(self, pos, arg=None):
        return Op(pos, opcode_xref["and"][AddressMode.immediate], arg)

    def visit_op_and_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["and"][AddressMode.zeropage], arg)

    def visit_op_and_zeropage_x(self, pos, arg=None):
        return Op(pos, opcode_xref["and"][AddressMode.zeropage_x], arg)

    def visit_op_and_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["and"][AddressMode.absolute], arg)

    def visit_op_and_absolute_x(self, pos, arg=None):
        return Op(pos, opcode_xref["and"][AddressMode.absolute_x], arg)

    def visit_op_and_absolute_y(self, pos, arg=None):
        return Op(pos, opcode_xref["and"][AddressMode.absolute_y], arg)

    def visit_op_and_indirect_x(self, pos, arg=None):
        return Op(pos, opcode_xref["and"][AddressMode.indirect_x], arg)

    def visit_op_and_indirect_y(self, pos, arg=None):
        return Op(pos, opcode_xref["and"][AddressMode.indirect_y], arg)

    def visit_op_asl_accumulator(self, pos, arg=None):
        return Op(pos, opcode_xref["asl"][AddressMode.accumulator], arg)

    def visit_op_asl_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["asl"][AddressMode.zeropage], arg)

    def visit_op_asl_zeropage_x(self, pos, arg=None):
        return Op(pos, opcode_xref["asl"][AddressMode.zeropage_x], arg)

    def visit_op_asl_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["asl"][AddressMode.absolute], arg)

    def visit_op_asl_absolute_x(self, pos, arg=None):
        return Op(pos, opcode_xref["asl"][AddressMode.absolute_x], arg)

    def visit_op_bcc_relative(self, pos, arg=None):
        return Op(pos, opcode_xref["bcc"][AddressMode.relative], arg)

    def visit_op_bcs_relative(self, pos, arg=None):
        return Op(pos, opcode_xref["bcs"][AddressMode.relative], arg)

    def visit_op_beq_relative(self, pos, arg=None):
        return Op(pos, opcode_xref["beq"][AddressMode.relative], arg)

    def visit_op_bit_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["bit"][AddressMode.zeropage], arg)

    def visit_op_bit_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["bit"][AddressMode.absolute], arg)

    def visit_op_bmi_relative(self, pos, arg=None):
        return Op(pos, opcode_xref["bmi"][AddressMode.relative], arg)

    def visit_op_bne_relative(self, pos, arg=None):
        return Op(pos, opcode_xref["bne"][AddressMode.relative], arg)

    def visit_op_bpl_relative(self, pos, arg=None):
        return Op(pos, opcode_xref["bpl"][AddressMode.relative], arg)

    def visit_op_brk_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["brk"][AddressMode.implied], arg)

    def visit_op_bvc_relative(self, pos, arg=None):
        return Op(pos, opcode_xref["bvc"][AddressMode.relative], arg)

    def visit_op_bvc_relative(self, pos, arg=None):
        return Op(pos, opcode_xref["bvc"][AddressMode.relative], arg)

    def visit_op_clc_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["clc"][AddressMode.implied], arg)

    def visit_op_cld_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["cld"][AddressMode.implied], arg)

    def visit_op_cli_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["cli"][AddressMode.implied], arg)

    def visit_op_clv_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["clv"][AddressMode.implied], arg)

    def visit_op_cmp_immediate(self, pos, arg=None):
        return Op(pos, opcode_xref["cmp"][AddressMode.immediate], arg)

    def visit_op_cmp_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["cmp"][AddressMode.zeropage], arg)

    def visit_op_cmp_zeropage_x(self, pos, arg=None):
        return Op(pos, opcode_xref["cmp"][AddressMode.zeropage_x], arg)

    def visit_op_cmp_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["cmp"][AddressMode.absolute], arg)

    def visit_op_cmp_absolute_x(self, pos, arg=None):
        return Op(pos, opcode_xref["cmp"][AddressMode.absolute_x], arg)

    def visit_op_cmp_absolute_y(self, pos, arg=None):
        return Op(pos, opcode_xref["cmp"][AddressMode.absolute_y], arg)

    def visit_op_cmp_indirect_x(self, pos, arg=None):
        return Op(pos, opcode_xref["cmp"][AddressMode.indirect_x], arg)

    def visit_op_cmp_indirect_y(self, pos, arg=None):
        return Op(pos, opcode_xref["cmp"][AddressMode.indirect_y], arg)

    def visit_op_cpx_immediate(self, pos, arg=None):
        return Op(pos, opcode_xref["cpx"][AddressMode.immediate], arg)

    def visit_op_cpx_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["cpx"][AddressMode.zeropage], arg)

    def visit_op_cpx_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["cpx"][AddressMode.absolute], arg)

    def visit_op_cpy_immediate(self, pos, arg=None):
        return Op(pos, opcode_xref["cpy"][AddressMode.immediate], arg)

    def visit_op_cpy_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["cpy"][AddressMode.zeropage], arg)

    def visit_op_cpy_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["cpy"][AddressMode.absolute], arg)

    def visit_op_dec_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["dec"][AddressMode.zeropage], arg)

    def visit_op_dec_zeropage_x(self, pos, arg=None):
        return Op(pos, opcode_xref["dec"][AddressMode.zeropage_x], arg)

    def visit_op_dec_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["dec"][AddressMode.absolute], arg)

    def visit_op_dec_absolute_x(self, pos, arg=None):
        return Op(pos, opcode_xref["dec"][AddressMode.absolute_x], arg)

    def visit_op_dec_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["dec"][AddressMode.implied], arg)

    def visit_op_dec_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["dec"][AddressMode.implied], arg)

    def visit_op_eor_immediate(self, pos, arg=None):
        return Op(pos, opcode_xref["eor"][AddressMode.immediate], arg)

    def visit_op_eor_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["eor"][AddressMode.zeropage], arg)

    def visit_op_eor_zeropage_x(self, pos, arg=None):
        return Op(pos, opcode_xref["eor"][AddressMode.zeropage_x], arg)

    def visit_op_eor_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["eor"][AddressMode.absolute], arg)

    def visit_op_eor_absolute_x(self, pos, arg=None):
        return Op(pos, opcode_xref["eor"][AddressMode.absolute_x], arg)

    def visit_op_eor_absolute_y(self, pos, arg=None):
        return Op(pos, opcode_xref["eor"][AddressMode.absolute_y], arg)

    def visit_op_eor_indirect_x(self, pos, arg=None):
        return Op(pos, opcode_xref["eor"][AddressMode.indirect_x], arg)

    def visit_op_eor_indirect_y(self, pos, arg=None):
        return Op(pos, opcode_xref["eor"][AddressMode.indirect_y], arg)

    def visit_op_inc_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["inc"][AddressMode.zeropage], arg)

    def visit_op_inc_zeropage_x(self, pos, arg=None):
        return Op(pos, opcode_xref["inc"][AddressMode.zeropage_x], arg)

    def visit_op_inc_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["inc"][AddressMode.absolute], arg)

    def visit_op_inc_absolute_x(self, pos, arg=None):
        return Op(pos, opcode_xref["inc"][AddressMode.absolute_x], arg)

    def visit_op_inx_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["inx"][AddressMode.implied], arg)

    def visit_op_iny_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["iny"][AddressMode.implied], arg)

    def visit_op_jmp_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["jmp"][AddressMode.absolute], arg)

    def visit_op_jmp_indirect(self, pos, arg=None):
        return Op(pos, opcode_xref["jmp"][AddressMode.indirect], arg)

    def visit_op_jsr_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["jsr"][AddressMode.absolute], arg)

    def visit_op_lda_immediate(self, pos, arg=None):
        return Op(pos, opcode_xref["lda"][AddressMode.immediate], arg)

    def visit_op_lda_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["lda"][AddressMode.zeropage], arg)

    def visit_op_lda_zeropage_x(self, pos, arg=None):
        return Op(pos, opcode_xref["lda"][AddressMode.zeropage_x], arg)

    def visit_op_lda_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["lda"][AddressMode.absolute], arg)

    def visit_op_lda_absolute_x(self, pos, arg=None):
        return Op(pos, opcode_xref["lda"][AddressMode.absolute_x], arg)

    def visit_op_lda_absolute_y(self, pos, arg=None):
        return Op(pos, opcode_xref["lda"][AddressMode.absolute_y], arg)

    def visit_op_lda_indirect_x(self, pos, arg=None):
        return Op(pos, opcode_xref["lda"][AddressMode.indirect_x], arg)

    def visit_op_lda_indirect_y(self, pos, arg=None):
        return Op(pos, opcode_xref["lda"][AddressMode.indirect_y], arg)

    def visit_op_ldx_immediate(self, pos, arg=None):
        return Op(pos, opcode_xref["ldx"][AddressMode.immediate], arg)

    def visit_op_ldx_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["ldx"][AddressMode.zeropage], arg)

    def visit_op_ldx_zeropage_y(self, pos, arg=None):
        return Op(pos, opcode_xref["ldx"][AddressMode.zeropage_y], arg)

    def visit_op_ldx_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["ldx"][AddressMode.absolute], arg)

    def visit_op_ldx_absolute_y(self, pos, arg=None):
        return Op(pos, opcode_xref["ldx"][AddressMode.absolute_y], arg)

    def visit_op_ldy_immediate(self, pos, arg=None):
        return Op(pos, opcode_xref["ldy"][AddressMode.immediate], arg)

    def visit_op_ldy_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["ldy"][AddressMode.zeropage], arg)

    def visit_op_ldy_zeropage_x(self, pos, arg=None):
        return Op(pos, opcode_xref["ldy"][AddressMode.zeropage_x], arg)

    def visit_op_ldy_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["ldy"][AddressMode.absolute], arg)

    def visit_op_ldy_absolute_x(self, pos, arg=None):
        return Op(pos, opcode_xref["ldy"][AddressMode.absolute_x], arg)

    def visit_op_lsr_accumulator(self, pos, arg=None):
        return Op(pos, opcode_xref["lsr"][AddressMode.accumulator], arg)

    def visit_op_lsr_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["lsr"][AddressMode.zeropage], arg)

    def visit_op_lsr_zeropage_x(self, pos, arg=None):
        return Op(pos, opcode_xref["lsr"][AddressMode.zeropage_x], arg)

    def visit_op_lsr_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["lsr"][AddressMode.absolute], arg)

    def visit_op_lsr_absolute_x(self, pos, arg=None):
        return Op(pos, opcode_xref["lsr"][AddressMode.absolute_x], arg)

    def visit_op_nop_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["nop"][AddressMode.implied], arg)

    def visit_op_ora_immediate(self, pos, arg=None):
        return Op(pos, opcode_xref["ora"][AddressMode.immediate], arg)

    def visit_op_ora_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["ora"][AddressMode.zeropage], arg)

    def visit_op_ora_zeropage_x(self, pos, arg=None):
        return Op(pos, opcode_xref["ora"][AddressMode.zeropage_x], arg)

    def visit_op_ora_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["ora"][AddressMode.absolute], arg)

    def visit_op_ora_absolute_x(self, pos, arg=None):
        return Op(pos, opcode_xref["ora"][AddressMode.absolute_x], arg)

    def visit_op_ora_absolute_y(self, pos, arg=None):
        return Op(pos, opcode_xref["ora"][AddressMode.absolute_y], arg)

    def visit_op_ora_indirect_x(self, pos, arg=None):
        return Op(pos, opcode_xref["ora"][AddressMode.indirect_x], arg)

    def visit_op_ora_indirect_y(self, pos, arg=None):
        return Op(pos, opcode_xref["ora"][AddressMode.indirect_y], arg)

    def visit_op_pha_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["pha"][AddressMode.implied], arg)

    def visit_op_php_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["php"][AddressMode.implied], arg)

    def visit_op_pla_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["pla"][AddressMode.implied], arg)

    def visit_op_plp_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["plp"][AddressMode.implied], arg)

    def visit_op_rol_accumulator(self, pos, arg=None):
        return Op(pos, opcode_xref["rol"][AddressMode.accumulator], arg)

    def visit_op_rol_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["rol"][AddressMode.zeropage], arg)

    def visit_op_rol_zeropage_x(self, pos, arg=None):
        return Op(pos, opcode_xref["rol"][AddressMode.zeropage_x], arg)

    def visit_op_rol_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["rol"][AddressMode.absolute], arg)

    def visit_op_rol_absolute_x(self, pos, arg=None):
        return Op(pos, opcode_xref["rol"][AddressMode.absolute_x], arg)

    def visit_op_ror_accumulator(self, pos, arg=None):
        return Op(pos, opcode_xref["ror"][AddressMode.accumulator], arg)

    def visit_op_ror_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["ror"][AddressMode.zeropage], arg)

    def visit_op_ror_zeropage_x(self, pos, arg=None):
        return Op(pos, opcode_xref["ror"][AddressMode.zeropage_x], arg)

    def visit_op_ror_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["ror"][AddressMode.absolute], arg)

    def visit_op_ror_absolute_x(self, pos, arg=None):
        return Op(pos, opcode_xref["ror"][AddressMode.absolute_x], arg)

    def visit_op_rti_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["rti"][AddressMode.implied], arg)

    def visit_op_rts_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["rts"][AddressMode.implied], arg)

    def visit_op_sbc_immediate(self, pos, arg=None):
        return Op(pos, opcode_xref["sbc"][AddressMode.immediate], arg)

    def visit_op_sbc_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["sbc"][AddressMode.zeropage], arg)

    def visit_op_sbc_zeropage_x(self, pos, arg=None):
        return Op(pos, opcode_xref["sbc"][AddressMode.zeropage_x], arg)

    def visit_op_sbc_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["sbc"][AddressMode.absolute], arg)

    def visit_op_sbc_absolute_x(self, pos, arg=None):
        return Op(pos, opcode_xref["sbc"][AddressMode.absolute_x], arg)

    def visit_op_sbc_absolute_y(self, pos, arg=None):
        return Op(pos, opcode_xref["sbc"][AddressMode.absolute_y], arg)

    def visit_op_sbc_indirect_x(self, pos, arg=None):
        return Op(pos, opcode_xref["sbc"][AddressMode.indirect_x], arg)

    def visit_op_sbc_indirect_y(self, pos, arg=None):
        return Op(pos, opcode_xref["sbc"][AddressMode.indirect_y], arg)

    def visit_op_sec_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["sec"][AddressMode.implied], arg)

    def visit_op_sed_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["sed"][AddressMode.implied], arg)

    def visit_op_sei_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["sei"][AddressMode.implied], arg)

    def visit_op_sta_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["sta"][AddressMode.zeropage], arg)

    def visit_op_sta_zeropage_x(self, pos, arg=None):
        return Op(pos, opcode_xref["sta"][AddressMode.zeropage_x], arg)

    def visit_op_sta_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["sta"][AddressMode.absolute], arg)

    def visit_op_sta_absolute_x(self, pos, arg=None):
        return Op(pos, opcode_xref["sta"][AddressMode.absolute_x], arg)

    def visit_op_sta_absolute_y(self, pos, arg=None):
        return Op(pos, opcode_xref["sta"][AddressMode.absolute_y], arg)

    def visit_op_sta_indirect_x(self, pos, arg=None):
        return Op(pos, opcode_xref["sta"][AddressMode.indirect_x], arg)

    def visit_op_sta_indirect_y(self, pos, arg=None):
        return Op(pos, opcode_xref["sta"][AddressMode.indirect_y], arg)

    def visit_op_stx_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["stx"][AddressMode.zeropage], arg)

    def visit_op_stx_zeropage_y(self, pos, arg=None):
        return Op(pos, opcode_xref["stx"][AddressMode.zeropage_y], arg)

    def visit_op_stx_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["stx"][AddressMode.absolute], arg)

    def visit_op_sty_zeropage(self, pos, arg=None):
        return Op(pos, opcode_xref["sty"][AddressMode.zeropage], arg)

    def visit_op_sty_zeropage_x(self, pos, arg=None):
        return Op(pos, opcode_xref["sty"][AddressMode.zeropage_x], arg)

    def visit_op_sty_absolute(self, pos, arg=None):
        return Op(pos, opcode_xref["sty"][AddressMode.absolute], arg)

    def visit_op_tax_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["tax"][AddressMode.implied], arg)

    def visit_op_tay_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["tay"][AddressMode.implied], arg)

    def visit_op_tsx_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["tsx"][AddressMode.implied], arg)

    def visit_op_txa_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["txa"][AddressMode.implied], arg)

    def visit_op_txs_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["txs"][AddressMode.implied], arg)

    def visit_op_tya_implied(self, pos, arg=None):
        return Op(pos, opcode_xref["tya"][AddressMode.implied], arg)

