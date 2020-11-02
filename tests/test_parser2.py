import unittest
from parsimonious.grammar import Grammar
from parsimonious.nodes import Node
from xcomp.parser2 import *
from xcomp.model import *
from xcomp.ast import ast_print
from pragma_utils import selfish


class TestExprContext(ExprContext):
    __test__ = False

    def __init__(self):
        self.names = {}

    def resolve_name(self, label_name):
        return self.names[label_name]


class ParserTest(unittest.TestCase):
    def setUp(self):
        self.parser = Parser()
        self.ctx = TestExprContext()

    def parse(self, text, rule):
        result = self.parser.parse(text=text, rule=rule)
        ast_print(result)
        return result

class SegmentTest(ParserTest):
    def test_segment(self):
        result = self.parse('.text', 'segment')
        self.assertEqual(result.name, 'text')
        self.assertEqual(result.start, None)

    def test_segment_start(self):
        result = self.parse('.data 0x1234', 'segment')
        self.assertEqual(result.name, 'data')
        self.assertEqual(result.start.value, 0x1234)


class IncludeTest(ParserTest):
    def test_include(self):
        result = self.parse('.include "foobar.asm"', 'include')
        self.assertEqual(result.filename.value, 'foobar.asm')


class DefTest(ParserTest):
    def test_def(self):
        result = self.parse('.def foo bar', 'def')
        self.assertEqual(result.name, 'foo')
        self.assertEqual(result.body[0].value, 'bar')



class StorageTest(ParserTest):
    def test_parse_byte(self):
        result = self.parse('.byte 01','byte_storage')
        self.assertEqual(result.width, 8)
        self.assertEqual([x.eval(self.ctx) for x in result.items],
                [1])

    def test_parse_byte_many(self):
        result = self.parse(".byte 01, 02, 03",'byte_storage')
        self.assertEqual(result.width, 8)
        self.assertEqual([x.eval(self.ctx) for x in result.items],
                [1, 2, 3])


class StringTest(ParserTest):
    def test_parse_escapechar(self):
        result = self.parse(r'"\n"', 'string')
        self.assertEqual(result.value, "\n")
        with self.assertRaisesRegex(ParseException, r"Invalid escape sequence '\\x'"):
            self.parse(r'"\x"', 'string')

    def test_parse_string(self):
        result = self.parse('"foobar"', 'string')
        self.assertEqual(result.value, 'foobar')


class NumberTest(ParserTest):
    @selfish('parser')
    def test_parse_base2(self, parser):
        result = self.parse('%101010', 'number')
        self.assertEqual(result.value, 0b101010)

    @selfish('parser')
    def test_parse_base16(self, parser):
        result = self.parse('0xcafe', 'number')
        self.assertEqual(result.value, 0xcafe)

    @selfish('parser')
    def test_parse_base10(self, parser):
        result = self.parse('12345', 'number')
        self.assertEqual(result.value, 12345)


class CompositeTest(unittest.TestCase):
    pass

test_program = """
; hello world
.def foo 0x1234
.macro foo
    nop
.endmacro
nop
"""


