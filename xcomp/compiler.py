# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

import codecs
import cbmcodecs
from itertools import filterfalse
from functools import singledispatchmethod
from .model import *
from .parser import Parser
from .parser import ParseError
from .compiler_base import CompilerBase
from .cpu6502 import AddressMode


class SegmentData(object):
    def __init__(self, default_start):
        self._start = None
        self._default_start = default_start
        self._end = None
        self._offset = default_start

    @property
    def start(self):
        if self._start == None:
            self._start = self._default_start
        return self._start

    @property
    def end(self):
        if self._end == None:
            self._end = self._offset
        return self._end

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value):
        self._offset = value
        if self._start == None:
            self._start = value
        else:
            self._start = min(self._start, value)
        if self._end == None:
            self._end = value
        else:
            self._end = max(self._end, value)


class Compiler(CompilerBase):
    def __init__(self, ctx_manager, debug=False):
        super().__init__(ctx_manager)
        self.debug = debug
        self.reset()

    def reset(self):
        self.encoding = 'utf-8'
        self.data = bytearray(0xFFFF)
        self.segments = {
            'zero': SegmentData(0x0000),
            'bss':  SegmentData(0x0100),
            'data': SegmentData(0x0200),
            'text': SegmentData(0x0800),
        }
        self.fixups = []
        self.scope_stack = []
        self.seg = self.segments['text']
        self.pragma = {}

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

    def resolve_expr(self, opcode, addr, expr):
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
        vlen = len(expr_bytes)

        if self.debug:
            print('expr bytes', f'${addr:x}', vlen, ' '.join([f'{x:x}' for x in expr_bytes]))

        # if resolving to an operation, handle bytes length and emit op byte
        width = 1
        if opcode:
            if vlen > 2:
                self._error(expr.pos,
                        f'Expresssion evalutes to {vlen} bytes; operations can only take up to 2.')
            if vlen == 2:
                opcode = opcode.promote16bits()
                if not opcode:
                    self._error(expr.pos, f'operation cannot take a 16 bit value')
            # special case: reduce argument to a 8 bit relative offset
            if opcode.mode == AddressMode.relative:
                jmp = (value - (addr + 2))
                if jmp > 127 or jmp < -128:
                    self._error(expr.pos,
                            f'Relative jump for {opcode.name} is out of range.')
                expr_bytes = [jmp & 0xFF]
                vlen = 1
            # emit op byte
            self.data[addr] = opcode.value
            addr += 1
            width = opcode.width

        # emit args and return effective length
        for ii in range(vlen):
            self.data[addr + ii] = expr_bytes[ii]
        return width + vlen

    def resolve_fixups(self):
        def attempt(fixup):
            try:
                self.resolve_expr(*fixup)
                return True
            except:
                return False
        self.fixups[:] = filterfalse(attempt, self.fixups)

    def start_scope(self):
        self.scope_stack.append({})

    def end_scope(self):
        self.resolve_fixups()
        self.scope_stack.pop()

    @singledispatchmethod
    def _compile(self, item):
        raise Exception(f'no defined compile handler for item: {type(item)}')

    @_compile.register
    def _compile_encoding(self, encoding: Encoding):
        try:
            codecs.getreader(encoding.name)
            self.encoding = encoding.name
        except LookupError:
            self._error(encoding.pos, f'Invalid string codec "{encoding.name}"')

    @_compile.register
    def _compile_scope(self, scope: Scope):
        self.start_scope()

    @_compile.register
    def _compile_end_scope(self, endscope: EndScope):
        self.end_scope()

    @_compile.register
    def _compile_define(self, define: Define):
        if define.name in self.scope:
            self._error(define.pos,
                    f'Identifier "{define.name}" is already defined in scope')
        self.scope[define.name] = define

    @_compile.register
    def _compile_label(self, label: Label):
        if label.name in self.scope:
            self._error(label.pos,
                    f'Identifier "{label.name}" is already defined in scope')
        self.scope[label.name] = label
        label.addr = self.seg.offset

    @_compile.register
    def _compile_storage(self, storage: Storage):
        for ii in range(len(storage.items)):
            fixup = (None, self.seg.offset, storage.items[ii])
            try:
                self.resolve_expr(*fixup)
            except Exception as e:
                self.fixups.append(fixup)
            self.seg.offset += storage.width

    @_compile.register
    def _compile_segment(self, segment: Segment):
        self.seg = self.segments[segment.name]
        if segment.start is not None:
            self.seg.offset = self.eval(segment.start)

    @_compile.register
    def _compile_op(self, op: Op):
        opcode = op.op
        if op.arg:
            try:
                self.seg.offset += self.resolve_expr(
                        opcode, self.seg.offset, op.arg)
            except:
                # Assume that the arg expression cannot be resolved w/o some
                # other label defined after this line.  Make the arg width
                # 16 bits and log a fixup to be resolved later
                fixup_opcode = opcode.promote16bits() or opcode
                self.fixups.append([
                        fixup_opcode, self.seg.offset, op.arg])
                self.seg.offset += fixup_opcode.width
        else:
            self.data[self.seg.offset] = opcode.value
            self.seg.offset += opcode.width

    def compile(self, ast):
        self.start_scope()
        for item in ast:
            self._compile(item)
        for fixup in self.fixups:
            self.resolve_expr(*fixup)
        self.end_scope()

