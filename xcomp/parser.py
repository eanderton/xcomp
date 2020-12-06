from .model import *
from .reduce_parser import ReduceParser
from .reduce_parser import Token
from .reduce_parser import TokenList
from .cpu6502 import *

# TODO: collapse repetition of op parsing into something more sane
# TODO: add scope/endscope
# TODO: add .bin <filename> for direct binary include
# TODO: add .pragma name <expr> for arbitrary metadata

grammar = r"""
goal            = (include / macro / def / core_syntax)*

core_syntax     = comment / byte_storage / word_storage / segment /
                  encoding / (_ label) / oper / macro_call / _

comment         = ~r";\s*.*(?=\n|$)"

include         = include_tok _ string

def             = def_tok _ name _ expr

byte_storage    = byte_tok _ storage
word_storage    = word_tok _ storage
storage         = expr _ (comma_tok _ expr _)*

segment         = period_tok segment_name _ expr?
segment_name    = "zero" / "text" / "data" / "bss"

encoding        = encoding_tok _ string

macro           = macro_tok _ macro_params _ macro_body _ endmacro_tok
macro_params    = name _ (comma_tok _ macro_params _)?
macro_body      = core_syntax*

macro_call      = name _ macro_args?
macro_args      = expr _ (comma_tok _ expr _)?

label           = ident colon_tok
name            = ident !colon_tok

#expr16          = bang_tok expr
expr16          = (bang_tok expr) / expr

expr            = sub / add / or / and / negate / lobyte / hibyte / term
negate          = minus_tok _ term
lobyte          = lessthan_tok _ term
hibyte          = morethan_tok _ term
add             = term _ plus_tok _ expr
sub             = term _ minus_tok _ expr
or              = term _ pipe_tok _ expr
and             = term _ ampersand_tok _ expr

term            = div / mul / exp
mul             = exp _ asterisk_tok _ exp
div             = exp _ slash_tok _ exp

exp             = pow / fact
pow             = fact carrot_tok fact
fact            = name / string / number / group_expr

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
encoding_tok    = ".encoding"
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

# 6502 arg modes
arg_acc         = a_tok _
arg_imm         = hash_tok _ expr
arg_ind         = lparen_tok _ expr16 _ rparen_tok
arg_ind_x       = lparen_tok _ expr _ comma_tok _ x_tok _ rparen_tok
arg_ind_y       = lparen_tok _ expr _ rparen_tok _ comma_tok _ y_tok
arg_zp          = expr _
arg_zp_x        = expr _ comma_tok _ x_tok
arg_zp_y        = expr _ comma_tok _ y_tok
arg_abs         = expr16 _
arg_abs_x       = expr16 _ comma_tok _ x_tok
arg_abs_y       = expr16 _ comma_tok _ y_tok
arg_rel         = expr _

# 6502 instructions
op_adc = "adc" _ (arg_imm / arg_ind_x / arg_ind_y / arg_zp_x / arg_zp / arg_abs_x / arg_abs_y / arg_abs)
op_and = "and" _ (arg_imm / arg_ind_x / arg_ind_y / arg_zp_x / arg_zp / arg_abs_x / arg_abs_y / arg_abs)
op_asl = "asl" _ (arg_acc / arg_zp_x / arg_zp / arg_abs_x / arg_abs)
op_bcc = "bcc" _ (arg_rel)
op_bcs = "bcs" _ (arg_rel)
op_beq = "beq" _ (arg_rel)
op_bit = "bit" _ (arg_zp / arg_abs)
op_bmi = "bmi" _ (arg_rel)
op_bne = "bne" _ (arg_rel)
op_bpl = "bpl" _ (arg_rel)
op_brk = "brk" _
op_bvc = "bvc" _ (arg_rel)
op_clc = "clc" _
op_cld = "cld" _
op_cli = "cli" _
op_clv = "clv" _
op_cmp = "cmp" _ (arg_imm / arg_ind_x / arg_ind_y / arg_zp_x / arg_zp / arg_abs_x / arg_abs_y / arg_abs)
op_cpx = "cpx" _ (arg_imm / arg_zp / arg_abs)
op_cpy = "cpy" _ (arg_imm / arg_zp / arg_abs)
op_dec = "dec" _ (arg_zp_x / arg_zp / arg_abs_x / arg_abs)?
op_eor = "eor" _ (arg_imm / arg_ind_x / arg_ind_y / arg_zp_x / arg_zp / arg_abs_x / arg_abs_y / arg_abs)
op_inc = "inc" _ (arg_zp_x / arg_zp / arg_abs_x / arg_abs)
op_inx = "inx" _
op_iny = "iny" _
op_jmp = "jmp" _ (arg_ind / arg_abs)
op_jsr = "jsr" _ (arg_abs)
op_lda = "lda" _ (arg_imm / arg_ind_x / arg_ind_y / arg_zp_x / arg_zp / arg_abs_x / arg_abs_y / arg_abs)
op_ldx = "ldx" _ (arg_imm / arg_zp_y / arg_zp / arg_abs_y / arg_abs)
op_ldy = "ldy" _ (arg_imm / arg_zp_x / arg_zp / arg_abs_x / arg_abs)
op_lsr = "lsr" _ (arg_acc / arg_zp_x / arg_zp / arg_abs_x / arg_abs)
op_nop = "nop" _
op_ora = "ora" _ (arg_imm / arg_ind_x / arg_ind_y / arg_zp_x / arg_zp / arg_abs_x / arg_abs_y / arg_abs)
op_pha = "pha" _
op_php = "php" _
op_pla = "pla" _
op_plp = "plp" _
op_rol = "rol" _ (arg_acc / arg_zp_x / arg_zp / arg_abs_x / arg_abs)
op_ror = "ror" _ (arg_acc / arg_zp_x / arg_zp / arg_abs_x / arg_abs)
op_rti = "rti" _
op_rts = "rts" _
op_sbc = "sbc" _ (arg_imm / arg_ind_x / arg_ind_y / arg_zp_x / arg_zp / arg_abs_x / arg_abs_y / arg_abs)
op_sec = "sec" _
op_sed = "sed" _
op_sei = "sei" _
op_sta = "sta" _ (arg_ind_x / arg_ind_y / arg_zp_x / arg_zp / arg_abs_x / arg_abs_y / arg_abs)
op_stx = "stx" _ (arg_zp_y / arg_zp / arg_abs)
op_sty = "sty" _ (arg_zp_x / arg_zp / arg_abs)
op_tax = "tax" _
op_tay = "tay" _
op_tsx = "tsx" _
op_txa = "txa" _
op_txs = "txs" _
op_tya = "tya" _

oper = op_adc / op_and / op_asl / op_bcc / op_bcs / op_beq / op_bit / op_bmi / op_bne / op_bpl / op_brk / op_bvc / op_clc / op_cld / op_cli / op_clv / op_cmp / op_cpx / op_cpy / op_dec / op_eor / op_inc / op_inx / op_iny / op_jmp / op_jsr / op_lda / op_ldx / op_ldy / op_lsr / op_nop / op_ora / op_pha / op_php / op_pla / op_plp / op_rol / op_ror / op_rti / op_rts / op_sbc / op_sec / op_sed / op_sei / op_sta / op_stx / op_sty / op_tax / op_tay / op_tsx / op_txa / op_txs / op_tya

__ignored       = "comment" / ~r".*_tok" / "_"
"""


