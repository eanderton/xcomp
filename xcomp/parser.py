from itertools import chain
from parsimonious.grammar import Grammar, TokenGrammar
from xcomp.model import *
from xcomp.reduce_parser import ReduceParser, Token
from xcomp.cpu6502 import *


grammar = r"""
goal            = (macro / def / core_syntax)*

# TODO: why does adding ws before label fix this?
core_syntax     = comment / byte_storage / word_storage / segment /
                  (_ label) /
                  oper / macro_call / _

comment         = ~r";\s*.*(?=\n|$)"

byte_storage    = byte_tok _ expr _ (comma _ expr _)*
byte_tok        = ".byte"
word_storage    = word_tok _ expr _ (comma _ expr _)*
word_tok        = ".word"

segment         = period segment_name _ number?
segment_name    = "zero" / "text" / "data" / "bss"

include         = include_tok _ string
include_tok     = ".include"

def             = def_tok _ ident _ expr
def_tok         = ".def"

macro           = macro_tok _ macro_params _ macro_body _ endmacro_tok
macro_tok       = ".macro"
endmacro_tok    = ".endmacro"
macro_params    = ident _ (comma _ macro_params _)?
macro_body      = core_syntax*

macro_call      = ident _ macro_args?
macro_args      = expr _ (comma _ expr _)?

label           = ident colon

expr8           = expr
expr16          = expr

# PEMDAS
expr            = sub / add / negate / lobyte / hibyte / term
negate          = minus _ term
lobyte          = lessthan _ term
hibyte          = morethan _ term
add             = term _ plus _ expr
sub             = term _ sub _ expr

term            = div / mul / exp
mul             = exp _ asterisk _ exp
div             = exp _ slash _ exp

exp             = pow / fact
pow             = fact carrot fact
fact            = ident / string / number / group_expr

group_expr      = lparen _ expr _ rparen

string          = quote ((backslash escape_char) / stringchar)* endquote
endquote        = "\""
stringchar      = ~r'[^\\"]+'
escape_char     = 'r' / 'n' / 't' / 'v' / '"' / '\\'

number          =  base2 / base16 / base10
base2           = "%" ~r"[01]{1,16}"
base16          = ~r"\$|0x" ~r"[0-9a-fA-F]{1,4}"
base10          = ~r"(\d+)"

ident           = ~r"[_a-zA-Z][_a-zA-Z0-9]*"

backslash       = "\\"
quote           = "\""
lparen          = "("
rparen          = ")"
plus            = "+"
minus           = "-"
slash           = "/"
carrot          = "^"
pipe            = "|"
ampersand       = "&"
comma           = ","
hash            = "#"
lessthan        = "<"
morethan        = ">"
colon           = ":"
asterisk        = "*"
period          = "."

any             = ~r"."
_               = ~r"\s*"

__ignored       = "comment" / "endquote" /
                  "backslash" / "quote" / "comma" / "hash" / "lparen" / "rparen" /
                  "plus" / "minus" / "slash" / "carrot" / "pipe" / "ampersand" /
                  "comma" / "hash" / "lessthan" / "morethan" / "colon" / "asterisk" /
                  "period" / ~r".*_tok" / "_"
"""


class Parser(ReduceParser):

    def __init__(self):
        super().__init__(grammar_ebnf=grammar)

    def visit_segment(self, pos, name, addr=None):
        return Segment(pos, name.text, addr)

    visit_include = Include

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
        return Storage(pos, 8, exprs)

    def visit_word_storage(self, pos, *exprs):
        return Storage(pos, 16, exprs)

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

    def error_endquote(self, pos):
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

    def visit_base2(self, pos, start, lit):
        return ExprValue(pos, int(lit.text, base=2))

    def visit_base16(self, pos, start, lit):
        return ExprValue(pos, int(lit.text, base=16))

    def visit_base10(self, pos, lit):
        return ExprValue(pos, int(lit.text, base=10))

    ### EXPR ###

    def visit_ident(self, pos, lit):
        return ExprName(pos, lit.text)

    ### OP ###

    def _visit_no_args(self, op, pos, *args):
        print('visit_no_args', op, pos)
        return Op(pos, op)

    def _visit_one_arg(self, op, pos, arg, *args):
        print('visit_one_arg', op, pos, arg)
        return Op(pos, op, arg)

# flag for import-time initializaiton
__setup_complete = False

# amend the module by dynamically building the grammar and parser base class
if not __setup_complete:
    op_names = []
    grammar_parts = []
    opname_tokens = []

    for name in opcode_xref.keys():
        grammar_parts.append(f'{name}_tok = "{name}"')

    for op in opcode_table:
        expr = f'op_{op.name}_{op.mode.name}'
        seq = ' _ '.join([f'_ {op.name}_tok'] + addressmode_params[op.mode])
        op_names.append(expr)
        grammar_parts.append(f'{expr} = {seq}')
        if addressmode_args[op.mode]:
            visit_name = '_visit_one_arg'
        else:
            visit_name = '_visit_no_args'
        fn = partialmethod(getattr(Parser, visit_name), op)
        setattr(Parser, f'visit_{expr}', fn)
    grammar_parts.append('oper = ' + ' / '.join(op_names))
    grammar += '\n'.join(grammar_parts)
