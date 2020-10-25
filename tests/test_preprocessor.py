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

    def _set_file(self, content, path='<internal>'):
        self._test_files[path] = content

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
        self._set_file(cleandoc("""
        .macro foo
        .endmacro
        """))
        parser.parse('<internal>')
        self.assertLexEqual(parser._tokens_out, [])
        foo = parser._macros.get('foo', None)
        self.assertIsNotNone(foo)
        self.assertTrue(foo.is_singlet())
        self.assertEqual(foo.params, [])
        self.assertEqual(foo.body, [])

    @selfish('parser')
    def test_const_decl(self, parser):
        self._set_file(cleandoc("""
        .const foo 0x1234
        """))
        parser.parse('<internal>')
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
        self._set_file(cleandoc("""
        .macro foo
            macro content
        .endmacro
        """))
        parser.parse('<internal>')
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
        self._set_file(cleandoc("""
        .macro foo, a
            macro content a
        .endmacro
        """))
        parser.parse('<internal>')
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
        self._set_file(cleandoc("""
        .macro foo, a, b, c
            macro content
        .endmacro
        """))
        parser.parse('<internal>')
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
            self._set_file(cleandoc("""
            .const
            """))
            parser.parse('<internal>')

    @selfish('parser')
    def test_const_no_value(self, parser):
        with self.assertRaises(ParseError, msg='Expected const value'):
            self._set_file(cleandoc("""
            .const foo
            """))
            parser.parse('<internal>')

    @selfish('parser')
    def test_macro_no_name(self, parser):
        with self.assertRaises(ParseError, msg='Expected macro name'):
            self._set_file(cleandoc("""
            .macro
            """))
            parser.parse('<internal>')

    @selfish('parser')
    def test_macro_param_no_end(self, parser):
        parser.reset()
        with self.assertRaises(ParseError,
                msg='Expected macro parameter name'):
            self._set_file(cleandoc("""
            .macro foo,
            """))
            parser.parse('<internal>')

    @selfish('parser')
    def test_macro_no_body(self, parser):
        with self.assertRaises(ParseError, msg='Expected ".endmacro"'):
            self._set_file(cleandoc("""
            .macro foo
            """))
            parser.parse('<internal>')

        parser.reset()
        with self.assertRaises(ParseError, msg='Expected ".endmacro"'):
            self._set_file(cleandoc("""
            .macro foo xxx
            """))
            parser.parse('<internal>')

class TestPrepSubstitution(PrepTest):

    @selfish('parser')
    def test_macro_decl_empty(self, parser):
        self._set_file(cleandoc("""
        .macro foo
        .endmacro
        foo
        """))
        parser.parse('<internal>')
        self.assertLexEqual(parser._tokens_out, [])
        foo = parser._macros.get('foo', None)
        self.assertIsNotNone(foo)
        self.assertTrue(foo.is_singlet())
        self.assertEqual(foo.params, [])
        self.assertEqual(foo.body, [])

    @selfish('parser')
    def test_macro_decl_content(self, parser):
        self._set_file(cleandoc("""
        .macro foo
            lda 0x4001
        .endmacro
        foo
        """))
        parser.parse('<internal>')
        self.assertLexEqual(parser._tokens_out, [
            Token('op', 'lda', line=2, column=5),
            Token('number', 0x4001, line=2, column=9),
        ])
        foo = parser._macros.get('foo', None)
        self.assertIsNotNone(foo)
        self.assertTrue(foo.is_singlet())
        self.assertEqual(foo.params, [])
        self.assertLexEqual(foo.body, [
            Token('op', 'lda', line=2, column=5),
            Token('number', 0x4001, line=2, column=9),
        ])

    @selfish('parser')
    def test_macro_args_one_pass(self, parser):
        self._set_file(cleandoc("""
        .macro foo, addr
            lda addr
        .endmacro
        foo 0xbabe
        """))
        parser.parse('<internal>', max_passes=1)
        foo = parser._macros.get('foo', None)
        self.assertIsNotNone(foo)
        self.assertFalse(foo.is_singlet())
        self.assertEqual(foo.params, ['addr'])

        self.assertLexEqual(parser._tokens_out, [
            Token('.const', '.const'),
            Token('ident', foo.get_param_id('addr')),
            Token('number', 0xbabe, line=4, column=5),
            Token('op', 'lda', line=2, column=5),
            Token('ident', foo.get_param_id('addr'), line=2, column=9),
        ])

        self.assertLexEqual(foo.body, [
            Token('op', 'lda', line=2, column=5),
            Token('ident', foo.get_param_id('addr'), line=2, column=9),
        ])

    @selfish('parser')
    def test_macro_args(self, parser):
        self._set_file(cleandoc("""
        .macro foo, addr
            lda addr
        .endmacro
        foo 0xbabe
        """))
        parser.parse('<internal>')
        self.assertLexEqual(parser._tokens_out, [
            Token('op', 'lda', line=2, column=5),
            Token('number', 0xbabe, line=4, column=5),
        ])

    @selfish('parser')
    def test_macro_args_multi(self, parser):
        self._set_file(cleandoc("""
        .macro foo, a, b, c, d
            op d, c, b, a
        .endmacro
        foo 0x01, 0x02, 0x03, 0x04
        """))
        parser.parse('<internal>')
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

    # TODO: assertRaises is not validating msg
    @selfish('parser')
    def test_too_many_args(self, parser):
        with self.assertRaises(ParseError,
                msg='Expected 1 arguments; got 3 instead'):
            self._set_file(cleandoc("""
            .macro foo, a
            .endmacro
            foo one,two
            """))
            parser.parse('<internal>')

    @selfish('parser')
    def test_too_few_args(self, parser):
        with self.assertRaises(ParseError,
                msg='Expected 3 arguments; got 1 instead'):
            self._set_file(cleandoc("""
            .macro foo, a,b,c
            .endmacro
            foo one
            """))
            parser.parse('<internal>')

class TestPreprocessorInclude(PrepTest):
    @selfish('parser')
    def test_include_file(self, parser):
        self._set_file(cleandoc("""
        .macro foo, a, b, c, d
            op d, c, b, a
        .endmacro
        """), 'macro-lib.inc')

        self._set_file(cleandoc("""
        .include "macro-lib.inc"
        foo 0x01, 0x02, 0x03, 0x04
        """))
        parser.parse('<internal>')
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

    @selfish('parser')
    def test_expected_string(self, parser):
        with self.assertRaises(ParseError,
                msg='Expected string argument for .include.'):
            self._set_file(cleandoc("""
            .include foobar
            """))
            parser.parse('<internal>')

