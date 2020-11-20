import unittest
from inspect import cleandoc
from xcomp.compiler import PreProcessor
from xcomp.compiler import Compiler
from xcomp.compiler import CompilationError
from xcomp.parser import Parser
from xcomp.model import *



class CompilerTest(unittest.TestCase):
    def setUp(self):
        self.ctx_manager = FileContextManager()
        self.processor = PreProcessor(self.ctx_manager)

    def set_file(self, name, text):
        self.ctx_manager.files[name] = cleandoc(text)

    def assertAstEqual(self, ast, ast_text):
        left = '\n'.join(map(str, ast))
        right = cleandoc(ast_text)
        self.assertEqual(left, right)

class PreprocessorTest(CompilerTest):
    def parse(self, name):
        return self.processor.parse(name)

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
            .text 32768
            start:
                lda #128
                lda <foo
            .scope
            .define value 123
                nop
                adc #value
            .endscope
            """)


