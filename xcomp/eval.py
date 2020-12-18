
import logging
import codecs
import cbmcodecs
from functools import singledispatchmethod
from .model import *
from .parser import Parser
from .parser import ParseError
from .compiler_base import CompilerBase
from .cpu6502 import AddressMode

log = logging.getLogger(__name__)


class Evaluator(CompilerBase):
    def __init__(self, data, ctx_manager):
        super().__init__(ctx_manager)
        self.data = data
        self.encoding = 'utf-8'
        self.scope_stack = []

    def start_scope(self):
        self.scope_stack.append({})

    def end_scope(self):
        self.scope_stack.pop()

    @property
    def scope(self):
        return self.scope_stack[-1]

    @singledispatchmethod
    def eval(self, expr):
        return value

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
    def _eval_value(self, expr:ExprValue):
        return expr.value

    @eval.register
    def _eval_binary_op(self, expr:ExprBinaryOp):
        return expr.oper(self.eval(expr.left), self.eval(expr.right))

    @eval.register
    def _eval_unary_op(self, expr:ExprUnaryOp):
        return expr.oper(self.eval(expr.arg))

    @eval.register
    def _eval_define(self, expr:Define):
        return self.eval(expr.expr)

    @eval.register
    def _eval_label(self, expr:Label):
        return expr.addr

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
        return value, expr_bytes

    def resolve_expr(self, opcode, addr, expr):
        value, expr_bytes = self.get_expr_bytes(expr)
        vlen = len(expr_bytes)
        log.debug('expr bytes %s %s %s', f'${addr:x}', vlen,
                ' '.join([f'{x:x}' for x in expr_bytes]))

        # if resolving to an operation, handle bytes length and emit op byte
        width = 1
        if opcode:
            if vlen > 2:
                self._error(expr.pos,
                        f'Expresssion evalutes to {vlen} bytes; operations can only take up to 2.')

            # special case: reduce argument to a 8 bit relative offset
            if opcode.mode == AddressMode.relative:
                jmp = (value - addr - 2)
                if jmp > 127 or jmp < -128:
                    self._error(expr.pos,
                            f'Relative jump for {opcode.name} is out of range.')
                expr_bytes = [jmp & 0xFF]
                vlen = 1

            # special case: use single-byte address if that's all we have
            if opcode.mode in [AddressMode.zeropage, AddressMode.zeropage_x,
                    AddressMode.zeropage_y, AddressMode.immediate]:
                if lobyte(value) == value:
                    vlen = 1
                    log.debug('optimizing to single-byte arg %s %s %s', value,
                            vlen, expr_bytes)

            # make sure we don't have to many bytes
            if vlen == 2:
                log.debug('promoting: %s %s', opcode.value, opcode.mode)
                if not opcode.promote16bits():
                    self._error(expr.pos,
                            f'operation {opcode.name} cannot take a 16 bit value')
                log.debug('promoted to: %s %s', opcode.value, opcode.mode)

            # emit op byte
            self.data[addr] = opcode.value
            addr += 1
            #width = opcode.width

        # emit args and return effective length
        for ii in range(vlen):
            self.data[addr + ii] = expr_bytes[ii]
        return width + vlen


