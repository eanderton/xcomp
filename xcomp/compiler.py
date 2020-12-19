# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

import logging
import codecs
import cbmcodecs
from functools import singledispatchmethod
from functools import partial
from itertools import filterfalse
from .model import *
from .eval import Evaluator
from .compiler_base import CompilerBase
from .preprocessor import PreProcessor

log = logging.getLogger(__name__)

# TODO: patch dim and var to work with forward references

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
    def __init__(self, ctx_manager):
        super().__init__(ctx_manager)
        self.data = bytearray(0xFFFF)
        self.eval = Evaluator(ctx_manager)
        self.segments = {
            'zero': SegmentData(0x0000),
            'bss':  SegmentData(0x0100),
            'data': SegmentData(0x0200),
            'text': SegmentData(0x0800),
        }
        self.seg = self.segments['text']
        self.pragma = {}
        self.fixups = []

    def resolve_expr(self, addr, expr):
        value, expr_bytes = self.eval.get_expr_bytes(expr)
        vlen = len(expr_bytes)
        for ii in range(vlen):
            self.data[addr + ii] = expr_bytes[ii]
        return vlen

    def resolve_op(self, opcode, addr, expr):
        value, expr_bytes = self.eval.get_expr_bytes(expr)
        vlen = len(expr_bytes)

        # operations can't take on more than 2 bytes as an argument
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

        # make sure we don't have too many bytes
        if vlen == 2:
            log.debug('promoting: %s %s', opcode.value, opcode.mode)
            if not opcode.promote16bits():
                self._error(expr.pos,
                        f'operation {opcode.name} cannot take a 16 bit value')
            log.debug('promoted to: %s %s', opcode.value, opcode.mode)

        # emit op byte
        self.data[addr] = opcode.value
        addr += 1

        # emit args and return effective length
        for ii in range(vlen):
            self.data[addr + ii] = expr_bytes[ii]
        return 1 + vlen

    def resolve_fixups(self, must_pass=False):
        def attempt(fixup):
            try:
                log.debug('fixing up: %s', fixup)
                fixup()
                return True
            except:
                if must_pass:
                    raise
                return False
        self.fixups[:] = filterfalse(attempt, self.fixups)

    def _repeat_init(self, length, init):
        """Dumps repetitions of init into memory at offset, up to length bytes."""
        init_bytes = []
        for item in init:
            _, expr_bytes = self.eval.get_expr_bytes(item)
            init_bytes.extend(expr_bytes)
        init_len = len(init_bytes)
        if init_len > 0:
            end = self.seg.offset + length
            for ii in range(self.seg.offset, end, init_len):
                self.data[ii:ii+init_len] = init_bytes
            self.data[ii:end] = init_bytes[0:end-ii]
        self.seg.offset += length

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
        self.resolve_fixups()
        self.eval.end_scope()

    @_compile.register
    def _compile_define(self, define: Define):
        self.eval.add_label(define.pos, define.name, define.expr)

    @_compile.register
    def _compile_label(self, label: Label):
        label.addr = self.seg.offset
        self.eval.add_label(label.pos, label.name, self.seg.offset)

    @_compile.register
    def _compile_storage(self, storage: Storage):
        for ii in range(len(storage.items)):
            fixup = partial(self.resolve_expr, self.seg.offset, storage.items[ii])
            try:
                fixup()
            except Exception as e:
                self.fixups.append(fixup)
            self.seg.offset += storage.width

    @_compile.register
    def _compile_dim(self, dim: Dim):
        length = self.eval.eval(dim.length)
        self._repeat_init(length, dim.init)

    @_compile.register
    def _compile_var(self, var: Var):
        self.eval.add_label(var.pos, var.name, self.seg.offset)
        length = self.eval.eval(var.length)
        self._repeat_init(length, var.init)

    @_compile.register
    def _compile_segment(self, segment: Segment):
        self.seg = self.segments[segment.name]
        if segment.start is not None:
            self.seg.offset = self.eval.eval(segment.start)

    @_compile.register
    def _compile_op(self, op: Op):
        if op.arg:
            fixup = partial(self.resolve_op, op, self.seg.offset, op.arg)
            try:
                self.seg.offset += fixup()
            except:
                # Assume that the arg expression cannot be resolved due to
                # a forward reference.  Make the arg width to ensure that
                # there is enough space to provide the argument and resolve
                # this fixup later.
                op.promote16bits()
                self.fixups.append(fixup)
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
        self.resolve_fixups(must_pass=True)
        self.eval.end_scope()

    def compile_file(self, filename):
        ast = PreProcessor(self.ctx_manager).parse(filename)
        self.compile(ast)
