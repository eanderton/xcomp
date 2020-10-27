from functools import reduce
from pragma_utils import selfish
from xcomp.lexer import Lexer, TokenPrinter
from oxeye.token import Token
from oxeye.testing import *
from pprint import pprint

def doc(text):
    if text.startswith('\n'):
        text = text[1:]
    lines = text.splitlines()
    min_depth = 1000  # arbitrary starting point
    for ln in lines:
        min_depth = min(min_depth, len(ln)-len(ln.lstrip()))
    return '\n'.join([ln[min_depth:] for ln in lines]).rstrip()

class TestLexer(OxeyeTest):
    def setUp(self):
        self.maxDiff = None  # show everything on failure
        self.lexer = Lexer()
        self.printer = TokenPrinter()
        super().setUp()

    def tearDown(self):
        print('output', self.printer._output)
        print('line', self.printer._line)

    def printSource(self, source):
        tokens = self.lexer.parse(source)
        return self.printer.parse(tokens)

    def test_empty(self):
        result = self.printSource(doc("""
        """))
        expected = doc("""
        """)
        self.assertEqual(result, expected)

    def test_data(self):
        result = self.printSource(doc("""
        .byte 0x12, 0x34, 0x56, 0x78
        .word 0x1234, 0x5678
        """))
        expected = doc("""
            .byte 0x12, 0x34, 0x56, 0x78
            .word 0x1234, 0x5678
        """)
        self.assertEqual(result, expected)

    def test_segments(self):
        result = self.printSource(doc("""
        .text .data .zero
        .bss
        """))
        expected = doc("""
            .text
            .data
            .zero
            .bss
        """)
        self.assertEqual(result, expected)

    def test_macro(self):
        result = self.printSource(doc("""
        .macro foo, a, b, c
        lda a
        .endmacro
        """))
        expected = doc("""
        .macro foo, a, b, c
            lda a
        .endmacro
        """)

    def test_const(self):
        result = self.printSource(doc("""
        .const
        a,
        0x1234
        .const
        b,
        0x5678
        """))
        expected = doc("""
        .const a, 0x1234
        .const b, 0x5678
        """)

    def test_print_include(self):
        result = self.printSource(doc("""
        .include
        "foobar.inc"
        .include
        "baz.inc"
        """))
        expected = doc("""
        .include "foobar.inc"
        .include "baz.inc"
        """)

    def test_label(self):
        result = self.printSource(doc("""
        hello: lda #42 world: foobar
        """))
        expected = doc("""
        hello:
            lda #42
        world:
            foobar
        """)
        self.assertEqual(result, expected)
