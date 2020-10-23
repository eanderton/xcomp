from inspect import cleandoc
from pragma_utils import selfish
from xcomp.prep import Preprocessor
from oxeye.token import Token
from oxeye.exception import ParseError
from oxeye.testing import *
from pprint import pprint

class PrepTest(OxeyeTest):
    def __init__(self, *args, **kwargs):
        self._test_files = {}
        super().__init__(*args, **kwargs)

    def _load_file(self, path):
        return self._test_files[path]

    def setUp(self):
        self.maxDif = None
        self.parser = Preprocessor(self._load_file)
        super().setUp()

    @selfish('parser')
    def tearDown(self, parser):
        print('trace:')
        dbg = {x:getattr(parser, x) for x in [
            '_trace', '_macros', '_macro_args',
            ]}
        dbg['_tokens_out'] = tuple([x.value for x in parser._tokens_out])
        pprint(dbg, indent=1, width=40)


class TestPreprocessor(PrepTest):
    @selfish('parser')
    def test_macro_decl_empty(self, parser):
        parser.parse(cleandoc("""
        .macro foo
        .endmacro
        """))
        self.assertLexEqual(parser._tokens_out, [])
        foo = parser._macros.get('foo', None)
        self.assertIsNotNone(foo)
        self.assertTrue(foo.is_singlet())
        self.assertEqual(foo.params, [])
        self.assertEqual(foo.body, [])

    @selfish('parser')
    def test_const_decl(self, parser):
        parser.parse(cleandoc("""
        .const foo 0x1234
        """))
        self.assertLexEqual(parser._tokens_out, [])
        foo = parser._macros.get('foo', None)
        self.assertIsNotNone(foo)
        self.assertTrue(foo.is_singlet())
        self.assertEqual(foo.params, [])
        self.assertLexEqual(foo.body, [
            Token('number', 0x1234, line=1, column=12),
        ])


    @selfish('parser')
    def test_macro_decl_args_none(self, parser):
        parser.parse(cleandoc("""
        .macro foo ()
            macro content
        .endmacro
        """))
        self.assertLexEqual(parser._tokens_out, [])
        foo = parser._macros.get('foo', None)
        self.assertIsNotNone(foo)
        self.assertTrue(foo.is_singlet())
        self.assertEqual(foo.params, [])
        self.assertEqual(foo.body, [
            Token('ident', 'macro', line=2, column=5),
            Token('ident', 'content', line=2, column=11),
        ])

    @selfish('parser')
    def test_macro_decl_args_one(self, parser):
        parser.parse(cleandoc("""
        .macro foo (a)
            macro content a
        .endmacro
        """))
        self.assertLexEqual(parser._tokens_out, [])
        foo = parser._macros.get('foo', None)
        self.assertIsNotNone(foo)
        self.assertFalse(foo.is_singlet())
        self.assertEqual(foo.params, ['a'])
        self.assertLexEqual(foo.body, [
            Token('ident', 'macro', line=2, column=5),
            Token('ident', 'content', line=2, column=11),
            Token('ident', foo.get_param_id('a'), line=2, column=19),
        ])

    @selfish('parser')
    def test_macro_decl_args_multi(self, parser):
        parser.parse(cleandoc("""
        .macro foo (a, b, c)
            macro content
        .endmacro
        """))
        self.assertLexEqual(parser._tokens_out, [])
        foo = parser._macros.get('foo', None)
        self.assertIsNotNone(foo)
        self.assertFalse(foo.is_singlet())
        self.assertEqual(foo.params, ['a', 'b', 'c'])
        self.assertEqual(foo.body, [
            Token('ident', 'macro', line=2, column=5),
            Token('ident', 'content', line=2, column=11),
        ])

    @selfish('parser')
    def test_const_no_name(self, parser):
        with self.assertRaises(ParseError, msg='Expected const name'):
            parser.parse(cleandoc("""
            .const
            """))

    @selfish('parser')
    def test_const_no_value(self, parser):
        with self.assertRaises(ParseError, msg='Expected const value'):
            parser.parse(cleandoc("""
            .const foo
            """))

    @selfish('parser')
    def test_macro_no_name(self, parser):
        with self.assertRaises(ParseError, msg='Expected macro name'):
            parser.parse(cleandoc("""
            .macro
            """))

    @selfish('parser')
    def test_macro_param_no_end(self, parser):
        with self.assertRaises(ParseError,
                msg='Expected closing ")" in macro parameter list.'):
            parser.parse(cleandoc("""
            .macro foo (
            """))
        parser.reset()
        with self.assertRaises(ParseError,
                msg='Expected closing ")" in macro parameter list.'):
            parser.parse(cleandoc("""
            .macro foo (a
            """))
        parser.reset()
        with self.assertRaises(ParseError,
                msg='Expected closing ")" in macro parameter list.'):
            parser.parse(cleandoc("""
            .macro foo (a,
            """))

    @selfish('parser')
    def test_macro_no_body(self, parser):
        with self.assertRaises(ParseError, msg='Expected ".endmacro"'):
            parser.parse(cleandoc("""
            .macro foo
            """))

        parser.reset()
        with self.assertRaises(ParseError, msg='Expected ".endmacro"'):
            parser.parse(cleandoc("""
            .macro foo xxx
            """))

