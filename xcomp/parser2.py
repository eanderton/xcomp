from itertools import chain
from parsimonious.grammar import Grammar, TokenGrammar
from xcomp.model import *
from xcomp.ast import ASTParser, ASTNode, Empty


xcomp_grammar = r"""
goal            = (macro / def / core_syntax)*
core_syntax     = comment / byte_storage / word_storage / segment / oper / _

comment         = ~r";\s*.*(?=\n|$)"

byte_storage    = ".byte" _ expr _ (comma _ expr _)*
word_storage    = ".word" _ expr _ (comma _ expr _)*

segment         = segment_name _ number?
segment_name    = ".zero" / ".text" / ".data" / ".bss"

include         = ".include" _ string

def             = ".def" _ ident _ expr

macro           = ".macro" _ macro_params? _ macro_body? _ ".endmacro"
macro_params    = ident _ (comma _ macro_params)?
macro_body      = core_syntax*

oper            = ident _ oper_args?
oper_args       = expr

expr            = ident / number

string          = "\"" (escapechar / stringchar)* "\""
stringchar      = ~r'[^\"]+'
escapechar      = "\\" any

number          =  base2 / base16 / base10
base2           = "%" ~r"[01]{1,16}"
base16          = ~r"\$|0x" ~r"[0-9a-fA-F]{1,4}"
base10          = ~r"(\d+)"

ident           = ~r"[_a-zA-Z][_a-zA-Z0-9]*"

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

any             = ~r"."
_              = ~r"\s*"
"""


class ParseException(Exception):
    def __init__(self, node, *args, **kwargs):
        self.node = node
        super().__init__(*args, **kwargs)

class Parser(ASTParser):

    def __init__(self):
        super().__init__(grammar_ebnf=xcomp_grammar,
                ignored=['_', 'comma', 'comment'],
                unwrapped_exceptions=[ParseException])

    #def visit_goal(self, node, children):
    #    return children

    #def visit_core_syntax(self, node, children):
    #    return children[0]

    def visit_segment(self, node, children):
        name, addr = children
        if addr == Empty:
            addr = None
        return Segment(name.pos, name.text[1:], addr)

    def visit_include(self, node, children):
        start, filename = children
        return Include(start.pos, filename)

    def visit_def(self, node, children):
        start, name, expr = children
        return Macro(start.pos, name.value, body=[expr])

    ### STORAGE ###

    def visit_byte_storage(self, node, children):
        start, first, exprs = children
        return Storage(start.pos, 8, tuple(chain([first], *exprs)))

    def visit_word_storage(self, node, children):
        _, first, exprs = children
        return Storage(node.pos, 16, tuple(chain([first], *exprs)))

    ### STRING ###

    def visit_string(self, node, children):
        start, chars, _ = children
        return String(start.pos, ''.join(chars))

    def visit_stringchar(self, node, children):
        return node.text

    def visit_escapechar(self, node, children):
        _, ch = children
        value = {
            'r': '\r',
            'n': '\n',
            't': '\t',
            'v': '\v',
            '"': '"',
            '\\': '\\',
        }.get(ch.text, None)
        if value == None:
            raise ParseException(ch, f"Invalid escape sequence '\\{ch.text}'")
        return value

    ### NUMBER ###

    def visit_base2(self, node, children):
        start, match = children  # discard prefix
        return ExprValue(start.pos, int(match.text, base=2))

    def visit_base16(self, node, children):
        start, match = children  # discard prefix
        return ExprValue(start.pos, int(match.text, base=16))

    def visit_base10(self, node, children):
        return ExprValue(node.pos, int(node.text, base=10))

    ### EXPR ###

    def visit_ident(self, node, children):
        return ExprName(node.pos, node.text)


class Preprocessor(object): #NodeVisitor):
    def __init__(self):
        self.macros = {}

    def visit_macro(self, node, children):
        print('macro:', node, [x.expr for x in children])
        return node

    def generic_visit(self, node, visited_children):
        ''' lets all other nodes through to output '''
        return node
