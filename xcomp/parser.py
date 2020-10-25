'''
Parser for the compiler.
'''

from oxeye.token import Token, TokenParser
from oxeye.pred import nop
from oxeye.rule import rule_end
from oxeye.match import *
from xcomp.model import *
from xcomp.lexer import Tok, Lexer
from xcomp.cpu6502 import *

class Parser6502(TokenParser):
    def _do_segment(self, name: Token):
        ''' Sets the current segment based on the token name. '''
        self._segment = self.segments[name.value]

    def _do_label(self, tokens):
        ''' Creates a label from a token. '''
        name = tokens[0].value
        label = Label(name)
        self._segment.code.append(label)

    def _start_words(self, _):
        pass

    def _start_bytes(self, _):
        pass

    def _start_op(self, head, name):
        pass

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

        # set parser state variables
        self._segment = self.segments['.text']
        self._op = None
        self._op_args = []

    def parse(self, tokens):
        super().parse(tokens)

    def generate_grammar(self):
        ''' Generates the grammar for the parser. '''
        op_names ={}
        return {
            'goal': (
                (Tok.byte, '_start_bytes', 'dataset'),
                (Tok.word, '_start_words', 'dataset'),
                (Tok.segment, '_do_segment', 'goal'),
                (match_seq([Tok.ident, ':']), '_do_label', 'goal'),
                (match_lut(op_names), '_start_op', 'op'),
                rule_end,
                self._error('unexpected token'),
            ),
        }
