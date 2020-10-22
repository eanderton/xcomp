'''
Parser for the compiler.
'''

from oxeye.token import Token, TokenParser
from oxeye.pred import nop
from oxeye.rule import *
from oxeye.match import *
from xcomp.model import *
from xcomp.lexer import Tok, Lexer

class Preprocessor(TokenParser):
    '''
    Pre-processor for a token stream that handles
    '''
    # TODO: factor into reset() after refactoring parser
    def __init__(self, *args, **kwargs):
        self._tokens_out = []
        self._ident = None
        self._macros = {}
        self._const = {}
        self._macro_name = None
        self._macro_body = []
        self._macro_args = []
        super().__init__(*args, **kwargs)

    def _start_macro_decl(self, tok):
        print('START DECL')
        self._macro_name = tok.value

    def _end_macro_decl(self, _):
        print('END DECL')
        name = self._macro_name
        self._macros[name] = Macro(name, self._macro_args, self._macro_body)
        if len(self._macro_args) == 0:
            self._const[name] = name
        self._macro_name = None
        self._macro_args = []
        self._macro_body = []

    def _start_macro_call(self, head, macro):
        print('call', str(head), macro)
        self._macro = macro

    def _end_macro_call(self, head, macro):
        # TODO: sub-process content somehow
        self._tokens_out.extend(self._macro.body)
        self._macro = None

    def _insert_const(self, head):
        macro = self._macros[head.value]
        self._tokens_out.extend(macro.body)

    def _set_macro_name(self, tok):
        self._macro_name = tok.value

    def _add_macro_arg(self, tok):
        self._macro_args.append(tok.value)

    def _add_macro_body(self, tok):
        self._macro_body.append(tok)

    def _set_const_body(self, tok):
        self._macro_body.append(tok)
        self._end_macro_decl(tok)

    def _add_token(self, tok):
        self._tokens_out.append(tok)

    def _is_const(self, tok):
        return tok.value in self._const

    def _is_macro(self, tok):
        return tok.value in self._macros

    def reset(self):
        ''' Resets the parser state. '''
        self._tokens_out.clear()
        self._ident = None
        self._macros.clear()
        self._const.clear()
        self._macro_name = None
        self._macro_body.clear()
        self._macro_args.clear()
        super().reset()

    def parse(self, asm_source):
        lexer = Lexer()
        lexer.parse(asm_source)
        self._tokens = lexer.tokens  # debug
        super().parse(lexer.tokens)

    def generate_grammar(self):
        ''' Generates the grammar for the parser. '''
        return {
            'goal': (
                (Tok.macro, nop, 'macro_decl'),
                (Tok.const, nop,'const_decl'),
                (match_fn(self._is_const), self._insert_const, 'goal'),
                (match_fn(self._is_macro), self._start_macro_call, 'macro_arg'),
                (match_any, self._add_token, 'goal'),
                rule_end,
            ),

            'const_decl': (
                (Tok.ident, self._start_macro_decl, 'const_body'),
                self._error('Expected const name'),
            ),
            'const_body': (
                (match_any, self._set_const_body, 'goal'),
                self._error('Expected const value'),
            ),

            'macro_decl': (
                (Tok.ident, self._start_macro_decl, 'macro_param_start'),
                self._error('Expected macro name'),
            ),
            'macro_param_start': (
                ('(', nop, 'macro_param'),
                (match_peek, nop, 'macro_body'),
                self._error('Expected ".endmacro"'),
            ),
            'macro_param': (
                (Tok.ident, self._add_macro_arg, 'macro_param_next'),
                (')', nop, 'macro_body'),
                self._error('Expected closing ")" in macro parameter list.')
            ),
            'macro_param_next': (
                (',', nop, 'macro_param'),
                (')', nop, 'macro_body'),
                self._error('Expected closing ")" in macro parameter list.')
            ),
            'macro_body': (
                (Tok.endmacro, self._end_macro_decl, 'goal'),
                (match_any, self._add_macro_body, 'macro_body'),
                self._error('Expected ".endmacro"'),
            ),

            'macro_arg': (
                (match_any, self._add_macro_arg, 'macro_arg_next'),
                self._error('Expected one or more arguments for macro.'),
            ),
            'macro_arg_next': (
                (',', nop, 'macro_param'),
                (match_peek, self._end_macro_call, 'goal')
            ),
        }
