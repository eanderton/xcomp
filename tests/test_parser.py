import unittest
from inspect import cleandoc
from pragma_utils import selfish
from oxeye.exception import ParseError
from xcomp.parser import Parser
from pprint import pprint

from xcomp.lexer import Tok

class TestParser(unittest.TestCase):
    def print_tokens(self, tokens):
        print(tuple([f'{x.name}: {x.value}' for x in tokens]))

    def setUp(self):
        self.maxDiff = None
        self.parser = Parser()
        super().setUp()

    @selfish('parser')
    def tearDown(self, parser):
        print(parser.head, parser._trace)

    @selfish('parser')
    def test_reset(self, parser):
        parser.reset()
        for x in ['.zero', '.text', '.data', '.bss']:
            self.assertEqual(parser.segments[x], parser.name_table[x])
        self.assertEqual(parser._segment, parser.segments['.text'])

    @selfish('parser')
    def test_empty(self, parser):
        parser.parse(cleandoc("""
        """))

    @selfish('parser')
    def test_segments(self, parser):
        parser.parse(cleandoc("""
        .zero
        .text
        .data
        .bss
        """))

    @selfish('parser')
    def test_macro_def(self, parser):
        with self.assertRaises(ParseError, msg='(1, 1) Expected macro name'):
            parser.parse(".macro")

        parser.reset()
        parser.parse(cleandoc("""
        .macro foo()
        .endmacro
        """))


