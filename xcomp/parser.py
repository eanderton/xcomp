# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

import logging
from .cpu6502 import opcode_xref
from .cpu6502 import AddressMode
from .model import *
from .reduce_parser import ReduceParser
from .reduce_parser import ParseError
from .reduce_parser import Token
from .reduce_parser import TokenList

log = logging.getLogger(__name__)


# TODO: .end token for all scoped decls
# TODO: .struct ?
# TODO: .def call arguments
# TODO: implicit functions for expr

grammar = r"""
goal            = (include / macro / def / core_syntax)*

core_syntax     = comment / byte_storage / word_storage / segment /
                  encoding / scope / endscope / dim / bin / var /
                  pragma / label / oper / macro_call / eol / _

comment         = semi_tok ~r".*(?=\n|$)"
eol             = _ eol_tok

include         = include_tok sp string

def             = def_tok sp name sp expr

byte_storage    = byte_tok sp storage
word_storage    = word_tok sp storage
storage         = expr _ (comma_tok _ expr _)*

segment         = period_tok segment_name (sp expr)?
segment_name    = "zero" / "text" / "data" / "bss"

encoding        = encoding_tok _ string

scope           = scope_tok _
endscope        = endscope_tok _

dim             = dim_tok sp expr _ (comma_tok _ expr)*
bin             = bin_tok sp string

var             = var_tok sp name sp expr _ (comma_tok _ expr)*

pragma          = pragma_tok _ name _ expr

macro           = macro_tok _ macro_params _ macro_body _ endmacro_tok
macro_params    = name _ (comma_tok _ macro_params _)?
macro_body      = core_syntax*

macro_call      = name (sp macro_args)?
macro_args      = expr _ (comma_tok _ expr _)?

label           = ident _ colon_tok
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
scope_tok       = ".scope"
endscope_tok    = ".endscope"
bin_tok         = ".bin"
dim_tok         = ".dim"
var_tok         = ".var"
pragma_tok      = ".pragma"
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
semi_tok        = ";"
asterisk_tok    = "*"
period_tok      = "."
eol_tok         = _ ~r"\n"
_               = ~r"[ \t]*"  # whitespace(s)
sp              = ~r"[ \t]+"  # syntactic space(s)

# 6502 opcode tokens
a_tok           = "a"
x_tok           = "x"
y_tok           = "y"

# 6502 arg modes
arg_acc         = _ a_tok _
arg_imm         = _ hash_tok _ expr
arg_ind         = _ lparen_tok _ expr16 _ rparen_tok
arg_ind_x       = _ lparen_tok _ expr _ comma_tok _ x_tok _ rparen_tok
arg_ind_y       = _ lparen_tok _ expr _ rparen_tok _ comma_tok _ y_tok
arg_zp          = sp expr _
arg_zp_x        = sp expr _ comma_tok _ x_tok
arg_zp_y        = sp expr _ comma_tok _ y_tok
arg_abs         = sp expr16 _
arg_abs_x       = sp expr16 _ comma_tok _ x_tok
arg_abs_y       = sp expr16 _ comma_tok _ y_tok
arg_rel         = sp expr _

# 6502 instructions
op_adc = "adc" (arg_imm / arg_ind_x / arg_ind_y / arg_zp_x / arg_zp / arg_abs_x /
                arg_abs_y / arg_abs)
op_and = "and" (arg_imm / arg_ind_x / arg_ind_y / arg_zp_x / arg_zp / arg_abs_x /
                arg_abs_y / arg_abs)
op_asl = "asl" (arg_acc / arg_zp_x / arg_zp / arg_abs_x / arg_abs)
op_bcc = "bcc" arg_rel
op_bcs = "bcs" arg_rel
op_beq = "beq" arg_rel
op_bit = "bit" (arg_zp / arg_abs)
op_bmi = "bmi" arg_rel
op_bne = "bne" arg_rel
op_bpl = "bpl" arg_rel
op_brk = "brk"
op_bvc = "bvc" arg_rel
op_clc = "clc"
op_cld = "cld"
op_cli = "cli"
op_clv = "clv"
op_cmp = "cmp" (arg_imm / arg_ind_x / arg_ind_y / arg_zp_x / arg_zp / arg_abs_x /
               arg_abs_y / arg_abs)
op_cpx = "cpx" (arg_imm / arg_zp / arg_abs)
op_cpy = "cpy" (arg_imm / arg_zp / arg_abs)
op_dec = "dec" (arg_zp_x / arg_zp / arg_abs_x / arg_abs)?
op_eor = "eor" (arg_imm / arg_ind_x / arg_ind_y / arg_zp_x / arg_zp / arg_abs_x /
                arg_abs_y / arg_abs)
op_inc = "inc" (arg_zp_x / arg_zp / arg_abs_x / arg_abs)
op_inx = "inx"
op_iny = "iny"
op_jmp = "jmp" (arg_ind / arg_abs)
op_jsr = "jsr" arg_abs
op_lda = "lda" (arg_imm / arg_ind_x / arg_ind_y / arg_zp_x / arg_zp / arg_abs_x /
                arg_abs_y / arg_abs)
op_ldx = "ldx" (arg_imm / arg_zp_y / arg_zp / arg_abs_y / arg_abs)
op_ldy = "ldy" (arg_imm / arg_zp_x / arg_zp / arg_abs_x / arg_abs)
op_lsr = "lsr" (arg_acc / arg_zp_x / arg_zp / arg_abs_x / arg_abs)
op_nop = "nop"
op_ora = "ora" (arg_imm / arg_ind_x / arg_ind_y / arg_zp_x / arg_zp / arg_abs_x /
                arg_abs_y / arg_abs)
op_pha = "pha"
op_php = "php"
op_pla = "pla"
op_plp = "plp"
op_rol = "rol" (arg_acc / arg_zp_x / arg_zp / arg_abs_x / arg_abs)
op_ror = "ror" (arg_acc / arg_zp_x / arg_zp / arg_abs_x / arg_abs)
op_rti = "rti"
op_rts = "rts"
op_sbc = "sbc" (arg_imm / arg_ind_x / arg_ind_y / arg_zp_x / arg_zp / arg_abs_x /
                arg_abs_y / arg_abs)
op_sec = "sec"
op_sed = "sed"
op_sei = "sei"
op_sta = "sta" (arg_ind_x / arg_ind_y / arg_zp_x / arg_zp / arg_abs_x / arg_abs_y /
                arg_abs)
op_stx = "stx" (arg_zp_y / arg_zp / arg_abs)
op_sty = "sty" (arg_zp_x / arg_zp / arg_abs)
op_tax = "tax"
op_tay = "tay"
op_tsx = "tsx"
op_txa = "txa"
op_txs = "txs"
op_tya = "tya"

oper = op_adc / op_and / op_asl / op_bcc / op_bcs / op_beq / op_bit / op_bmi /
       op_bne / op_bpl / op_brk / op_bvc / op_clc / op_cld / op_cli / op_clv /
       op_cmp / op_cpx / op_cpy / op_dec / op_eor / op_inc / op_inx / op_iny /
       op_jmp / op_jsr / op_lda / op_ldx / op_ldy / op_lsr / op_nop / op_ora /
       op_pha / op_php / op_pla / op_plp / op_rol / op_ror / op_rti / op_rts /
       op_sbc / op_sec / op_sed / op_sei / op_sta / op_stx / op_sty / op_tax /
       op_tay / op_tsx / op_txa / op_txs / op_tya

__ignored       = ~r".*_tok" / "sp" / "_"
"""


