import unittest
from parsimonious.grammar import Grammar
from xcomp.parser import *
from xcomp.reduce_parser import ParseError
from xcomp.model import *


class TestExprContext(ExprContext):
    __test__ = False

    def __init__(self):
        self.names = {}

    def resolve_name(self, label_name):
        return self.names[label_name]

class ParserTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.parser = Parser()
        self.ctx = TestExprContext()

    def parse(self, text, rule):
        result = self.parser.parse(text=text, rule=rule)
        print(result)
        #print(self.parser.grammar)
        return result


class IgnoredTest(ParserTest):
    def test_ws(self):
        result = self.parse('', 'goal')
        self.assertEqual(result, tuple())
        result = self.parse(' ', 'goal')
        self.assertEqual(result, tuple())
        result = self.parse('\n', 'goal')
        self.assertEqual(result, tuple())

    def test_comment(self):
        result = self.parse('''
        ; hello world
        ''', 'goal')
        self.assertEqual(result, tuple())


class SegmentTest(ParserTest):
    def test_segment(self):
        result = self.parse('.text', 'segment')
        self.assertEqual(result.name, 'text')
        self.assertEqual(result.start, None)

    def test_segment_start(self):
        result = self.parse('.data 0x1234', 'segment')
        self.assertEqual(result.name, 'data')
        self.assertEqual(result.start.value, 0x1234)


class LabelTest(ParserTest):
    def test_label(self):
        result = self.parse('foo:', 'label')
        self.assertEqual(result.name, 'foo')

        result = self.parse('foo:', 'core_syntax')
        self.assertEqual(result[0].name, 'foo')

        result = self.parse('''
        start:
        ''', 'goal')
        self.assertEqual(result[0].name, 'start')

class IncludeTest(ParserTest):
    def test_include(self):
        result = self.parse('.include "foobar.asm"', 'include')
        self.assertEqual(result.filename.value, 'foobar.asm')


class DefTest(ParserTest):
    def test_def(self):
        result = self.parse('.def foo bar', 'def')
        self.assertEqual(result.name, 'foo')
        self.assertEqual(result.expr.value, 'bar')



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


class ExprTest(ParserTest):
    def test_negate(self):
        result = self.parse('-42', 'negate')
        self.assertEqual(result, ExprNegate(Pos(0, 3),
            ExprValue(Pos(1, 3), 42),
        ))
        self.assertEqual(result.eval(None), -42)

    def test_add(self):
        result = self.parse('3 + 4', 'add')
        self.assertEqual(result, ExprAdd(Pos(0, 5),
            ExprValue(Pos(0, 1), 3),
            ExprValue(Pos(4, 5), 4),
        ))
        self.assertEqual(result.eval(None), 7)

    def test_lobyte(self):
        result = self.parse('<33', 'lobyte')
        self.assertEqual(result, ExprLobyte(Pos(0, 3),
            ExprValue(Pos(1, 3), 33),
        ))
        result = self.parse('<$33', 'expr')
        self.assertEqual(result[0], ExprLobyte(Pos(0, 4),
            ExprValue(Pos(1, 4), 0x33),
        ))

    def test_mul(self):
        result = self.parse('2 * foo', 'mul')
        self.assertEqual(result, ExprMul(Pos(0, 7),
            ExprValue(Pos(0, 1), 2),
            ExprName(Pos(4, 7), 'foo'),
        ))
        ctx = ExprContext({'foo': 7})
        self.assertEqual(result.eval(ctx), 14)


class StringTest(ParserTest):
    def test_parse_escapechar(self):
        result = self.parse(r'"\n"', 'string')
        self.assertEqual(result.value, "\n")

    def test_parse_escape_error(self):
        with self.assertRaisesRegex(ParseError,
                r"<internal> \(1, 3\): Invalid escape sequence: '\\x'"):
            self.parse(r'"\x"', 'string')

    def test_parse_string(self):
        result = self.parse('"foobar"', 'string')
        self.assertEqual(result.value, 'foobar')

    def test_parse_string_error(self):
        with self.assertRaisesRegex(ParseError,
                r'<internal> \(1, 13\): Expected string end quote \("\)'):
            self.parse(r'"hello world', 'string')


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
            Params(Pos(0, 13), ['foo', 'bar', 'baz']),
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

    def test_macro_call(self):
        result = self.parse('foo', 'macro_call')
        self.assertEqual(result,
            MacroCall(Pos(0, 3), 'foo', Args(Pos(3, 3)))
        )
        result = self.parse('foo $EA', 'macro_call')
        self.assertEqual(result,
            MacroCall(Pos(0, 7), 'foo', Args(Pos(4, 7), [
                ExprValue(Pos(4, 7), 0xEA),
            ]))
        )

    def test_macro_error(self):
        with self.assertRaisesRegex(Exception,
                r"<internal> \(1, 7\): expected macro params"):
            result = self.parse('.macro', 'macro')


