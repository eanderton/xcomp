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

segment         = segment_name ws number?
segment_name    = ".zero" / ".text" / ".data" / ".bss"

include         = ".include" ws string

def             = ".def" ws ident ws expr

macro           = ".macro" ws macro_params? ws macro_body? ws ".endmacro"
macro_params    = ident ws (comma ws macro_params)?
macro_body      = core_syntax*

oper            = ident ws oper_args?
oper_args       = expr

expr            = ident / number

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


def query(ctx, *productions):
    if isinstance(ctx, list):
        for x in ctx:
            for y in query(x, *productions):
                yield y
    elif isinstance(ctx, Node):
        for p in productions:
            if isinstance(p, str) and ctx.expr_name == p:
                yield ctx
            elif isinstance(p, type) and isinstance(ctx, p):
                print('Q', p, type(ctx))
                yield ctx
            elif hasattr(ctx, 'children'):
                for x in ctx.children:
                    for y in query(x, *productions):
                        yield y
    else:
        for p in productions:
            if isinstance(p, type) and isinstance(ctx, p):
                print('Q', p, type(ctx))
                yield ctx


def query_one(ctx, *productions):
    result = tuple(query(ctx, *productions))
    if len(result) == 1:
        return result[0]
    return None


def dbg(ctx, indent=0):
    pre = ' '*indent
    if isinstance(ctx, list) or isinstance(ctx, tuple):
        print(pre, '[', len(ctx))
        for x in ctx:
            dbg(x, indent+2)
        print(pre, ']')
    elif isinstance(ctx, Node):
        print(pre, 'Node:', ctx.expr_name, ctx.text, '[')
        for x in ctx.children:
            dbg(x, indent+2)
        print(pre, ']')
    else:
        print(pre, ctx)


class ParseException(Exception):
    def __init__(self, node, *args, **kwargs):
        self.node = node
        super().__init__(*args, **kwargs)


class Cleaner(NodeVisitor):
    unwrapped_exceptions = (ParseException, )

    #def visit_goal(self, node, children):
    #    return children

    #def visit_core_syntax(self, node, children):
    #    return children[0]

    def visit_comment(self, *args):
        return None

    def visit_segment(self, node, children):
        name = query_one(children, 'segment_name')
        start = query_one(children, ExprValue)
        print(name, start)
        return Segment(node, name.text[1:], start)

    def visit_include(self, node, children):
        filename = query_one(children, String)
        return Include(node, filename)

    def visit_def(self, node, children):
        #print(node)
        q = query(children, Expr)

        #print(name, body)
        #return Macro(node, name.value, body=[body])

    ### STORAGE ###

    def visit_storage(self, node, children):
        return children[0]

    def visit_byte(self, node, children):
        return Storage(node, 8, tuple([v for v in query(children, ExprValue)]))

    def visit_word(self, node, children):
        return Storage(node, 16, tuple([v for v in query(children, ExprValue)]))

    ### STRING ###

    def visit_string(self, node, children):
        text = ''
        for v in query(node, 'stringchar', 'escapechar'):
            if v.text[0] == '\\':
                value = {
                    r'\r': '\r',
                    r'\n': '\n',
                    r'\t': '\t',
                    r'\v': '\v',
                    r'\"': '"',
                    r'\\': '\\',
                }.get(v.text, None)
                if value == None:
                    raise ParseException(node, f"Invalid escape sequence '{v.text}'")
                text += value
            else:
                text += v.text
        return String(node, text)

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

    ### EXPR ###

    def visit_ident(self, node, children):
        return ExprName(node, node.text)


    ### MISC ###

    def generic_visit(self, node, visited_children):
        if node.children != visited_children:
            return Node(node.expr, node.full_text, node.start, node.end, visited_children)
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
