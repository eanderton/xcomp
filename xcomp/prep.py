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
    Pre-processor for a token stream that handles macros and inclusions.
    '''
    def __init__(self, file_loader_fn):
        self.file_loader_fn = file_loader_fn
        super().__init__()

    def _include_file(self, tok):
        ''' Inserts a tokenized file into the output stream '''
        filename = tok.value
        lexer = Lexer()
        lexer.parse(self.file_loader_fn(filename), source=filename)
        self._tokens_out.extend(lexer.tokens)
        self._needs_another_pass = True

    def _start_macro_decl(self, tok):
        ''' Creates a new macro object for the token name provided. '''
        name = tok.value
        self._macro = Macro(name)
        self._macros[name] = self._macro

    def _end_macro_decl(self, _=None):
        ''' Clears the current macro state. '''
        self._macro = None

    def _start_macro_call(self, tok):
        ''' Generates a new macro for the identifier token specified. '''
        name = tok.value
        self._macro = self._macros[name]

    def _end_macro_call(self, _=None):
        ''' Substitutes the current macro into the output token stream. '''
        # validate arguments are satisfied
        arglen = len(self._macro_args)
        paramlen = len(self._macro.params)
        if arglen != paramlen:
            self._parse_error(f'Expected {paramlen} arguments; got {arglen} instead')

        # emit constants for args to be used on next pass
        for ii in range(arglen):
            arg = self._macro_args[ii]
            param = self._macro.get_param_id(ii)
            self._tokens_out.extend([
                Tok.const('.const', line=0, column=0),
                Tok.ident(param, line=0, column=0),
                arg,
            ])

        # emit macro body, cleanup, and flag for one more pass
        self._tokens_out.extend(self._macro.body)
        self._macro_args = []
        self._needs_another_pass = len(self._macro.params) > 0

    def _insert_singlet(self, tok):
        ''' Inserts singlet into the output token stream '''
        macro = self._macros[tok.value]
        self._tokens_out.extend(macro.body)

    def _add_macro_arg(self, tok):
        print('add_macro_arg', str(tok))
        self._macro_args.append(tok)

    def _add_macro_param(self, tok):
        self._macro.params.append(tok.value)

    def _add_macro_body(self, tok):
        ''' Adds a token to the current macro body, substituting references to parameters. '''
        if tok.value in self._macro.params:
            param_id = self._macro.get_param_id(tok.value)
            macro_token = tok(param_id, tok.line, tok.column, tok.source)
        else:
            macro_token = tok
        self._macro.body.append(macro_token)

    def _set_singlet_body(self, tok):
        self._macro.body.append(tok)
        self._end_macro_decl()

    def _add_token(self, tok):
        self._tokens_out.append(tok)

    def _is_singlet(self, tok):
        macro = self._macros.get(tok.value, None)
        return macro and macro.is_singlet()

    def _is_macro(self, tok):
        return tok.value in self._macros

    def reset(self):
        ''' Resets the parser state. '''
        self._macros = {}
        self.soft_reset()

    def soft_reset(self):
        ''' Resets the parser state for another pass at the token stream. '''
        self._tokens_out = []
        self._macro = None
        self._macro_args = []
        self._needs_another_pass = False
        super().reset()

    def parse(self, filename, max_passes=10):
        ''' Re-parse the input stream up to a set maximum numer of times. '''
        lexer = Lexer()
        self._tokens_out = lexer.parse(self.file_loader_fn(filename), source=filename)
        self._needs_another_pass = True
        for ii in range(max_passes):
            if self._needs_another_pass:
                tokens = self._tokens_out
            else:
                break
            self.soft_reset()
            super().parse(tokens)
        return self._tokens_out

    # TODO: get rid of parens for macro decl - make it a comma-list with the
    # name as the first arg
    def generate_grammar(self):
        return {
            'goal': (
                (Tok.include, nop, 'include_decl'),
                (Tok.macro, nop, 'macro_decl'),
                (Tok.const, nop,'singlet_decl'),
                (match_fn(self._is_singlet), self._insert_singlet, 'goal'),
                (match_fn(self._is_macro), self._start_macro_call, 'macro_arg'),
                (match_any, self._add_token, 'goal'),
                rule_end,
            ),

            'include_decl': (
                (Tok.string, self._include_file, 'goal'),
                self._error('Expected string argument for .include.'),
            ),

            'singlet_decl': (
                (Tok.ident, self._start_macro_decl, 'singlet_body'),
                self._error('Expected const name'),
            ),
            'singlet_body': (
                (match_any, self._set_singlet_body, 'goal'),
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
