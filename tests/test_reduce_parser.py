import unittest
from xcomp.reduce_parser import *


unittest.TestCase.maxDiff = True

class TestParser(ReduceParser):
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

        group_expr = lparen _ expr _ rparen
        lparen = "("
        rparen = ")"
        value = ~r"\d+"

        __ignored = "_" / "lparen" / "rparen"
        """)

    def visit_group_expr(self, pos, *children):
        expr = [x.text for x in children]
        return ['group expression: ' + ' '.join(expr)]


class TestReduceParser(unittest.TestCase):
    def setUp(self):
        self.parser = TestParser()

    def parse(self, text, rule='goal'):
        tokens = self.parser.parse(text=text, rule=rule)
        print(tokens)
        self.tok = Token.builder(text)
        return tokens

    def tok(self, full_text, start, end):
        return Token(Pos(start, end), full_text)

    def test_simple_literal(self):
        full_text='hello'
        self.assertEqual(self.parse(full_text, 'goal'), [
            self.tok(0, 5),
        ])
        full_text='world'
        self.assertEqual(self.parse(full_text, 'goal'), [
            self.tok(0, 5),
        ])

    def test_token_stream(self):
        full_text='1 + 3'
        self.assertEqual(self.parse(full_text, 'expr'), [
            self.tok(0, 1),
            self.tok(2, 3),
            self.tok(4, 5),
        ])

    def test_group(self):
        full_text="(3*2)"
        self.assertEqual(self.parse(full_text, 'expr'), [[
            'group expression: 3 * 2',
        ]])
