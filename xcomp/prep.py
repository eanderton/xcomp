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

    def _start_macro_decl(self, tok):
        print('start decl', tok.value)
        name = tok.value
        self._macro = Macro(name)
        self._macros[name] = self._macro

    def _end_macro_decl(self, _=None):
        self._macro = None

    def _start_macro_call(self, tok):
        print('macro call', tok.value, self.pos)
        name = tok.value
        self._macro = self._macros[name]

    def _end_macro_call(self, _=None):
        print('end macro call', self.pos)
        # emit constants for args
        for ii in range(len(self._macro_args)):
            arg = self._macro_args[ii]
            param = self._macro.params[ii]
            param = self._macro.get_param_id(param)
            self._tokens_out.extend([
                Tok.const('.const', line=0, column=0),
                Tok.ident(param, line=0, column=0),
                arg,
            ])
        # emit macro body and cleanup
        self._tokens_out.extend(self._macro.body)
        self._macro_args = []
        self._has_substitutions = len(self._macro.params) > 0

    def _insert_const(self, tok):
        print('insert const', tok.value, tuple(map(str, self._tokens_out)))
        macro = self._macros[tok.value]
        self._tokens_out.extend(macro.body)

    def _add_macro_arg(self, tok):
        self._macro_args.append(tok)

    def _add_macro_param(self, tok):
        self._macro.params.append(tok.value)

    def _add_macro_body(self, tok):
        if tok.value in self._macro.params:
            param_id = self._macro.get_param_id(tok.value)
            macro_token = tok(
                    param_id, tok.line, tok.column, tok.source)
        else:
            macro_token = tok
        self._macro.body.append(macro_token)

    def _set_const_body(self, tok):
        self._macro.body.append(tok)
        self._end_macro_decl()

    def _add_token(self, tok):
        self._tokens_out.append(tok)

    def _is_const(self, tok):
        macro = self._macros.get(tok.value, None)
        return macro and macro.is_const()

    def _is_macro(self, tok):
        return tok.value in self._macros

    def reset(self):
        ''' Resets the parser state. '''
        self._tokens_out = []
        self._macros = {}
        self._macro = None
        self._macro_args = []
        self._has_substitutions = False
        super().reset()

    # TODO; may need a soft_reset() for a multipass capable parser base

    def parse(self, asm_source, max_passes=10):
        lexer = Lexer()
        lexer.parse(asm_source)
        self._lex_tokens = lexer.tokens  # debug

        # loop until there's nothing left to do
        self._tokens_out = lexer.tokens
        for ii in range(max_passes):
            self._tokens = self._tokens_out
            self.reset()
            print('pass:', ii+1)
            super().parse(self._tokens)
            if not self._has_substitutions:
                break

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
                (Tok.ident, self._add_macro_param, 'macro_param_next'),
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
                (',', nop, 'macro_arg'),
                (match_peek, self._end_macro_call, 'goal',),
                (match_end, self._end_macro_call, 'goal'),
            ),
        }
