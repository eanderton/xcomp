'''
Lexer for the compiler.
'''

from attr import attrib, attrs, Factory
from typing import *
from oxeye.token import Token, TokenLexer, TokenParser
from oxeye.pred import nop
from oxeye.rule import rule_fail, rule_end
from oxeye.match import *
from xcomp.cpu6502 import *

class ExtToken(Token):
    def __init__(self, *args, **kwargs):
        self.meta = {}
        super().__init__(*args, **kwargs)


class Tok(object):
    '''
    Containing namespace for token types.
    '''
    op = ExtToken('op')
    ident = ExtToken('ident')
    number = ExtToken('number')
    string = ExtToken('string')
    comment = ExtToken('comment')
    segment = ExtToken('segment')
    include = ExtToken('.include')
    const = ExtToken('.const')
    macro = ExtToken('.macro')
    endmacro = ExtToken('.endmacro')
    byte = ExtToken('.byte')
    word = ExtToken('.word')


# LUT for escape sequences used by the tokenizer
escape_chars = {
    't': '\t',
    'r': '\r',
    'n': '\n',
    'v': '\v',
    '\\': '\\',
}


class Lexer(TokenLexer):
    '''
    Lexer for TokenCalculator.  Serializes a text stream into a list of tokens.
    Line and column information is gathered and attached to tokens as they are
    generated.
    '''

    def reset(self):
        self._string = []
        super().reset()

    def _hex_value8(self, prefix, value):
        tok = self._token(int(value, 16), Tok.number, len(prefix) + len(value))
        tok.meta['width'] = 8
        tok.meta['hex'] = True

    def _hex_value16(self, prefix, value):
        tok = self._token(int(value, 16), Tok.number, len(prefix) + len(value))
        tok.meta['width'] = 16
        tok.meta['hex'] = True

    def _int_value(self, value):
        v = int(value)
        tok = self._token(v, Tok.number, len(value))
        if v > 65535 or v < -32768:
            self._error('Integer is out of range for a 16-bit value')
        if v > 0xFF or v < -128:
            tok.meta['width'] = 16
        else:
            tok.meta['width'] = 8
        tok.meta['hex'] = False

    def _string_append(self, value):
        self._string.append(value)

    def _string_end(self, _):
        value = ''.join(self._string)
        self._token(value, Tok.string, len(value) + 2)
        self._string = []

   #TODO: attach comments to following whole line comments token as metadata
   #TODO: attach end-line comments to previous token as metadata

    def generate_grammar(self):
        opcode_rules = tuple([(match_seq(x), Tok.op, 'goal') for x in opcode_xref.keys()])
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
                (match_seq('"'), nop, 'string_char'),

                (match_rex(r'(\$|0x)([0-9a-fA-F]{3,4})'), '_hex_value16', 'goal'),
                (match_rex(r'(\$|0x)([0-9a-fA-F]{1,2})'), '_hex_value8', 'goal'),
                (match_rex(r';\s*(.*)(?=\n|$)'), '_newline', 'goal'),
                (match_rex(r'([_a-zA-Z][_a-zA-Z0-9]*)'), Tok.ident, 'goal'),
                (match_rex(r'(\d+)'), '_int_value', 'goal'),

                (match_set('()-+*/^|&,#<>:'), '_token', 'goal'),
                (match_set(' \r\t\v'), '_next', 'goal'),
                (match_seq('\n'), '_newline', 'goal'),

                rule_end,
                self._error('Unexpected token'),
            ),
            'string_char': (
                (match_seq('"'), '_string_end', 'goal'),
                (match_seq('\\'), nop, 'escape_char'),
                (match_any, '_string_append', 'string_char'),
                self._error('Expected closing " for string'),
            ),
            'escape_char': (
                (match_lut(escape_chars), '_string_append', 'string_char'),
                self._error('Unknown string escape squence'),
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
        self._indent = 1
        super().reset()

    def _append(self, value):
        if not self._line:
            self._line.append(' ' * (self._indent * self._indent_amount))
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
            if tok.meta['hex']:
                if tok.meta['width'] == 16:
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
        self._append(' ')

    def _start(self, tok):
        ''' End line and start a new line. '''
        self._end()
        self._sep(tok)

    def _single(self, tok):
        ''' Emit a token on a single line. '''
        self._start(tok)
        self._end()

    def _label(self, tokens):
        self._end()
        self._indent = 0
        self._append(tokens[0].value + ':')
        self._indent = 1
        self._end()

    def _macro_start(self, tok):
        ''' Starts an indented section. '''
        self._indent = 0
        self._start(tok)
        self._indent = 2

    def _macro_end(self, tok):
        ''' Ends an indented section. '''
        self._indent = 0
        self._single(tok)
        self._indent = 1

    def parse(self, tokens):
        ''' Transform a token stream into a series of text lines. '''
        super().parse(tokens)
        if self._output:
            self._end()
        return '\n'.join(self._output)

    def generate_grammar(self):
        return {
            'goal': (
                (match_seq([Tok.ident, ':']), '_label', 'goal'),
                (Tok.segment, '_single', 'goal'),
                (Tok.byte, '_start', 'goal'),
                (Tok.word, '_start', 'goal'),
                (Tok.op, '_start', 'goal'),
                (Tok.include, '_start', 'goal'),
                (Tok.const, '_start', 'goal'),
                (Tok.macro, '_macro_start', 'goal'),
                (Tok.endmacro, '_macro_end', 'goal'),
                (Tok.number, '_number', 'goal'),
                (',', '_sep', 'goal'),
                (match_any, '_token', 'goal'),
                rule_end,
                self._error('Unexpected token'),
            ),
        }
