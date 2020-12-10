# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

from functools import singledispatchmethod
from .printer import StylePrinter
from .model import *
from .cpu6502 import AddressMode

model_stylesheet = {
    'comment': {'color': 'green'},
    'directive': {'color': 'yellow', 'before': '    '},
    'scope': {'color': 'yellow'},
    'label': {'bold': True,},
    'string': {'color': 'cyan', 'before': '"', 'after': '"'},
    'operator': {},
    'ident': {},
    'number': {'color': '#AA44BB'},
    'call': {'after': ' '},
    'opcode': { 'before': '    '},
}


# TODO: add support for indentation
# TODO: add better comment support

class ModelPrinter(StylePrinter):
    def __init__(self, stream=None, stylesheet=None, style_defaults=None, ansimode=True):
        stylesheet = stylesheet if stylesheet is not None else model_stylesheet
        super().__init__(stream, stylesheet, style_defaults, ansimode)
        self.context = None

    @singledispatchmethod
    def print(self, item):
        return self.text(str(item)).nl()

    @print.register
    def _print_list(self, items: list):
        if not items:
            return
        for x in items[:-1]:
            self.print(x)
            self.text(', ')
        self.print(items[-1])
        return self

    @print.register
    def _print_tuple(self, items: tuple):
        self._print_list(list(items))
        return self

    @print.register
    def _print_pos(self, pos: Pos):
        if pos.context != self.context:
          self.comment(f'; {pos.context}').nl()
          self.context = pos.context
        return self

    @print.register
    def _print_bin(self, binfile: BinaryInclude):
        self.print(binfile.pos)
        self.directive('.bin ').ident(binfile.name)
        self.text(' ').string(binfile.filename).nl()

    @print.register
    def _print_dim(self, dim: Dim):
        self.print(dim.pos)
        self.directive('.dim ').print(dim.length).print(dim.init).nl()

    @print.register
    def _print_pragma(self, pragma: Pragma):
        self.print(pragma.pos)
        self.directive('.pragma ').ident(pragma.name)
        self.text(' ').print(pragma.expr).nl()

    @print.register
    def _print_scope(self, scope: Scope):
        self.print(scope.pos)
        self.scope('.scope').nl()
        return self

    @print.register
    def _print_endscope(self, endscope: EndScope):
        self.print(endscope.pos)
        self.scope('.endscope').nl()
        return self

    @print.register
    def _print_encoding(self, encoding: Encoding):
        self.print(encoding.pos)
        self.directive('.encoding ').string(encoding.name).nl()
        return self

    @print.register
    def _print_define(self, define: Define):
        self.print(define.pos)
        self.directive('.def ').ident(f'{define.name} ')
        self.print(define.expr)
        self.nl()
        return self

    @print.register
    def _print_label(self, label: Label):
        self.print(label.pos)
        self.label(f'{label.name}:').nl()
        return self

    @print.register
    def _print_macro_call(self, macro: MacroCall):
        self.print(macro.pos)
        self.call(macro.name)
        self.print(macro.args)
        return self

    @print.register
    def _print_storage(self, storage: Storage):
        self.print(storage.pos)
        if storage.width == 1:
            self.directive('.byte ')
        else:
            self.directive('.word ')
        self.print(storage.items)
        self.nl()
        return self

    @print.register
    def _print_segment(self, segment: Segment):
        self.print(segment.pos)
        self.directive(f'.{segment.name}')
        if segment.start is not None:
            self.text(' ').print(segment.start)
        self.nl()
        return self

    @print.register
    def _print_expr_value(self, expr: ExprValue):
        with self.number as p:
            if expr.base == 2:
                if expr.width == 16:
                    p.bold('%').text(f'{expr.value:016b}')
                else:
                    p.bold('%').text(f'{expr.value:08b}')
            elif expr.base == 16:
                if expr.width == 16:
                    p.bold('$').text(f'{expr.value:04x}')
                else:
                    p.bold('$').text(f'{expr.value:02x}')
            else:
                value = expr.value
                if expr.width == 16 and is8bit(value):
                    p.bold('!').text(str(value))
                else:
                    p.text(str(value))
        return self

    @print.register
    def _print_op(self, op: Op):
        self.print(op.pos)
        mode = op.mode
        arg = op.arg

        # end early if there's no arg, otherwise emit a separator
        self.opcode(op.name)
        if mode == AddressMode.implied:
            return self.nl()
        self.text(' ')

        # all other modes
        if mode == AddressMode.accumulator:
            self.ident('a')
        if mode == AddressMode.absolute:
            self.print(arg)
        if mode == AddressMode.absolute_x:
            self.print(arg).text(', ').ident('x')
        if mode == AddressMode.absolute_y:
            self.print(arg).text(', ').ident('y')
        if mode == AddressMode.immediate:
            self.text('#').print(arg)
        if mode == AddressMode.indirect:
            self.text('(').print(arg).text(')')
        if mode == AddressMode.indirect_x:
            self.text('(').print(arg).text(', x)')
        if mode == AddressMode.indirect_y:
            self.text('(').print(arg).text('), y')
        if mode == AddressMode.relative:
            self.print(arg)
        if mode == AddressMode.zeropage:
            self.print(arg)
        if mode == AddressMode.zeropage_x:
            self.print(arg).text(', x')
        if mode == AddressMode.zeropage_y:
            self.print(arg).text(', y')
        return self.nl()

    @print.register
    def _print_expr_binary_op(self, expr: ExprBinaryOp):
        return self.print(expr.left).text(' ').oper(expr.opname) \
                .text(' ').print(expr.right)

    @print.register
    def _print_expr_unary_op(self, expr: ExprUnaryOp):
        return self.oper(expr.opname).print(expr.arg)

    @print.register
    def _print_exprname(self, expr: ExprName):
        return self.ident(expr.value)

    def print_ast(self, ast):
        for x in ast:
            self.print(x)
