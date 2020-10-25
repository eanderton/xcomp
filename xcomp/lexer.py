'''
Lexer for the compiler.
'''

from attr import attrib, attrs, Factory
from typing import *
from oxeye.token import Token, TokenLexer, TokenParser
from oxeye.rule import rule_fail, rule_end
from oxeye.match import *

# TODO: build a real opcode table
mock_opcodes = ['lda', 'pha', 'pla', 'adc']


class ExtToken(Token):
    def __init__(self, *args, **kwargs):
        self.hints = {}
        super().__init__(*args, **kwargs)


class Tok(object):
    '''
    Containing namespace for token types.
    '''
    pass


# set elements in namespace
for x in ['op', 'ident', 'number', 'string', 'comment', 'segment',
        '.include', '.const', '.macro', '.endmacro',
        '.byte', '.word']:
    setattr(Tok, x[1:] if x.startswith('.') else x, ExtToken(x))


class Lexer(TokenLexer):
    '''
    Lexer for TokenCalculator.  Serializes a text stream into a list of tokens.
    Line and column information is gathered and attached to tokens as they are
    generated.
    '''

    def _hex_value8(self, prefix, value):
        tok = self._token(int(value, 16), Tok.number, len(prefix) + len(value))
        tok.hints['width'] = 8
        tok.hints['hex'] = True

    def _hex_value16(self, prefix, value):
        tok = self._token(int(value, 16), Tok.number, len(prefix) + len(value))
        tok.hints['width'] = 16
        tok.hints['hex'] = True

    def _int_value(self, value):
        v = int(value)
        tok = self._token(v, Tok.number, len(value))
        if v > 65535 or v < -32768:
            self._error('Integer is out of range for a 16-bit value')
        if v > 0xFF or v < -128:
            tok.hints['width'] = 16
        else:
            tok.hints['width'] = 8
        tok.hints['hex'] = False

   #TODO: attach comments to following whole line comments token as metadata
   #TODO: attach end-line comments to previous token as metadata
   #TODO: provide width-hints for numbers (8-bit, 16-bit)

    def generate_grammar(self):
        opcode_rules = tuple([(match_seq(x), Tok.op, 'goal') for x in mock_opcodes])
        return {
            'goal': opcode_rules + (
                (match_seq('.byte'), Tok.byte, 'goal'),
                (match_seq('.word'), Tok.word, 'goal'),
                (match_seq('.zero'), Tok.segment, 'goal'),
                (match_seq('.text'), Tok.segment, 'goal'),
                (match_seq('.data'), Tok.segment, 'goal'),
                (match_seq('.bss'), Tok.segment, 'goal'),
                (match_seq('.include'), Tok.include, 'goal'),
                (match_seq('.const'), Tok.const, 'goal'),
                (match_seq('.macro'), Tok.macro, 'goal'),
                (match_seq('.endmacro'), Tok.endmacro, 'goal'),

                (match_rex(r'(\$|0x)([0-9a-fA-F]{3,4})'), self._hex_value16, 'goal'),
                (match_rex(r'(\$|0x)([0-9a-fA-F]{1,2})'), self._hex_value8, 'goal'),
                (match_rex(r'"((?:\\.|[^"\\])*)"'), Tok.string, 'goal'),
                (match_rex(r';\s*(.*)(?=\n|$)'), self._newline, 'goal'),
                (match_rex(r'([_a-zA-Z][_a-zA-Z0-9]*)'), Tok.ident, 'goal'),
                (match_rex(r'(\d+)'), self._int_value, 'goal'),

                (match_set('()-+*/^|,'), self._token, 'goal'),
                (match_set(' \r\t\v'), self._next, 'goal'),
                (match_seq('\n'), self._newline, 'goal'),

                rule_end,
                self._error('Unexpected token'),
            ),
        }

class TokenPrinter(TokenParser):
    '''
    Pretty-printer for a token stream.

    Functions as a debugging tool and as a code formatter.
    '''

    def __init__(self, indent_amount=4):
        self._indent_amount = indent_amount
        super().__init__()

    def reset(self):
        self._output = []
        self._line = []
        self._indent = 0
        super().reset()

    def _append(self, value):
        if not self._line:
            self._line.append(' ' * self._indent)
        self._line.append(value)

    def _end(self):
        ''' Ends a line and adds it to the output set. '''
        if self._line:
            self._output.append(''.join(self._line).rstrip())
            self._line = []

    def _token(self, tok):
        ''' Appends a token value to the current line. '''
        self._append(tok.value)

    def _number(self, tok):
        if tok.name == 'number':
            if tok.hints['hex']:
                if tok.hints['width'] == 16:
                    v = f'0x{tok.value:04x}'
                else:
                    v = f'0x{tok.value:02x}'
            else:
                v = str(tok.value)
        else:
            v = tok.value
        self._append(v)

    def _sep(self, tok):
        ''' Emit a token with trailing whitespace (separator). '''
        self._token(tok)
        self._line.append(' ')

    def _start(self, tok):
        ''' End line and start a new line. '''
        self._end()
        self._sep(tok)

    def _single(self, tok):
        ''' Emit a token on a single line. '''
        self._start(tok)
        self._end()

    def _indent_start(self, tok):
        ''' Starts an indented section. '''
        self._start(tok)
        self._indent += self._indent_amount

    def _indent_end(self, tok):
        ''' Ends an indented section. '''
        self._indent -= self._indent_amount
        self._single(tok)

    def parse(self, tokens):
        ''' Transform a token stream into a series of text lines. '''
        super().parse(tokens)
        if self._output:
            self._end()
        return '\n'.join(self._output)

    def generate_grammar(self):
        return {
            'goal': (
                (Tok.segment, self._single, 'goal'),
                (Tok.byte, self._start, 'goal'),
                (Tok.word, self._start, 'goal'),
                (Tok.op, self._start, 'goal'),
                (Tok.include, self._start, 'goal'),
                (Tok.const, self._start, 'goal'),
                (Tok.macro, self._indent_start, 'goal'),
                (Tok.endmacro, self._indent_end, 'goal'),
                (Tok.number, self._number, 'goal'),
                (',', self._sep, 'goal'),
                (match_any, self._token, 'goal'),
                rule_end,
                self._error('Unexpected token'),
            ),
        }
