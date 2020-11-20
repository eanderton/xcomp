import unittest
from inspect import cleandoc
from xcomp.compiler import Compiler
from xcomp.compiler import CompilationError
from xcomp.parser import Parser
from xcomp.model import *



class CompilerTest(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.parser = Parser()
        self.compiler = Compiler(FileContextManager())

    def set_file(self, name, text):
        self.compiler.ctx_manager.files[name] = cleandoc(text)

    def assertAstEqual(self, ast, ast_text):
        left = '\n'.join(map(str, ast))
        right = cleandoc(ast_text)
        self.assertEqual(left, right)

class PreprocessorTest(CompilerTest):
    def pre_process(self, name):
        ast = self.compiler._parse(name)
        return self.compiler._pre_process(ast)

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
        self.assertAstEqual(self.pre_process('foo.asm'), """
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


