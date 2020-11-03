import unittest
from xcomp.ast import *


class TestParser(ASTParser):
    __test__ = False

    def __init__(self):
        super().__init__(r"""
        goal  = _ (alpha / beta / gamma) _
        alpha = "hello"
        beta  = "world"
        gamma = "goat"
        _    = ~r"\s*"

        calc = _ expr _

        # PEMDAS
        expr = sub / add / negate / term
        negate = "-" _ term
        add = term _ "+" _ expr
        sub = term _ "-" _ expr

        term =  div / mul / exp
        mul = exp _ "*" _ exp
        div = exp _ "/" _ exp

        exp = pow / fact
        pow = fact "^" fact
        fact = value / group_expr

        group_expr = "(" _ expr _ ")"

        value = ~r"\d+"
        """, ignored=["_"])

    def visit_group_expr(self, node, children):
        return children[1]


class TestAST(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.maxDiff = True
        super().__init__(*args, **kwargs)

    def setUp(self):
        self.parser = TestParser()

    def parse(self, text, rule='goal'):
        ast = self.parser.parse(text=text, rule=rule)
        ast_print(ast)
        return ast

    def node(self, name, full_text, start, end, children=None):
        return ASTNode(name, Pos(start, end), full_text, children)

    def test_simple_literal(self):
        full_text="hello"
        self.assertEqual(self.parse(full_text, 'goal'), (
            self.node('alpha', full_text, 0, 5),
        ))

    def test_visit_value(self):
        full_text="world"
        self.assertEqual(self.parse(full_text, 'goal'), (
            self.node('beta', full_text, 0, 5),
        ))

    def test_negate(self):
        full_text="-5"
        self.assertEqual(self.parse(full_text, 'expr'), (
            self.node('literal', full_text, 0, 1),
            self.node('value', full_text, 1, 2),
        ))

    def test_add(self):
        full_text="3+2"
        self.assertEqual(self.parse(full_text, 'expr'), (
            self.node('value', full_text, 0, 1),
            self.node('literal', full_text, 1, 2),
            self.node('value', full_text, 2, 3),
        ))

    def test_mul(self):
        full_text="3*2"
        self.assertEqual(self.parse(full_text, 'expr'), (
            self.node('value', full_text, 0, 1),
            self.node('literal', full_text, 1, 2),
            self.node('value', full_text, 2, 3),
        ))

    def test_group(self):
        full_text="(3*2)"
        self.assertEqual(self.parse(full_text, 'expr'), (
            self.node('value', full_text, 1, 2),
            self.node('literal', full_text, 2, 3),
            self.node('value', full_text, 3, 4),
        ))

    def test_complex(self):
        full_text="(3*2+7/2-12)"
        self.assertEqual(self.parse(full_text, 'expr'), (
            (
                self.node('value', full_text, 1, 2),
                self.node('literal', full_text, 2, 3),
                self.node('value', full_text, 3, 4),
            ),
            self.node('literal', full_text, 4, 5),
            (
                (
                    self.node('value', full_text, 5, 6),
                    self.node('literal', full_text, 6, 7),
                    self.node('value', full_text, 7, 8),
                ),
                self.node('literal', full_text, 8, 9),
                self.node('value', full_text, 9, 11),
            ),
        ))
