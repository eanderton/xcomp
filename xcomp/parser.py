from itertools import chain
from parsimonious.grammar import Grammar, TokenGrammar
from xcomp.model import *
from xcomp.reduce_parser import ReduceParser, Token
from xcomp.cpu6502 import *


grammar = r"""
goal            = (macro / def / core_syntax)*
core_syntax     = comment / byte_storage / word_storage / segment /
                  label / oper / macro_call / _

comment         = ~r";\s*.*(?=\n|$)"

byte_storage    = ".byte" _ expr _ (comma _ expr _)*
word_storage    = ".word" _ expr _ (comma _ expr _)*

segment         = segment_name _ number?
segment_name    = ".zero" / ".text" / ".data" / ".bss"

include         = ".include" _ string

def             = ".def" _ ident _ expr

macro           = ".macro" _ macro_params _ macro_body _ ".endmacro"
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

any             = ~r"."
_               = ~r"\s*"

__ignored       = "comment" / "endquote" /
                "backslash" / "quote" / "comma" / "hash" / "lparen" / "rparen" /
                "plus" / "minus" / "slash" / "carrot" / "pipe" / "ampersand" /
                "comma" / "hash" / "lessthan" / "morehtan" / "colon" / "asterisk" /
                "_"
"""


class Parser(ReduceParser):

    def __init__(self):
        super().__init__(grammar_ebnf=grammar)

    def visit_segment(self, pos, name, addr=None):
        return Segment(pos, name.text[1:], addr)

    def visit_include(self, pos, _, filename):
        return Include(pos, filename)

    def visit_def(self, pos, start, name, expr):
        return Define(pos, name.value, expr)

    ### MACRO ###

    def visit_macro(self, pos, start, params, fragment, end):
        name, *params = tuple(params.names)
        print(name, params)
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

    def visit_byte_storage(self, pos, start, *exprs):
        return Storage(pos, 8, exprs)

    def visit_word_storage(self, pos, start, *exprs):
        return Storage(pos, 16, exprs)

    ### EXPRESSIONS ###
    def visit_expr8(self, pos, expr):
        return Expr8(pos, expr)

    def visit_expr16(self, pos, expr):
        return Expr16(pos, expr)

    def visit_negate(self, pos, a):
        return ExprNegate(pos, a)

    def visit_lobyte(self, pos, a):
        return ExprLobyte(pos, a)

    def visit_hibyte(self, pos, a):
        return ExprHibyte(pos, a)

    def visit_add(self, pos, a, b):
        return ExprAdd(pos, a, b)

    def visit_sub(self, pos, a, b):
        return ExprSub(pos, a, b)

    def visit_mul(self, pos, a, b):
        return ExprMul(pos, a, b)

    def visit_div(self, pos, a, b):
        return ExprDiv(pos, a, b)

    def visit_pow(self, pos, a, b):
        return ExprPow(pos, a, b)

    ### STRING ###

    def visit_string(self, pos, *chars):
        return String(pos, ''.join(chars))

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
        return Op(pos, op)

    def _visit_one_arg(self, op, pos, opname, arg):
        return Op(pos, op, arg)


# flag for import-time initializaiton
__setup_complete = False

# amend the module by dynamically building the grammar and parser base class
if not __setup_complete:
    op_names = []
    grammar_parts = []
    for op in opcode_table:
        expr = f'op_{op.name}_{op.mode.name}'
        seq = ' _ '.join([f'"{op.name}"'] + addressmode_params[op.mode])
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
