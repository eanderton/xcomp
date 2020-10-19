from inspect import cleandoc
from pragma_utils import selfish
from xcomp.lexer import Lexer
from oxeye.token import Token
from oxeye.testing import *
from pprint import pprint

class TestLexer(OxeyeTest):
    def setUp(self):
        self.maxDiff = None  # show everything on failure
        self.lexer = Lexer()
        super().setUp()
        pprint(self.lexer.spec)

    @selfish('lexer')
    def test_lex_comment(self, lexer):
        lexer.parse(cleandoc("""
        ; comment one
        ; comment two
        """))
        expected = [
            Token('comment', ' comment one', 1, 1),
            Token('comment', ' comment two', 2, 1),
        ]
        print('tok 0:', lexer._tokens[0].value)
        print('tok 1:', lexer._tokens[1].value)
        self.assertEqual(lexer._tokens, expected)

    @selfish('lexer')
    def test_lex_number(self, lexer):
        lexer.parse(' 10 22.56')
        expected = [
            Token('number', 10, 1, 2),
            Token('number', 22.56, 1, 3),
        ]
        self.assertEqual(lexer._tokens, expected)

    @selfish('lexer')
    def test_lex_hex(self, lexer):
        lexer.parse('0x10 0xface $42 $babe')
        expected = [
            Token('number', 0x10, 1, 1),
            Token('number', 0xface, 1, 6),
            Token('number', 0x42, 1, 13),
            Token('number', 0xbabe, 1, 18),
        ]
        self.assertEqual(lexer._tokens, expected)

    @selfish('lexer')
    def test_lex_dots(self, lexer):
        lexer.parse('\n'.join([
        '.byte',
        '.word',
        '.zero',
        '.text',
        '.data',
        '.bss',
        '.macro',
        '.endmacro',
        ]))
        expected = [
            Token('.byte', '.byte', 1, 1),
            Token('.word', '.word', 2, 1),
            Token('segment', '.zero', 3, 1),
            Token('segment', '.text', 4, 1),
            Token('segment', '.data', 5, 1),
            Token('segment', '.bss', 6, 1),
            Token('.macro', '.macro', 7, 1),
            Token('.endmacro', '.endmacro', 8, 1),
        ]
        self.assertEqual(lexer._tokens, expected)

    @selfish('lexer')
    def test_lex_symbols(self, lexer):
        lexer.parse('- +\n*)(')
        expected = [
            Token('-', '-', 1, 1),
            Token('+', '+', 1, 9),
            Token('*', '*', 2, 1),
            Token(')', ')', 2, 2),
            Token('(', '(', 2, 3),
        ]
        self.assertEqual(lexer.tokens, expected)
        self.assertEqual(lexer.line, 2)
        self.assertEqual(lexer.column, 4)
        self.assertEqual(lexer.pos, 7)

    @selfish('lexer')
    def test_lex_string(self, lexer):
        lexer.parse('"hello world"')
        expected = [
            Token('string', 'hello world', 1, 1)
        ]
        self.assertEqual(lexer.tokens, expected)

    @selfish('lexer')
    def test_lex_symbols(self, lexer):
        lexer.parse('- +\n*)(')
        expected = [
            Token('-', '-', 1, 1),
            Token('+', '+', 1, 9),
            Token('*', '*', 2, 1),
            Token(')', ')', 2, 2),
            Token('(', '(', 2, 3),
        ]
        self.assertEqual(lexer.tokens, expected)

    @selfish('lexer')
    def test_lex_macro_decl(self, lexer):
        lexer.parse(cleandoc("""
        .macro foo()
        .endmacro
        """))
        expected = [
            Token('.macro', '.macro', 2, 1),
            Token('ident', 'foo', 2, 8),
            Token('(', '(', 2, 9),
            Token(')', ')', 2, 10),
            Token('.endmacro', '.endmacro', 3, 1),
        ]
        self.assertEqual(lexer.tokens, expected)