class TestPrepSubstitution(PrepTest):

    @selfish('parser')
    def test_macro_decl_empty(self, parser):
        parser.parse(cleandoc("""
        .macro foo
        .endmacro
        foo
        """))
        self.assertLexEqual(parser._tokens_out, [])
        foo = parser._macros.get('foo', None)
        self.assertIsNotNone(foo)
        self.assertTrue(foo.is_singlet())
        self.assertEqual(foo.params, [])
        self.assertEqual(foo.body, [])

    @selfish('parser')
    def test_macro_decl_content(self, parser):
        parser.parse(cleandoc("""
        .macro foo
            lda 0x4001
        .endmacro
        foo
        """))
        self.assertLexEqual(parser._tokens_out, [
            Token('ident', 'lda', line=2, column=5),
            Token('number', 0x4001, line=2, column=9),
        ])
        foo = parser._macros.get('foo', None)
        self.assertIsNotNone(foo)
        self.assertTrue(foo.is_singlet())
        self.assertEqual(foo.params, [])
        self.assertLexEqual(foo.body, [
            Token('ident', 'lda', line=2, column=5),
            Token('number', 0x4001, line=2, column=9),
        ])

    @selfish('parser')
    def test_macro_args_one_pass(self, parser):
        parser.parse(cleandoc("""
        .macro foo (addr)
            lda addr
        .endmacro
        foo 0xbabe
        """), max_passes=1)
        foo = parser._macros.get('foo', None)
        self.assertIsNotNone(foo)
        self.assertFalse(foo.is_singlet())
        self.assertEqual(foo.params, ['addr'])

        self.assertLexEqual(parser._tokens_out, [
            Token('.const', '.const'),
            Token('ident', foo.get_param_id('addr')),
            Token('number', 0xbabe, line=4, column=5),
            Token('ident', 'lda', line=2, column=5),
            Token('ident', foo.get_param_id('addr'), line=2, column=9),
        ])

        self.assertLexEqual(foo.body, [
            Token('ident', 'lda', line=2, column=5),
            Token('ident', foo.get_param_id('addr'), line=2, column=9),
        ])

    @selfish('parser')
    def test_macro_args(self, parser):
        parser.parse(cleandoc("""
        .macro foo (addr)
            lda addr
        .endmacro
        foo 0xbabe
        """))
        self.assertLexEqual(parser._tokens_out, [
            Token('ident', 'lda', line=2, column=5),
            Token('number', 0xbabe, line=4, column=5),
        ])

    @selfish('parser')
    def test_macro_args_multi(self, parser):
        parser.parse(cleandoc("""
        .macro foo (a, b, c, d)
            op d, c, b, a
        .endmacro
        foo 0x01, 0x02, 0x03, 0x04
        """))
        self.assertLexEqual(parser._tokens_out, [
            Token('ident', 'op', line=2, column=5),
            Token('number', 0x04, line=4, column=23),
            Token(',', ',', line=2, column=9),
            Token('number', 0x03, line=4, column=17),
            Token(',', ',', line=2, column=12),
            Token('number', 0x02, line=4, column=11),
            Token(',', ',', line=2, column=15),
            Token('number', 0x01, line=4, column=5),
        ])

class TestPreprocessorInclude(PrepTest):
    def setUp(self):
        self._test_files = {
            'macro-lib.inc': cleandoc("""
            .macro foo (a, b, c, d)
                op d, c, b, a
            .endmacro
            """),
        }
        super().setUp()

    @selfish('parser')
    def test_include_file(self, parser):
        parser.parse(cleandoc("""
        .include "macro-lib.inc"
        foo 0x01, 0x02, 0x03, 0x04
        """))
        self.assertLexEqual(parser._tokens_out, [
            Token('ident', 'op', line=2, column=5, source='macro-lib.inc'),
            Token('number', 0x04, line=2, column=23),
            Token(',', ',', line=2, column=9, source='macro-lib.inc'),
            Token('number', 0x03, line=2, column=17),
            Token(',', ',', line=2, column=12, source='macro-lib.inc'),
            Token('number', 0x02, line=2, column=11),
            Token(',', ',', line=2, column=15, source='macro-lib.inc'),
            Token('number', 0x01, line=2, column=5),
        ])


