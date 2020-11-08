from itertools import chain
from parsimonious.grammar import Grammar, TokenGrammar
from xcomp.model import *
from xcomp.grammar import grammar as xcomp_grammar
from xcomp.flat_ast import ReduceParser, Token
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
        return Params(pos, [param.value] + rest) #x.value for x in params])

    def visit_macro_body(self, pos, *body):
        return Fragment(pos, body)

    ### STORAGE ###

    def visit_byte_storage(self, pos, start, *exprs):
        return Storage(pos, 8, exprs)

    def visit_word_storage(self, pos, start, *exprs):
        return Storage(pos, 16, exprs)

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
