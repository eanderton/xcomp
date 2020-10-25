import unittest
from inspect import cleandoc
from pragma_utils import selfish
from oxeye.exception import ParseError
from oxeye.testing import *
from xcomp.prep import Preprocessor
from xcomp.parser import Parser
from xcomp.lexer import Tok
from pprint import pprint

class ParserTest(OxeyeTest):
    def __init__(self, *args, **kwargs):
        self._test_files = {}
        super().__init__(*args, **kwargs)

    def _load_file(self, path):
        return self._test_files[path]

    def _set_file(self, content, path='<internal>'):
        self._test_files[path] = content

    def setUp(self):
        self.maxDif = None
        self.pre = Preprocessor(self._load_file)
        self.parser = Parser()
        super().setUp()

    def _parse(self, text, path='<internal>'):
        self._set_file(text, path)
        tokens = self.pre.parse(path)
        print('Tokens:', tokens)
        self.parser.parse(tokens)

    @selfish('parser')
    def tearDown(self, parser):
        dbg = {x:getattr(parser, x) for x in [
            'segments',
            ]}
        dbg['_trace'] = parser._trace
        pprint(dbg, indent=1, width=40)



class TestParserBasic(ParserTest):
    @selfish('parser')
    def test_empty(self, parser):
        self._parse("""
        """)
        # TODO: figure out valid tests

    @selfish('parser')
    def test_segments(self, parser):
        self._parse("""
        .zero
        .text
        .data
        .bss
        """)
        # TODO: figure out valid tests

