from attr import attrib, attrs, Factory
from typing import *
from collections.abc import Iterable
from parsimonious.nodes import Node
from parsimonious.grammar import Grammar
import parsimonious.exceptions as exceptions
import parsimonious.expressions as expressions


@attrs(auto_attribs=True, slots=True)
class Pos(object):
    start: int
    end: int
    context: str = '<internal>'

    @classmethod
    def fromNode(self, node: Node, context=None):
        return Pos(node.start, node.end, context or '<internal>')

    def __repr__(self):
        return f'{self.context}({self.start}:{self.end})'


@attrs(auto_attribs=True, slots=True)
class Token(object):
    pos: Pos
    full_text: str

    @classmethod
    def fromNode(self, node: Node, context=None):
        return Token(Pos.fromNode(node, context=context), node.full_text)

    @classmethod
    def builder(self, full_text, context=None):
        def impl(start, end):
            return Token(Pos(start, end, context or '<internal>'), full_text)
        return impl

    @property
    def text(self):
        return self.full_text[self.pos.start:self.pos.end]


class ParseError(Exception):
    def __init__(self, line, column, context, msg):
        super().__init__(f'{context} ({line}, {column}): {msg}')

    @classmethod
    def fromPos(self, pos, text, msg):
        line = text.count('\n', 0, pos.start) + 1
        try:
            column = pos.start - text.rindex('\n', 0, pos.start)
        except ValueError:
            column = pos.start + 1
        return ParseError(line, column, pos.context, msg)


class ReduceParser(object):
    debug = True

    def __init__(self, grammar_ebnf, unwrapped_exceptions=None):
        '''
        Creates a new parser around the provided arguments.

        The grammar may define a special rule called '__ignored'.  This
        specifies a set of production names that are to be ignored
        in the output tokens.  This is useful for stipping out whitespace
        productions, comments, and other "noisy" filler that otherwise
        makes it hard to process the AST.
        '''

        self.grammar = Grammar(grammar_ebnf)
        self.grammar.unwrapped_exceptions = unwrapped_exceptions or []

    def error(self, line, column, context, msg):
        ''' Raises an exeption around the provided arguments. '''
        raise ParseError(line, column, context, msg)

    def error_generic(self, e):
        ''' Generic hook for handling parsing errors. '''
        name = e.expr.name if e.expr.name else str(e.expr)
        name = name.replace('_', ' ')
        return f'expected {name} expression'

    def parse(self, text, pos=0, context=None, rule=None):
        '''
        Parses a grammar and returns an token tuple.

        Returned nodes are 'flattened' by the visit process built into this
        class.  See visit() for more information.
        '''

        self.context = context or '<internal>'
        parser = self.grammar if not rule else self.grammar[rule]

        try:
            return self.visit(parser.parse(text, pos))
        except exceptions.ParseError as e:
            name = e.expr.name if e.expr.name else str(e.expr)
            fn = getattr(self, f'error_{name}', self.error_generic)
            self.error(e.line(), e.column(), self.context, fn(e))

    def is_ignored_expr(self, name):
        '''
        Returns true if `name` is an ignored expression.
        '''
        try:
            self.grammar['__ignored'].parse(name)
            return True
        except:
            return False

    def visit(self, node):
        '''
        Visits all nodes in the provided node tree, and returns a tuple for the
        given node.

        Literals and Regex expressions are converted to Token instances.  All other
        nodes are discarded and replaced with a stream of child Tokens and the
        output of any custom visit functions.  Optional and productions that
        have zero children are collapsed to no tokens in the output stream.


        Custom visit functions may be added for any expression if they match
        the form of `visit_{node.expr_name}`.  These are passed a position
        argument, and `*args` for all the child tokens at that part of the grammar.
        '''

        if not isinstance(node, Node):
            return node

        if self.debug:
            print(f'ReduceParser(dbg): [{node.expr_name}] type: {type(node.expr)} text: {node.text}')
        values = []
        if isinstance(node.expr, (expressions.Regex, expressions.Literal)):
            values.append(Token.fromNode(node, context=self.context))
        else:
            for n in node.children:
                if self.is_ignored_expr(n.expr_name):
                    continue
                n = self.visit(n)
                if n:
                    if isinstance(n, Iterable):
                        values.extend(n)
                    else:
                        values.append(n)
        fn = getattr(self, f'visit_{node.expr_name}', None)
        if fn:
            return fn(Pos.fromNode(node), *values)
        else:
            return tuple(values)
