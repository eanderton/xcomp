# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

import logging
import codecs
import cbmcodecs
from itertools import filterfalse
from functools import singledispatchmethod
from .model import *
from .parser import Parser
from .parser import ParseError
from .compiler_base import CompilerBase
from .preprocessor import PreProcessor
from .cpu6502 import AddressMode

log = logging.getLogger(__name__)


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

class Evaluator(CompilerBase):
    def __init__(self, data, ctx_manager):
        super().__init__(ctx_manager)
        self.data = data
        self.encoding = 'utf-8'
        self.fixups = []
        self.scope_stack = []

    def start_scope(self):
        self.scope_stack.append({})

    def end_scope(self):
        self.resolve_fixups()
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

    def resolve_fixups(self, must_pass=False):
        def attempt(fixup):
            try:
                self.resolve_expr(*fixup)
                if must_pass:
                    raise
                return True
            except:
                return False
        self.fixups[:] = filterfalse(attempt, self.fixups)


class Compiler(CompilerBase):
    def __init__(self, ctx_manager):
        super().__init__(ctx_manager)
        self.data = bytearray(0xFFFF)
        self.eval = Evaluator(self.data, ctx_manager)
        self.segments = {
            'zero': SegmentData(0x0000),
            'bss':  SegmentData(0x0100),
            'data': SegmentData(0x0200),
            'text': SegmentData(0x0800),
        }
        self.seg = self.segments['text']
        self.pragma = {}

    @singledispatchmethod
    def _compile(self, item):
        raise Exception(f'no defined compile handler for item: {type(item)}')

    @_compile.register
    def _compile_comment(self, comment: Comment):
        pass  # throw it away

    @_compile.register
    def _compile_bin(self, binfile: BinaryInclude):
        value = self.ctx_manager.get_text(binfile.filename, 'rb')
        start = self.seg.offset
        end = start + len(value)
        self.data[start:end] = value
        self.seg.offset = end

    @_compile.register
    def _compile_pragma(self, pragma: Pragma):
        self.pragma[pragma.name] = self.eval.eval(pragma.expr)

    @_compile.register
    def _compile_encoding(self, encoding: Encoding):
        try:
            codecs.getreader(encoding.name)
            self.eval.encoding = encoding.name
        except LookupError:
            self._error(encoding.pos, f'Invalid string codec "{encoding.name}"')

    @_compile.register
    def _compile_scope(self, scope: Scope):
        self.eval.start_scope()

    @_compile.register
    def _compile_end_scope(self, endscope: EndScope):
        self.eval.end_scope()

    @_compile.register
    def _compile_define(self, define: Define):
        if define.name in self.eval.scope:
            self._error(define.pos,
                    f'Identifier "{define.name}" is already defined in scope')
        self.eval.scope[define.name] = define

    @_compile.register
    def _compile_label(self, label: Label):
        if label.name in self.eval.scope:
            self._error(label.pos,
                    f'Identifier "{label.name}" is already defined in scope')
        self.eval.scope[label.name] = label
        label.addr = self.seg.offset

    @_compile.register
    def _compile_storage(self, storage: Storage):
        for ii in range(len(storage.items)):
            fixup = (None, self.seg.offset, storage.items[ii])
            try:
                self.eval.resolve_expr(*fixup)
            except Exception as e:
                self.eval.fixups.append(fixup)
            self.seg.offset += storage.width

    # TODO: patch to work with forward references
    @_compile.register
    def _compile_dim(self, dim: Dim):
        length = self.eval.eval(dim.length)
        init_bytes = []
        for item in dim.init:
            _, expr_bytes = self.eval.get_expr_bytes(item)
            init_bytes.extend(expr_bytes)
        init_len = len(init_bytes)
        end = self.seg.offset + length
        for ii in range(self.seg.offset, end, init_len):
            self.data[ii:ii+init_len] = init_bytes
        self.data[ii:end] = init_bytes[0:end-ii]
        self.seg.offset += length

    @_compile.register
    def _compile_segment(self, segment: Segment):
        self.seg = self.segments[segment.name]
        if segment.start is not None:
            self.seg.offset = self.eval.eval(segment.start)

    @_compile.register
    def _compile_op(self, op: Op):
        if op.arg:
            try:
                self.seg.offset += self.eval.resolve_expr(
                        op, self.seg.offset, op.arg)
            except:
                # Assume that the arg expression cannot be resolved w/o some
                # other label defined after this line.  Make the arg width
                # 16 bits and log a fixup to be resolved later
                op.promote16bits()
                self.eval.fixups.append([op, self.seg.offset, op.arg])
                self.seg.offset += op.width
        else:
            self.data[self.seg.offset] = op.value
            self.seg.offset += op.width

    def get_extents(self, segment_names):
        segment_names = segment_names or ['data', 'text']
        start = None
        end = None

        for name in segment_names:
            if name not in self.segments:
                raise Exception(f'Unknown segment name "{name}"')
            seg = self.segments[name]
            start = min(seg.start, start) if start else seg.start
            end = max(seg.end, end) if end else seg.end
        return (start, end)

    def compile(self, ast):
        self.eval.start_scope()
        for item in ast:
            self._compile(item)
        for fixup in self.eval.fixups:
            self.eval.resolve_expr(*fixup)
        self.eval.end_scope()

    def compile_file(self, filename):
        ast = PreProcessor(self.ctx_manager).parse(filename)
        self.compile(ast)
