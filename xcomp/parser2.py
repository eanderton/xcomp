from collections.abc import Iterable
from itertools import chain
from parsimonious.grammar import Grammar, TokenGrammar
from parsimonious.nodes import NodeVisitor
from parsimonious.expressions import *
from parsimonious.expressions import Optional as OptionalExpr
from parsimonious.expressions import Sequence as SequenceExpr
from xcomp.model import *

xcomp_grammar = r"""
goal            = (macro / def / core_syntax)*
core_syntax     = comment / storage / segment / oper / ws

comment         = ~r";\s*.*(?=\n|$)"

storage         = byte / word
byte            = ".byte" ws expr ws (comma ws expr ws)*
word            = ".word" ws expr ws (comma ws expr ws)*

segment         = (".zero" / ".text" / ".data" / ".bss") number?

include         = ".include" string

def             = ".def" ws ident ws expr
macro           = ".macro" ws macro_params? ws macro_body? ws ".endmacro"
macro_params    = ident ws (comma ws macro_params)?
macro_body      = core_syntax*

oper            = ident ws oper_args?
oper_args       = expr

expr            = (ident / number)

string          = "\"" (escapechar / stringchar)* "\""
stringchar      = ~r'[^\"]'
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
ws              = ~r"\s*"
"""

def query(ctx, productions):
    if isinstance(ctx, Node)
    nodefor x in node.children):


class ParseException(Exception):
    def __init__(self, node, *args, **kwargs):
        self.node = node
        super().__init__(*args, **kwargs)

def promote(value):
    if isinstance(value, Iterable):
        return
    return [value]

def filter_none(fn):
    def impl(self, node, children):
        return fn(self, node, [x for x in children if x is not None])
    return impl

class Cleaner(NodeVisitor):
    unwrapped_exceptions = (ParseException, )

    #def visit_goal(self, node, children):
    #    return children

    #def visit_core_syntax(self, node, children):
    #    return children[0]

    def visit_comment(self, *args):
        return None

    ### STORAGE ###
    def visit_storage(self, node, children):
        return children[0]

    @filter_none
    def visit_byte(self, node, children):
        _, first, values = children
        items = [first]
        for x in values:
            items.append(x[0])
        return Storage(node, 8, items)

    @filter_none
    def visit_word(self, node, children):
        first = children[1]
        values = children[2]
        return Storage(node, 16, [first] + values)

    ### STRING ###

    def visit_escapechar(self, node, children):
        _, ch = children
        value = {
            'r': '\r',
            'n': '\n',
            't': '\t',
            'v': '\v',
            '"': '"',
        }.get(ch.text, None)
        if value == None:
            raise ParseException(node, f"Invalid escape sequence '{ch.text}'")
        return value

    def visit_stringchar(self, node, children):
        return node.text

    def visit_string(self, node, children):
        _, chars, _ = children  # discard delimiters
        return String(node, ''.join(chars))

    ### NUMBER ###

    def visit_number(self, node, children):
        return children[0]

    def visit_base2(self, node, children):
        _, match = children  # discard prefix
        return ExprValue(match, int(match.text, base=2))

    def visit_base16(self, node, children):
        _, match = children  # discard prefix
        return ExprValue(match, int(match.text, base=16))

    def visit_base10(self, node, children):
        return ExprValue(node, int(node.text, base=10))

    ### MISC ###

    def visit_comma(self, *args):
        return None

    def visit_ws(self, *args):
        return None

    def generic_visit(self, node, visited_children):
        ''' filters falsey children out of tree and eliminates useless nodes. '''

        children = [x for x in visited_children if x]
        if isinstance(node.expr, OneOf):
            return children[0]
        elif isinstance(node.expr, ZeroOrMore):
            return children
        elif isinstance(node.expr, OneOrMore):
            return children
        elif isinstance(node.expr, OptionalExpr):
            return children[0] if children else None
        elif isinstance(node.expr, SequenceExpr):
            return children
        else:
            print(f'generic: {type(node.expr)} - {node.expr.name} - {type(node.expr)}')

        node.children = children
        return node

class Preprocessor(NodeVisitor):
    def __init__(self):
        self.macros = {}

    def visit_macro(self, node, children):
        print('macro:', node, [x.expr for x in children])
        return node

    def generic_visit(self, node, visited_children):
        ''' lets all other nodes through to output '''
        return node


class Parser(NodeVisitor):
    def __init__(self):
        self.grammar = Grammar(xcomp_grammar)

    def parse(self, text, rule='goal'):
        ast = self.grammar[rule].parse(text)
        ast = Cleaner().visit(ast)
        #ast = Preprocessor().visit(ast)
        return ast