class Parser(ReduceParser):

    def __init__(self):
        super().__init__(grammar=grammar)

    def error_generic(self, e):
        from parsimonious.exceptions import IncompleteParseError
        if isinstance(e, IncompleteParseError):
            return 'Invalid syntax. Expected directive, macro, label, or operation'
        return super().error_generic(e)

    def visit_encoding(self, pos, name):
        return Encoding(pos, name.value)

    def visit_segment(self, pos, name, addr=None):
        return Segment(pos, name.text, addr)

    def visit_include(self, pos, filename):
        return Include(pos, filename.value)

    def visit_def(self, pos, name, expr):
        return Define(pos, name.value, expr)

    ### MACRO ###

    def visit_macro(self, pos, name, *args):
        params = tuple([x.value for x in args[:-1]])
        fragment = args[-1]
        return Macro(pos, name.value, params, fragment.body)

    def visit_macro_body(self, pos, *body):
        return Fragment(pos, body)

    def visit_label(self, pos, name):
        return Label(pos, name.value)

    def visit_macro_call(self, pos, name, *args):
        return MacroCall(pos, name.value, args)

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
    visit_or = ExprOr
    visit_and = ExprAnd
    visit_div = ExprDiv
    visit_mul = ExprMul

    ### STRING ###

    visit_string = String

    def visit_stringchar(self, pos, lit):
        return lit.text

    def error_endquote_tok(self, e):
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

    ### OP ###

    def visit_arg_acc(self, pos, arg):
        return TokenList([AddressMode.accumulator, arg])

    def visit_arg_imm(self, pos, arg):
        return TokenList([AddressMode.immediate, arg])

    def visit_arg_ind(self, pos, arg):
        return TokenList([AddressMode.indirect, arg])

    def visit_arg_ind_x(self, pos, arg):
        return TokenList([AddressMode.indirect_x, arg])

    def visit_arg_ind_y(self, pos, arg):
        return TokenList([AddressMode.indirect_y, arg])

    def visit_arg_zp(self, pos, arg):
        return TokenList([AddressMode.zeropage, arg])

    def visit_arg_zp_x(self, pos, arg):
        return TokenList([AddressMode.zeropage_x, arg])

    def visit_arg_zp_y(self, pos, arg):
        return TokenList([AddressMode.zeropage_y, arg])

    def visit_arg_abs(self, pos, arg):
        return TokenList([AddressMode.absolute, arg])

    def visit_arg_abs_x(self, pos, arg):
        return TokenList([AddressMode.absolute_x, arg])

    def visit_arg_abs_y(self, pos, arg):
        return TokenList([AddressMode.absolute_y, arg])

    def visit_arg_rel(self, pos, arg):
        return TokenList([AddressMode.relative, arg])

    def visit_oper(self, pos, name, mode=AddressMode.implied, arg=None):
        return Op(pos, opcode_xref[name.text][mode], arg)
