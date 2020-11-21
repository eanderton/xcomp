import unittest
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
        self.compiler = Compiler()

    def set_file(self, name, text):
        self.ctx_manager.files[name] = cleandoc(text)

    def assertAstEqual(self, ast, ast_text):
        left = '\n'.join(map(str, ast))
        right = cleandoc(ast_text)
        self.assertEqual(left, right)

    def parse(self, name):
        return self.processor.parse(name)

    def compile(self, name):
        return self.compiler.compiler(self.parse(name))


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
    def test_compile_simple(self):
        self.assertTrue(True)
