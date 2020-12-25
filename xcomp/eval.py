# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

import logging
from typing import *
from attr import attrs
from attr import Factory
from functools import singledispatchmethod
from .model import *
from .compiler_base import CompilerBase
from .cpu6502 import AddressMode

log = logging.getLogger(__name__)

# TODO: provide recursive context for eval failures


@attrs(auto_attribs=True)
class FixupExpr(object):
    pos: Pos
    scope_stack: List
    expr: Expr


class Evaluator(CompilerBase):
    def __init__(self, ctx_manager):
        super().__init__(ctx_manager)
        self.encoding = 'utf-8'
        self.scope_stack = []
        self.namespace_stack = []

    def start_scope(self, namespace=None):
        self.scope_stack.append({})
        self.namespace_stack.append(namespace)

    def end_scope(self, merge=False):
        head = self.scope_stack.pop()
        self.namespace_stack.pop()
        if merge and len(self.scope_stack):
            self.scope.update(head)
        return head

    @property
    def scope(self):
        return self.scope_stack[-1]

    def add_name(self, pos, name, item):
        namespace = list([x for x in self.namespace_stack if x is not None])
        realname = '.'.join(namespace + [name])
        if realname in self.scope:
            self._error(pos,
                    f'Identifier "{realname}" is already defined in scope')
        self.scope[realname] = item

    def get_fixup(self, expr):
        return FixupExpr(expr.pos, self.scope_stack.copy(), expr)

    @singledispatchmethod
    def _eval(self, expr):
        raise Exception('cannot eval expression of type {type(expr)}')

    @_eval.register
    def _eval_int(self, expr: int):
        return expr

    @_eval.register
    def _eval_fixup(self, fixup: FixupExpr):
        try:
            old_stack = self.scope_stack
            self.scope_stack = fixup.scope_stack
            return self.eval(fixup.expr)
        finally:
            self.scope_stack = old_stack

    @_eval.register
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

    @_eval.register
    def _eval_value(self, expr: ExprValue):
        return expr.value

    @_eval.register
    def _eval_binary_op(self, expr:ExprBinaryOp):
        return expr.oper(self.eval(expr.left), self.eval(expr.right))

    @_eval.register
    def _eval_unary_op(self, expr:ExprUnaryOp):
        return expr.oper(self.eval(expr.arg))

    @_eval.register
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

    def eval(self, expr):
        try:
            return self._eval(expr)
        except RecursionError as e:
            self._error(expr.pos,
                    f'cyclic reference when evaluating expression')
