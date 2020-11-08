import unittest
from parsimonious.grammar import Grammar
from xcomp.parser import *
from xcomp.model import *
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
        print(result)
        #print(self.parser.grammar)
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
        self.assertEqual(result,
            Storage(Pos(0, 8), 8, tuple([
                ExprValue(Pos(6, 8), 1)
            ]))
        )

    def test_parse_byte_many(self):
        result = self.parse(".byte 01, 02, 03",'byte_storage')
        self.assertEqual(result,
            Storage(Pos(0, 16), 8, tuple([
                ExprValue(Pos(6,8), 1),
                ExprValue(Pos(10,12), 2),
                ExprValue(Pos(14,16), 3),
            ]))
        )


class StringTest(ParserTest):
    def test_parse_escapechar(self):
        result = self.parse(r'"\n"', 'string')
        self.assertEqual(result.value, "\n")
        with self.assertRaisesRegex(ParseException,
                r"Invalid escape sequence '\\x'"):
            self.parse(r'"\x"', 'string')

    def test_parse_string(self):
        result = self.parse('"foobar"', 'string')
        self.assertEqual(result.value, 'foobar')


class NumberTest(ParserTest):
    def test_parse_base2(self):
        result = self.parse('%101010', 'number')
        self.assertEqual(result[0].value, 0b101010)

    def test_parse_base16(self):
        result = self.parse('0xcafe', 'number')
        self.assertEqual(result[0].value, 0xcafe)

    def test_parse_base10(self):
        result = self.parse('12345', 'number')
        self.assertEqual(result[0].value, 12345)


class MacroTest(ParserTest):
    def test_macro_params(self):
        result = self.parse('one', 'macro_params')
        self.assertEqual(result,
            Params(Pos(0, 3), ['one']),
        )
        result = self.parse('foo, bar, baz', 'macro_params')
        self.assertEqual(result,
            Params(Pos(0, 13, '<internal>'), ['foo', 'bar', 'baz']),
        )

    def test_macro(self):
        result = self.parse(""".macro foo .endmacro""", 'macro')
        self.assertEqual(result.name, 'foo')
        self.assertEqual(result.params, [])
        self.assertEqual(result.body, tuple())
        result = self.parse(""".macro foo, a,b,c
        nop
        .endmacro""", 'macro')
        self.assertEqual(result.name, 'foo')
        self.assertEqual(result.params, ['a','b','c'])
        print('body:', result.body)
        self.assertEqual(len(result.body), 1)
        self.assertEqual(result.body[0].op.name, 'nop')


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


