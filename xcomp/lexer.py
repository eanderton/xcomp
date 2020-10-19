'''
Lexer for the compiler.
'''

from oxeye.token import Token, TokenLexer
from oxeye.rule import rule_fail, rule_end
from oxeye.match import match_rex, match_seq


class Tok(object):
    '''
    Containing namespace for token types.
    '''
    pass


# set elements in namespace
for x in ['ident', 'number', 'string', 'comment', 'segment',
        '.macro', '.endmacro', '.byte', '.word']:
    setattr(Tok, x[1:] if x.startswith('.') else x, Token(x))


class Lexer(TokenLexer):
    '''
    Lexer for TokenCalculator.  Serializes a text stream into a list of tokens.
    Line and column information is gathered and attached to tokens as they are
    generated.
    '''

    def _hex_value(self, prefix, value):
        self._token(int(value, 16), Tok.number, len(prefix) + len(value))

    def _float_value(self, value):
        self._token(float(value), Tok.number, len(value))

    def generate_grammar(self):
        return {
            'goal': (
                (match_seq('.byte'), Tok.byte, 'goal'),
                (match_seq('.word'), Tok.word, 'goal'),
                (match_seq('.zero'), Tok.segment, 'goal'),
                (match_seq('.text'), Tok.segment, 'goal'),
                (match_seq('.data'), Tok.segment, 'goal'),
                (match_seq('.bss'), Tok.segment, 'goal'),
                (match_seq('.macro'), Tok.macro, 'goal'),
                (match_seq('.endmacro'), Tok.endmacro, 'goal'),
                (match_rex(r'(\$|0x)([0-9a-fA-F]{2,4})'), self._hex_value, 'goal'),
                (match_rex(r'"((?:\\.|[^"\\])*)"'), Tok.string, 'goal'),
                (match_rex(r';\s*(.*\n|.*$)'), Tok.comment, 'goal'),
                (match_rex(r'([_a-zA-Z][_a-zA-Z0-9]*)'), Tok.ident, 'goal'),
                (match_rex(r'(\d+(?:\.\d+)?)'), self._float_value, 'goal'),
                {
                    '(': (self._token, 'goal'),
                    ')': (self._token, 'goal'),
                    '-': (self._token, 'goal'),
                    '+': (self._token, 'goal'),
                    '*': (self._token, 'goal'),
                    '/': (self._token, 'goal'),
                    ':': (self._token, 'goal'),
                    '=': (self._token, 'goal'),
                    '|': (self._token, 'goal'),
                    ',': (self._token, 'goal'),
                    ' ': (self._next, 'goal'),
                    '\r': (self._next, 'goal'),
                    '\t': (self._next, 'goal'),
                    '\v': (self._next, 'goal'),
                    '\n': (self._newline, 'goal'),
                },
                rule_end,
                self._error('unexpected token'),
            ),
        }
