'''
Parser for the compiler.
'''

from oxeye.token import Token, TokenParser
from oxeye.pred import nop
from oxeye.rule import rule_end
from oxeye.match import match_peek, match_any
from xcomp.model import *
from xcomp.lexer import Tok, Lexer

class Parser(TokenParser):
    def _segment(self, name: Token):
        ''' Sets the current segment based on the token name. '''
        self._segment = self.segments[name.value]

    def _label(self, name: Token):
        ''' Creates a label from a token. '''
        label = Label()
        self._segment.code.append(label)
        self.name_table[name.value] = label
        self._stash = None

    def _do_stash(self, tok: Token):
        ''' Stash a token for later use. '''
        print('stashing: ', tok.value)
        self._stash = tok

    def _op_zero(self, name: Token):
        ''' Builds an operation with zero args. '''
        self._segment.code.append(Op(name))

    def _op_one(self, name: Token):
        ''' Builds an operation with one arg. '''
        self._segment.code.append(Op(name, self._arg1))

    def _op_two(self, name: Token):
        ''' Builds an operation with two args. '''
        self._segment.code.append(Op(name, self._arg1, self._arg2))

    def _macro_decl(self, _):
        name = self._stash.value
        self._macros[name] = Macro(name, self._macro_args)
        self._stash = None
        self._macro_args = []

    def _macro_call(self, _):
        name = self._stash.value
        self._macros[name] = MacroCall(name, self._macro_args)
        self._stash = None
        self._macro_args = []

    def reset(self):
        ''' Resets the parser state. '''

        super().reset()

        # build default segments and set default to .text
        self.segments = {
            '.zero': Segment('.zero', 0),
            '.text': Segment('.text', 0),
            '.data': Segment('.data', 0),
            '.bss': Segment('.bss', 0),
        }

        # set up name table
        self.name_table = {
            '.zero': self.segments['.zero'],
            '.text': self.segments['.text'],
            '.data': self.segments['.data'],
            '.bss': self.segments['.bss'],
        }

        # macro management
        self._macros = {}

        # set parser state variables
        self._segment = self.segments['.text']
        self._stash = None
        self._arg1 = None
        self._arg2 = None
        self._macro_body = []
        self._macro_args = []

    def parse(self, asm_source):
        lexer = Lexer()
        lexer.parse(asm_source)
        self._tokens = lexer.tokens  # debug
        super().parse(lexer.tokens)

    def generate_grammar(self):
        ''' Generates the grammar for the parser. '''
        return {
            'goal': (
                {
                    Tok.comment: (nop, 'goal'),
                    Tok.macro: (nop, 'macro_decl'),
                    Tok.segment: (self._segment, 'goal'),
                    #TODO: operations
                    'nop': (self._op_zero, 'goal'),
                    Tok.ident: (self._do_stash, 'ident'),
                },
                rule_end,
                self._error('unexpected token'),
            ),
            'macro_decl': (
                (Tok.ident, self._do_stash, 'macro_start_params'),
                self._error('Expected macro name'),
            ),
            'macro_start_params': (
                ('(', nop, 'macro_params'),
                (match_peek, self._macro_decl, 'goal'),
            ),
            'macro_params': (
                # TODO: params
                (')', nop, 'macro_body'),
                self._error('Expected closing ")" in macro call'),
            ),
            'macro_body': (
                (Tok.endmacro, self._macro_decl, 'goal'),
                # TODO: complete macro capture
                (match_any, nop, 'macro_body'),
            ),
            'ident': (
                (':', self._label, 'goal'),
                ('(', nop, 'macro_args'),
                (match_peek, self._macro_call, 'goal'),
                self._error('Expected end of macro'),
            ),
            'macro_args': (
                # TODO: arguments
                (')', self._macro_call, 'goal'),
                self._error('Expected closing ")" in macro call'),
            ),
        }
