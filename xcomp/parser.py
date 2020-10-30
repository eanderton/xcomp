'''
Parser for the compiler.
'''

from functools import partial
from oxeye.token import Token, TokenParser
from oxeye.pred import nop
from oxeye.rule import rule_end
from oxeye.match import *
from xcomp.model import *
from xcomp.lexer import Tok, Lexer
from xcomp.cpu6502 import *
from xcomp.model import *

class Parser6502(TokenParser):
    def _append(self, item):
        self._segment.code.append(item)

    def _do_segment(self, name: Token):
        ''' Sets the current segment based on the token name. '''
        self._segment = self.segments[name.value]

    def _do_label(self, tokens):
        ''' Creates a label from a token. '''
        name = tokens[0].value
        label = Label(name)
        self._append(Label(name))

    def _start_words(self, _):
        pass

    def _start_bytes(self, _):
        pass

    def _start_op(self, opcode):
        ''' Create an operation instnace in the current segment. '''
        pos = Position.create(self)
        self._op = Op(pos, opcode)
        self._segment.code.append(self._op)
        self._expr = []

    def _do_address_mode(self, mode, *tokens):
        self._op.mode = mode

    def reset(self):
        ''' Resets the parser state. '''

        # build default segments and set default to .text
        self.segments = {
            '.zero': Segment('.zero', 0),
            '.text': Segment('.text', 0),
            '.data': Segment('.data', 0),
            '.bss': Segment('.bss', 0),
        }

        # set parser state variables
        self._segment = self.segments['.text']
        self._opcode = None
        self._op_args = []
        super().reset()

    def parse(self, tokens):
        super().parse(tokens)

    def generate_grammar(self):
        ''' Generates the grammar for the parser. '''
        unary_ops = {
            '-': lambda x: -x,
            '>': lambda x: ((x & 0xFF00) >> 8),
            '<': lambda x: x & 0xFF,
            '^': lambda x: x ^ 0xFFFF,  # TODO; needs to consider width
        }

        binary_ops = {
            '/': lambda a,b: a / b,
            '*': lambda a,b: a * b,
            '-': lambda a,b: a - b,
            '+': lambda a,b: a + b,
            '|': lambda a,b: a | b,
            '&': lambda a,b: a & b,
        }

        def expr_parse(parent_state):
            term_state = parent_state + '_expr_term'
            oper_state = parent_state + '_expr_oper'
            return {
                term_state: (
                    ('(', '_push_group', parent_state),
                    (')', '_pop_group', term_state),
                    (match_lut(unary_ops), '_add_unary_expr', term_state),
                    (Tok.number, '_set_expr', oper_state),
                    (Tok.ident, '_set_expr', oper_state),
                    self._error('Expected expression'),
                ),
                oper_state: (
                    (')', '_pop_group', term_state),
                    (match_lut(binary_ops), '_add_binary_expr', term_state),
                    self._error('Expected operator'),
                ),
            }

        return {
            'goal': (
                (Tok.byte, '_start_bytes', 'dataset'),
                (Tok.word, '_start_words', 'dataset'),
                (Tok.segment, '_do_segment', 'goal'),
                (match_seq([Tok.ident, ':']), '_do_label', 'goal'),
                (match_lut(opcode_xref), '_start_op', 'op'),
                rule_end,
                self._error('unexpected token'),
            ),
        }
