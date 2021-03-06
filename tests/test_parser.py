# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

import logging
import unittest
from xcomp.parser import *
from xcomp.model import *
#from xcomp.reduce_parser import ParseError
from xcomp.cpu6502 import AddressMode

logging.getLogger('xcomp.reduce_parser').setLevel(logging.DEBUG)
logging.getLogger('xcomp.parser').setLevel(logging.DEBUG)


class ParserTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.parser = Parser()

    def parse(self, text, rule='goal'):
        result = self.parser.parse(text=text, rule=rule)
        print(result)
        return result


class IgnoredTest(ParserTest):
    def test_ws(self):
        result = self.parse('', 'goal')
        self.assertEqual(result, [])
        result = self.parse(' ', 'goal')
        self.assertEqual(result, [])
        result = self.parse('\n', 'goal')
        self.assertEqual(result, [])


class StatementSeparatorTest(ParserTest):
    def test_sep_newline(self):
        # test two back-to-back macro calls
        result = self.parse('foo\nbar')
        self.assertEqual(result, [
            MacroCall(Pos(0, 3), 'foo', tuple()),
            MacroCall(Pos(4, 7), 'bar', tuple()),
        ])

class EncodingTest(ParserTest):
    def test_encoding(self):
        result = self.parse('.encoding "foo"', 'encoding')
        self.assertEqual(result.name, 'foo')


class SegmentTest(ParserTest):
    def test_segment(self):
        result = self.parse('.text', 'segment')
        self.assertEqual(result.name, 'text')
        self.assertEqual(result.start, None)

    def test_segment_start(self):
        result = self.parse('.data 0x1234', 'segment')
        self.assertEqual(result.name, 'data')
        self.assertEqual(result.start.value, 0x1234)

    def test_segment_with_label(self):
        result = self.parse('.data foo:', 'goal')
        self.assertEqual(result[0].name, 'data')


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
        self.assertEqual(result.filename, 'foobar.asm')


class DefTest(ParserTest):
    def test_def(self):
        result = self.parse('.def foo bar', 'def')
        self.assertEqual(result.name, 'foo')
        self.assertEqual(result.expr.value, 'bar')



class StorageTest(ParserTest):
    def test_parse_byte(self):
        result = self.parse('.byte 01','byte_storage')
        self.assertEqual(result,
            Storage(Pos(0, 8), 1, tuple([
                ExprValue(Pos(6, 8), 1)
            ]))
        )

    def test_parse_byte_many(self):
        result = self.parse(".byte 01, 02, 03",'byte_storage')
        self.assertEqual(result,
            Storage(Pos(0, 16), 1, tuple([
                ExprValue(Pos(6,8), 1),
                ExprValue(Pos(10,12), 2),
                ExprValue(Pos(14,16), 3),
            ]))
        )

class OperTest(ParserTest):
    def test_op_nop(self):
        text = 'nop'
        result = self.parse(text, 'op_nop')
        self.assertEqual(result, [
            Token(Pos(start=0, end=3), text),
        ])

    def test_oper(self):
        result = self.parse('nop', 'oper')
        self.assertEqual(result.name, 'nop')

    def test_arg_precedence(self):
        result = self.parse('sta (<foo),y', 'oper')
        self.assertEqual(result.mode, AddressMode.indirect_y)

    def test_jsr(self):
        self.parser.debug = True
        result = self.parse('jsr foo', 'oper')
        self.assertEqual(result.mode, AddressMode.absolute)


class ExprTest(ParserTest):
    def test_negate(self):
        result = self.parse('-42', 'negate')
        self.assertEqual(result, ExprNegate(Pos(0, 3),
            ExprValue(Pos(1, 3), 42),
        ))

    def test_add(self):
        result = self.parse('3 + 4', 'add')
        self.assertEqual(result, ExprAdd(Pos(0, 5),
            ExprValue(Pos(0, 1), 3),
            ExprValue(Pos(4, 5), 4),
        ))

    def test_lobyte(self):
        result = self.parse('<33', 'lobyte')
        self.assertEqual(result, ExprLobyte(Pos(0, 3),
            ExprValue(Pos(1, 3), 33),
        ))
        result = self.parse('<$33', 'expr')
        self.assertEqual(result[0], ExprLobyte(Pos(0, 4),
            ExprValue(Pos(1, 4), 0x33, 16),
        ))

    def test_mul(self):
        result = self.parse('2 * foo', 'mul')
        self.assertEqual(result, ExprMul(Pos(0, 7),
            ExprValue(Pos(0, 1), 2),
            ExprName(Pos(4, 7), 'foo'),
        ))


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
        self.assertEqual(result, [
            ExprName(pos=Pos(start=0, end=3, context='<internal>'), value='one'),
        ])
        result = self.parse('foo, bar, baz', 'macro_params')
        self.assertEqual(result, [
            ExprName(pos=Pos(start=0, end=3, context='<internal>'), value='foo'),
            ExprName(pos=Pos(start=5, end=8, context='<internal>'), value='bar'),
            ExprName(pos=Pos(start=10, end=13, context='<internal>'), value='baz'),
        ])

    def test_macro(self):
        result = self.parse(""".macro foo .end""", 'macro')
        self.assertEqual(result.name, 'foo')
        self.assertEqual(result.params, tuple())
        self.assertEqual(result.body, tuple())

    def test_macro_params2(self):
        self.parser.debug = True
        result = self.parse(""".macro foo, a,b,c
        nop
        .end""", 'macro')
        self.assertEqual(result.name, 'foo')
        self.assertEqual(result.params, ('a','b','c'))
        print('body:', result.body)
        self.assertEqual(len(result.body), 1)
        self.assertEqual(result.body[0].name, 'nop')

    def test_macro_call(self):
        result = self.parse('foo', 'macro_call')
        self.assertEqual(result,
            MacroCall(Pos(0, 3), 'foo', tuple())
        )

    def test_macro_call_args(self):
        result = self.parse('foo $EA', 'macro_call')
        self.assertEqual(result,
            MacroCall(Pos(0, 7), 'foo', tuple([
                ExprValue(Pos(4, 7), 0xEA, 16),
            ]))
        )

    def test_macro_error(self):
        with self.assertRaisesRegex(ParseError,
                r"<internal> \(1, 7\): expected macro params"):
            self.parse('.macro', 'macro')


