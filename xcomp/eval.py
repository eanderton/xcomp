# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

import logging
from functools import singledispatchmethod
from .model import *
from .compiler_base import CompilerBase
from .cpu6502 import AddressMode

log = logging.getLogger(__name__)

# TODO: find a way to handle cyclic references

class Evaluator(CompilerBase):
    def __init__(self, ctx_manager):
        super().__init__(ctx_manager)
        self.encoding = 'utf-8'
        self.scope_stack = []

    def start_scope(self):
        self.scope_stack.append({})

    def end_scope(self):
        self.scope_stack.pop()

    @property
    def scope(self):
        return self.scope_stack[-1]

    def add_name(self, pos, name, item):
        if name in self.scope:
            self._error(pos,
                    f'Identifier "{name}" is already defined in scope')
        self.scope[name] = item

    @singledispatchmethod
    def eval(self, expr):
        return value

    @eval.register
    def _eval_int(self, expr: int):
        return expr

    @eval.register
    def _eval_name(self, expr: ExprName):
        value = None
        name = expr.value
        for scope in reversed(self.scope_stack):
            if name in scope:
                value = scope[name]
                break
        if value is None:
            self._error(expr.pos, f'Identifier {name} is undefined.')
        return self.eval(value)

    @eval.register
    def _eval_value(self, expr: ExprValue):
        return expr.value

    @eval.register
    def _eval_binary_op(self, expr:ExprBinaryOp):
        return expr.oper(self.eval(expr.left), self.eval(expr.right))

    @eval.register
    def _eval_unary_op(self, expr:ExprUnaryOp):
        return expr.oper(self.eval(expr.arg))

    @eval.register
    def _eval_string(self, expr:String):
        return expr.value

    def get_expr_bytes(self, expr):
        value = self.eval(expr)
        if isinstance(value, int):
            if is8bit(value):
                expr_bytes = [value]
            else:
                expr_bytes = [lobyte(value), hibyte(value)]
        elif isinstance(value, str):
            try:
                expr_bytes = stringbytes(value, self.encoding)
            except UnicodeError as e:
                self._error(expr.pos, str(e))
        else:
            self._error(expr.pos, f'value of type {type(value)} not supported.')
        log.debug('expr bytes %s %s %s', expr, value,
                ' '.join([f'{x:x}' for x in expr_bytes]))
        return value, expr_bytes