class Parser(ReduceParser):

    def __init__(self):
        super().__init__(grammar=grammar)
        self.last_token = None

    def error_generic(self, e):
        from parsimonious.exceptions import IncompleteParseError
        if isinstance(e, IncompleteParseError):
            return 'Invalid syntax. Expected directive, macro, label, or operation'
        return super().error_generic(e)

    def visit(self, node):
        result = super().visit(node)
        if not isinstance(result, TokenList):
            self.last_token = result
        return result

    def visit_eol(self, pos):
        self.last_token = None

    def visit_comment(self, pos, value):
        full_line = self.last_token is None
        result = Comment(pos, full_line, value.text)
        if not full_line:
            self.last_token.comment = result
            result = None
        self.last_token = None
        return result

    def visit_pragma(self, pos, name, expr):
        return Pragma(pos, name.value, expr)

    def visit_encoding(self, pos, name):
        return Encoding(pos, name.value)

    def visit_segment(self, pos, name, addr=None):
        return Segment(pos, name.text, addr)

    def visit_include(self, pos, filename):
        return Include(pos, filename.value)

    def visit_bin(self, pos, filename):
        return BinaryInclude(pos, filename.value)

    visit_scope = Scope
    visit_endscope = EndScope

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

    def visit_dim(self, pos, length, *exprs):
        return Dim(pos, length, exprs)

    def visit_var(self, pos, name, length, *init):
        return Var(pos, name.value, length, init)

    ### EXPRESSIONS ###

    def visit_def(self, pos, name, expr):
        return Define(pos, name.value, expr)

    def visit_ident(self, pos, lit):
        return ExprName(pos, lit.text)

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

    def visit_string(self, pos, *chars):
        return String(pos, ''.join(chars))

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

    ### OP ###

    def visit_arg_acc(self, pos):
        return AddressMode.accumulator

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
        name = name.text
        return Op(pos, name, mode, opcode_xref[name][mode], arg)