class ExceptionTest(ParserTest):
    def test_goal_fail(self):
        with self.assertRaisesRegex(ParseError,
                r"<internal> \(1, 1\): Invalid syntax. "
                r"Expected directive, macro, label, or operation"):
            self.parse('.foobar', 'goal')


class CommentTest(ParserTest):
    def test_full_line_comment(self):
        result = self.parse("""; foo bar baz""")
        self.assertEqual(result, [
            Comment(pos=Pos(start=0, end=13),
                full_line=True, text=' foo bar baz'),
        ])

    def test_full_line_multi(self):
        result = self.parse(""";foo\n;bar\n;baz""")
        self.assertEqual(result, [
            Comment(pos=Pos(start=0, end=4),
                full_line=True, text='foo'),
            Comment(pos=Pos(start=5, end=9),
                full_line=True, text='bar'),
            Comment(pos=Pos(start=10, end=14),
                full_line=True, text='baz'),
        ])

    def test_end_line_comment(self):
        result = self.parse(""".pragma foo bar;baz""")
        self.assertEqual(len(result), 1)
        pragma = result[0]
        self.assertEqual(pragma.name, 'foo')
        self.assertEqual(pragma.expr.value, 'bar')
        self.assertEqual(pragma.comment.text, 'baz')
        self.assertEqual(pragma.comment.full_line, False)


class VarTest(ParserTest):
    def test_var_simple(self):
        result = self.parse(""".var foo 9""")
        self.assertEqual(result, [
            Var(pos=Pos(start=0, end=10), name='foo', init=tuple(),
                size=ExprValue(Pos(start=9, end=10), value=9)),
        ])

    def test_var_init(self):
        result = self.parse(""".var foo 2, 1, 2, 3""")
        self.assertEqual(len(result), 1)
        var = result[0]
        self.assertEqual(var.name, 'foo')
        self.assertEqual(var.size.value, 2)
        self.assertEqual(len(var.init), 3)
        self.assertEqual(tuple([x.value for x in var.init]), (1, 2, 3))


class StructTest(ParserTest):
    def test_struct_empty(self):
        result = self.parse(".struct foo .end")
        self.assertEqual(result, [
            Struct(pos=Pos(start=0, end=16), name='foo', fields=tuple(),
                offset=None),
        ])

    def test_struct_offset(self):
        result = self.parse(".struct foo 100 .end")
        self.assertEqual(result, [
            Struct(pos=Pos(start=0, end=20), name='foo', fields=tuple(),
                offset=ExprValue(Pos(start=12, end=15), value=100)),
        ])

    def test_struct_field(self):
        result = self.parse("""
        .struct foo
            .var x 1  ; single byte field
            .var y 2  ; word field
        .end""")
        self.assertEqual(len(result), 1)
        struct = result[0]
        self.assertEqual(struct.name, 'foo')
        self.assertEqual(len(struct.fields), 2)
        field_x = struct.fields[0]
        field_y = struct.fields[1]
        self.assertEqual(field_x.name, 'x')
        self.assertEqual(field_x.size.value, 1)
        self.assertEqual(field_y.name, 'y')
        self.assertEqual(field_y.size.value, 2)

    def test_struct_label(self):
        result = self.parse("""
        .struct foo
            baz:
        .end""")
        self.assertEqual(len(result), 1)
        struct = result[0]
        self.assertEqual(struct.name, 'foo')
        self.assertEqual(len(struct.fields), 1)
        baz = struct.fields[0]
        self.assertEqual(baz.name, 'baz')

    def test_struct_def(self):
        result = self.parse("""
        .struct foo
            .def baz 20
        .end""")
        self.assertEqual(len(result), 1)
        struct = result[0]
        self.assertEqual(struct.name, 'foo')
        self.assertEqual(len(struct.fields), 1)
        baz = struct.fields[0]
        self.assertEqual(baz.name, 'baz')
        self.assertEqual(baz.expr.value, 20)

