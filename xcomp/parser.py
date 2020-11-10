from itertools import chain
from parsimonious.grammar import Grammar, TokenGrammar
from xcomp.model import *
from xcomp.grammar import grammar as xcomp_grammar
from xcomp.reduce_parser import ReduceParser, Token
from xcomp.cpu6502 import grammar as cpu6502_grammar
from xcomp.cpu6502 import Cpu6502Visitor


class ParseException(Exception):
    def __init__(self, pos, *args, **kwargs):
        self.pos = pos
        super().__init__(*args, **kwargs)


class Parser(ReduceParser, Cpu6502Visitor):

    def __init__(self):
        super().__init__(grammar_ebnf=xcomp_grammar + cpu6502_grammar,
                unwrapped_exceptions=[ParseException])

    #def visit_goal(self, node, children):
    #    return Program(...)

    def visit_segment(self, pos, name, addr=None):
        return Segment(pos, name.text[1:], addr)

    def visit_include(self, pos, start, filename):
        return Include(pos, filename)

    def visit_def(self, pos, start, name, expr):
        return Macro(pos, name.value, body=[expr])

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
        return Label(pos, name)

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

    def visit_escapechar(self, pos, _, lit):
        value = {
            'r': '\r',
            'n': '\n',
            't': '\t',
            'v': '\v',
            '"': '"',
            '\\': '\\',
        }.get(lit.text, None)
        if value == None:
            raise ParseException(pos, f"Invalid escape sequence '\\{lit.text}'")
        return value

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
