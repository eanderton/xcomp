import codecs
import cbmcodecs
from attr import attrib, attrs, Factory
from typing import *
from itertools import filterfalse
from functools import singledispatchmethod
from xcomp.model import *
from xcomp.parser import Parser
from xcomp.reduce_parser import ParseError
from xcomp.cpu6502 import AddressMode


class CompilationError(Exception):
    def __init__(self, line, column, context, msg):
        super().__init__(f'{context} ({line}, {column}): {msg}')


class CompilerBase(object):
    def _error(self, pos, msg):
        line, column = self._linecol(pos)
        raise CompilationError(line, column, pos.context, msg)

    def _linecol(self, pos):
        text = self.ctx_manager.get_text(pos.context)
        line = text.count('\n', 0, pos.start) + 1
        try:
            column = pos.start - text.rindex('\n', 0, pos.start)
        except ValueError:
            column = pos.start + 1
        return line, column


class PreProcessor(CompilerBase):
    def __init__(self, ctx_manager, debug=False):
        self.ctx_manager = ctx_manager
        self.debug = debug
        self.reset()

    def reset(self):
        self.macros = {}

    def _parse(self, ctx_name):
        parser = Parser()
        parser.debug = self.debug
        # TODO: handle duplicate include
        text = self.ctx_manager.get_text(ctx_name)
        return parser.parse(text, context=ctx_name)

    @singledispatchmethod
    def _process(self, item):
        yield item

    @_process.register
    def _process_include(self, include: Include):
        try:
            included_ast = self._parse(include.filename)
        except FileContextException as e:
            self._error(include.pos, str(e))
        for x in self._pre_process(included_ast):
            yield x

    @_process.register
    def _process_macro(self, macro: Macro):
        ''' Register macro definition. '''
        old_macro = self.macros.get(macro.name, None)
        if old_macro:
            old_pos = old_macro.pos
            line, column = self._linecol(old_pos)
            self._error(macro.pos,
                    f'Macro {macro.name} is already defined: {old_pos.context}({line}, {column})')
        self.macros[macro.name] = macro

    @_process.register
    def _process_maro_call(self, call: MacroCall):
        ''' Expand macro call to macro source with defines and scope tokens. '''
        macro = self.macros.get(call.name, None)
        if not macro:
            self._error(call.pos, f'Macro {call.name} is not defined')
        if len(call.args.values) != len(macro.params):
            self._error(call.args.pos,
                    f'Invalid number of arguments; expected {len(macro.params)}')
        yield Scope()
        body = macro.substitute(call.args)
        for y in self._pre_process(body):
            yield y
        yield EndScope()

    def _pre_process(self, ast):
        ''' Expand ast includes and macros into a single element stream. '''
        for x in ast:
            values = self._process(x)
            if values:
                for y in values:
                    yield y

    def parse(self, ctx_name):
        return self._pre_process(self._parse(ctx_name))


@attrs(auto_attribs=True, slots=True)
class SegmentData(object):
    offset: int
    data: list
    # TODO: provide property to write data here
    # TODO: capture start/end extents based on write activity


class Compiler(CompilerBase):
    def __init__(self, ctx_manager, debug=False):
        self.ctx_manager = ctx_manager
        self.debug = debug
        self.reset()

    def reset(self):
        self.encoding = 'utf-8'
        self.data = bytearray(0xFFFF)
        self.segments = {
            'text': SegmentData(0x0800, self.data),
            'data': SegmentData(0x0200, self.data),
            'bss':  SegmentData(0x0100, self.data),
            'zero': SegmentData(0x0000, self.data),
        }
        self.fixups = []
        self.scope_stack = []
        self.seg = self.segments['text']

    @property
    def scope(self):
        return self.scope_stack[-1]

    def resolve(self, name):
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None

    def eval_expr(self, expr):
        try:
            return expr.eval(self)
        except EvalException as e:
            self._error(e.pos, str(e))

    def resolve_expr(self, opcode, addr, expr):
        value = self.eval_expr(expr)
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
                self.resolve.expr(*fixup)
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
                    f'Identifier "{define.name}" is already defined in scope.')
        self.scope[define.name] = define

    @_compile.register
    def _compile_label(self, label: Label):
        if label.name in self.scope:
            self._error(label.pos,
                    f'Identifier "{label.name}" is already defined in scope.')
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
            self.seg.offset = self.eval_expr(segment.start)

    @_compile.register
    def _compile_op(self, op: Op):
        opcode = op.op
        if op.arg:
            try:
                self.seg.offset += self.resolve_expr(
                        opcode, self.seg.offset, op.arg)
            except:
                fixup_opcode = opcode.promote16bits() or opcode
                self.fixups.append([
                        fixup_opcode, self.seg.offset, op.arg])
                self.seg.offset += fixup_opcode.width
        else:
            self.data[self.seg.offset] = opcode.value
            self.seg.offset += opcode.width

    def compile(self, ast):
        self.seg = self.segments['text']
        self.start_scope()
        for item in ast:
            self._compile(item)
        for fixup in self.fixups:
            self.resolve_expr(*fixup)
        self.end_scope()
