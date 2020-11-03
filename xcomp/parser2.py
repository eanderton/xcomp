from itertools import chain
from parsimonious.grammar import Grammar, TokenGrammar
from xcomp.model import *
from xcomp.grammar import grammar as xcomp_grammar
from xcomp.grammar import ignore as xcomp_ignore
from xcomp.ast import ASTParser, ASTNode, Empty


class ParseException(Exception):
    def __init__(self, node, *args, **kwargs):
        self.node = node
        super().__init__(*args, **kwargs)

class Parser(ASTParser):

    def __init__(self):
        super().__init__(grammar_ebnf=xcomp_grammar,
                ignored=xcomp_ignore,
                unwrapped_exceptions=[ParseException])

    #def visit_goal(self, node, children):
    #    return children

    #def visit_core_syntax(self, node, children):
    #    return children[0]

    def visit_segment(self, node, children):
        name, addr = children
        if addr == Empty:
            addr = None
        return Segment(name.pos, name.text[1:], addr)

    def visit_include(self, node, children):
        start, filename = children
        return Include(start.pos, filename)

    def visit_def(self, node, children):
        start, name, expr = children
        return Macro(start.pos, name.value, body=[expr])

    def visit_macro(self, node, children):
        print('macro:', children)
        start, params, body, _ = children
        name, *params = tuple(params)
        if body == Empty:
            body = None
        return Macro(start.pos, name, params, body)

    def visit_macro_params(self, node, children):
        head, remain = children
        result = [head.value]
        if remain != Empty:
            result.extend(remain[0])
        return result

    ### STORAGE ###

    def visit_byte_storage(self, node, children):
        start, first, exprs = children
        return Storage(start.pos, 8, tuple(chain([first], *exprs)))

    def visit_word_storage(self, node, children):
        _, first, exprs = children
        return Storage(node.pos, 16, tuple(chain([first], *exprs)))

    ### STRING ###

    def visit_string(self, node, children):
        start, chars, _ = children
        return String(start.pos, ''.join(chars))

    def visit_stringchar(self, node, children):
        return node.text

    def visit_escapechar(self, node, children):
        _, ch = children
        value = {
            'r': '\r',
            'n': '\n',
            't': '\t',
            'v': '\v',
            '"': '"',
            '\\': '\\',
        }.get(ch.text, None)
        if value == None:
            raise ParseException(ch, f"Invalid escape sequence '\\{ch.text}'")
        return value

    ### NUMBER ###

    def visit_base2(self, node, children):
        start, match = children  # discard prefix
        return ExprValue(start.pos, int(match.text, base=2))

    def visit_base16(self, node, children):
        start, match = children  # discard prefix
        return ExprValue(start.pos, int(match.text, base=16))

    def visit_base10(self, node, children):
        return ExprValue(node.pos, int(node.text, base=10))

    ### EXPR ###

    def visit_ident(self, node, children):
        return ExprName(node.pos, node.text)
