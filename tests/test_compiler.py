import unittest
import hexdump
from inspect import cleandoc
from xcomp.compiler import PreProcessor
from xcomp.compiler import Compiler
from xcomp.compiler import CompilationError
from xcomp.parser import Parser
from xcomp.model import *



class TestBase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.ctx_manager = FileContextManager()
        self.processor = PreProcessor(self.ctx_manager)
        #self.processor.debug = True
        self.compiler = Compiler(self.ctx_manager)
        self.compiler.debug = True

    def set_file(self, name, text):
        self.ctx_manager.files[name] = cleandoc(text)

    def assertAstEqual(self, ast, ast_text):
        left = '\n'.join(map(str, ast))
        right = cleandoc(ast_text)
        self.assertEqual(left, right)

    def assertSegAttrEqual(self, name, attr, value):
        self.assertEqual(getattr(self.compiler.segments[name], attr), value)

    def assertDataEqual(self, start, end, values):
        left = hexdump.dump(self.compiler.data[start:end])
        right = hexdump.dump(bytearray(values))
        self.assertEqual(left, right)

    def parse(self, name):
        return self.processor.parse(name)

    def compile(self, name):
        return self.compiler.compile(self.parse(name))


class PreprocessorTest(TestBase):
    def test_macro(self):
        self.set_file('foo.asm', """
            .macro foobar, value
                nop
                adc #value
            .endmacro
            .text 0x8000
            start:
                lda #$80
                lda <foo
                foobar 123
            """)
        self.assertAstEqual(self.parse('foo.asm'), """
            .text $8000
            start:
                lda #$80
                lda <foo
            .scope
            .define value 123
                nop
                adc #value
            .endscope
            """)

    def test_include(self):
        self.set_file('root.asm',"""
        .text
        .include "test.asm"
        nop
        """)
        self.set_file('test.asm',"""
        lda $40
        adc #$80
        """)
        self.assertAstEqual(self.parse('root.asm'), """
        .text
            lda $40
            adc #$80
            nop
        """)


class CompilerTest(TestBase):
    def test_segment(self):
        self.set_file('root.asm', """
        .def foo $1234
        .text foo
        """)
        self.compile('root.asm')
        self.assertEqual(self.compiler.segments['text'].offset, 0x1234)

        with self.assertRaisesRegex(CompilationError,
                r'root.asm \(1, 7\): Identifier foo is undefined.'):
            self.set_file('root.asm', """
            .text foo
            """)
            self.compile('root.asm')

    def test_compile_simple(self):
        self.set_file('root.asm', """
        nop
        adc #$80
        """)
        self.compile('root.asm')
        self.assertDataEqual(0x0800, 0x0803, [
            0xEA, 0x69, 0x80
        ])
        print('{0:x}'.format(self.compiler.seg.offset))
        self.assertSegAttrEqual('text', 'offset', 0x0804)

    def test_def_simple(self):
        self.set_file('root.asm', """
        .def x $1234
        adc x
        """)
        self.compile('root.asm')
        self.assertDataEqual(0x0800, 0x0803, [
            0x6D, 0x34, 0x12
        ])

    def test_def_expr(self):
        self.set_file('root.asm', """
        .def x $1000 + ($200 + $34)
        adc x
        """)
        self.compile('root.asm')
        self.assertDataEqual(0x0800, 0x0803, [
            0x6D, 0x34, 0x12
        ])

    def test_storage_byte(self):
        self.set_file('root.asm', """
        .data 0x0200
        .byte $CA, $FE, $BA, $BE
        """)
        self.compile('root.asm')
        self.assertDataEqual(0x0200, 0x0204, [
            0xCA, 0xFE, 0xBA, 0xBE
        ])


