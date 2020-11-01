from attr import attrib, attrs, Factory
from typing import *
from parsimonious.nodes import Node
from parsimonious.grammar import Grammar
import parsimonious.expressions as expressions


@attrs(auto_attribs=True)
class ASTNode(object):
    name: str
    full_text: str
    start: int
    end: int
    context: str = '<internal>'
    children: List = Factory(list)

    #value: Any = None

    @classmethod
    def fromNode(self, node: Node, name=None, context=None, children=None):
        return ASTNode(name=name or node.expr_name,
                full_text=node.full_text,
                start=node.start,
                end=node.end,
                context=context or '<internal>',
                children=children or [])

    @property
    def text(self):
        return self.full_text[self.start:self.end]

    def __str__(self):
        return f'{self.name} {self.context}({self.start}:{self.end}) {self.text}'


Empty = ASTNode('empty', '', 0, 0)


def ast_print(root, indent=0):
    pre = ' '*indent
    if isinstance(root, ASTNode):
        if root.children:
            print(pre, str(root), '[')
            for c in root.children:
                ast_print(c, indent+2)
            print(pre, ']')
        else:
            print(pre, str(root))
    elif isinstance(root, tuple):
        print(pre, '[')
        for c in root:
            ast_print(c, indent+2)
        print(pre, ']')
    else:
        print(pre, str(root))


class ASTParser(object):
    def __init__(self, grammar_ebnf, ignored=None):
        self.grammar = Grammar(grammar_ebnf)
        self.ignored = ignored or []

    def parse(self, text, pos=0, context=None, rule=None):
        self.context = context or '<internal>'
        parser = self.grammar[rule] if rule else self.default_rule
        return self.visit(parser.parse(text, pos))

    def visit(self, node):
        '''
        Flattens the upstream node tree as a heterogenous AST.

        The tree is condensed into expression nodes, terminals, and customized
        visitor output.  Transforms are applied to all nodes to flatten the
        standard Node tree, in order to make the parse result easier to
        traverse.

        - The ASTNode type is used to wrap all the Parsimonious Nodes to enable
          easier tree traveersals, searches, and processing.
        - Literals and Regex expressions are both named 'literal' when used
          anonymously.  If either is the only expression for a rule, it adopts the
          name of the rule.
        - OneOf, Not, Optional, are replaced with the first matched child, or
          the Empty singleton ASTNode
        - Lookahead nodes are discarded.
        - Sequence, OneOrMore, and ZeroOrMore nodes are replaced by their
          children list.
        - If any expression name is in self.ignored, it is not visited and not
          included in any forwarded children.
        - If any visit function returns None, that value is discarded and
          not present in any forwarded children.

        Custom visit functions may be added for any expression if they match
        the form of `visit_{node.expr_name}`.
        '''

        if isinstance(node, Node):
            fn = getattr(self, f'visit_{node.expr_name}', self.generic_visit)
            children = [self.visit(n) for n in node.children if n.expr_name not in self.ignored]
            children = [n for n in children if n is not None]
            return fn(node, tuple(children))
        return node

    def generic_visit(self, node, children):
        ''' Generic visitor that provides flattening logic for visit(). '''

        print(f'[{node.expr_name}]', type(node.expr), node.text)
        expr = node.expr
        if isinstance(expr, expressions.Lookahead):
            return None
        if isinstance(expr, (expressions.OneOf, expressions.Not, expressions.Optional)):
            return children[0] if children else Empty
        if isinstance(expr, (expressions.Sequence, expressions.ZeroOrMore, expressions.OneOrMore)):
            return children
        if isinstance(expr, (expressions.Regex, expressions.Literal)):
            name = node.expr_name or 'literal'
            return ASTNode.fromNode(node, name=name, context=self.context)
        return ASTNode.fromNode(node, context=self.context, children=children)
