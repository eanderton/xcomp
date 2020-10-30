import unittest
from xcomp.parser2 import *
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

    def parse(self, *args, **kwargs):
        return self.parser.parse(*args, **kwargs)


class StorageTest(ParserTest):
    def test_parse_byte(self):
        result = self.parse(".byte 01",'byte')
        self.assertEqual(result.width, 8)
        self.assertEqual([x.eval(self.ctx) for x in result.items],
                [1])

    def test_parse_byte_many(self):
        result = self.parse(".byte 01, 02, 03",'byte')
        self.assertEqual(result.width, 8)
        print('ITEMS', result.items)
        self.assertEqual([x.eval(self.ctx) for x in result.items],
                [1, 2, 3])



class StringTest(ParserTest):
    @selfish('parser')
    def test_parse_stringchar(self, parser):
        result = parser.parse('F','stringchar')
        self.assertEqual(result, "F")

    @selfish('parser')
    def test_parse_escapechar(self, parser):
        result = parser.parse('\\n', 'escapechar')
        self.assertEqual(result, "\n")
        with self.assertRaisesRegex(ParseException, "Invalid escape sequence 'x'"):
            parser.parse('\\x', 'escapechar')

    @selfish('parser')
    def test_parse_string(self, parser):
        result = parser.parse('"foobar"', 'string')
        self.assertEqual(result.value, 'foobar')


class NumberTest(ParserTest):
    @selfish('parser')
    def test_parse_base2(self, parser):
        result = parser.parse('%101010', 'base2')
        self.assertEqual(result.value, 0b101010)

    @selfish('parser')
    def test_parse_base16(self, parser):
        result = parser.parse('0xcafe', 'base16')
        self.assertEqual(result.value, 0xcafe)

    @selfish('parser')
    def test_parse_base10(self, parser):
        result = parser.parse('12345', 'base10')
        self.assertEqual(result.value, 12345)

    @selfish('parser')
    def test_parse_number(self, parser):
        result = parser.parse('%101010', 'number')
        self.assertEqual(result.value, 0b101010)
        result = parser.parse('0xcafe', 'number')
        self.assertEqual(result.value, 0xcafe)
        result = parser.parse('12345', 'number')
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


