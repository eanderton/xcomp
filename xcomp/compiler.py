# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

import logging
import codecs
from functools import singledispatchmethod
from itertools import filterfalse
from .model import *
from .eval import Evaluator
from .compiler_base import CompilerBase
from .preprocessor import PreProcessor

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
        self.fixups = []

    def resolve_fixups(self, must_pass=False):
        def attempt(fixup):
            try:
                log.debug('fixing up: %s', fixup)
                self.eval.resolve_expr(*fixup)
                return True
            except:
                if must_pass:
                    raise
                return False
        self.fixups[:] = filterfalse(attempt, self.fixups)

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
                self.fixups.append(fixup)
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
                self.fixups.append([op, self.seg.offset, op.arg])
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
