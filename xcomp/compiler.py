from attr import attrib, attrs, Factory
from typing import *
from itertools import filterfalse
from functools import singledispatchmethod
from xcomp.model import *
from xcomp.parser import Parser
from xcomp.reduce_parser import ParseError


class CompilationError(Exception):
    def __init__(self, line, column, context, msg):
        super().__init__(f'{context} ({line}, {column}): {msg}')


class CompilerBase(object):
    def _error(self, pos, msg):
        line, column = self._linecol(pos)
        raise CompilerError(pos, line, column, msg)

    def _linecol(self, pos):
        text = self.ctx_manager.get_text(pos.context)
        line = text.count('\n', 0, pos.start) + 1
        try:
            column = pos.start - text.rindex('\n', 0, pos.start)
        except ValueError:
            column = pos.start + 1
        return line, column


class PreProcessor(CompilerBase):
    def __init__(self, ctx_manager):
        self.ctx_manager = ctx_manager
        self.reset()

    def reset(self):
        self.macros = {}

    def _parse(self, ctx_name):
        parser = Parser()
        # TODO: handle duplicate include
        text = self.ctx_manager.get_text(ctx_name)
        return parser.parse(text)

    @singledispatchmethod
    def _process(self, item):
        yield item

    @_process.register
    def _process_include(self, include: Include):
        included_ast = self._parse(include.filename)
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
    offset: int = 0
    data: bytearray = Factory(bytearray)


@attrs(auto_attribs=True, slots=True)
class VirtualSegment(object):
    start: int = 0
    offset: int = 0

    @property
    def data(self):
        raise Exception('not allowed')


class Compiler(CompilerBase):
    def __init__(self):
        self.reset()

    def reset(self):
        self.data = bytearray(0xFFFF)
        self.segments = {
            'text': SegmentData(0x0800, self.data),
            'data': SegmentData(0x0200, self.data),
            'bss':  VirtualSegment(0x0100),
            'zero': VirtualSegment(0x0000),
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

    def resolve_expr(self, width, addr, expr):
        value = expr.eval(self)
        if isinstance(value, int):
            if width == 1:
                if lobyte(value) != value:
                    self.error(expr.pos,
                            f'Expression value too large for a single byte.')
                expr_bytes = [value]
            else:
                expr_bytes = [lobyte(value), hibyte(value)]
        else:
            self.error(expr.pos, f'value of type {type(value)} not supported.')
        for ii in range(len(expr_bytes)):
            self.data[addr + ii] = expr_bytes[ii]

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
    def _compile_scope(self, scope: Scope):
        self.start_scope()

    @_compile.register
    def _compile_end_scope(self, endscope: EndScope):
        self.end_scope()

    @_compile.register
    def _compile_define(self, define: Define):
        if define.name in self.scope:
            self.error(define.pos,
                    f'Identifier "{define.name}" is already defined in scope.')
        self.scope[define.name] = define

    @_compile.register
    def _compile_label(self, label: Label):
        if label.name in self.scope:
            self.error(label.pos,
                    f'Identifier "{label.name}" is already defined in scope.')
        self.scope[label.name] = label
        label.addr = self.seg.offset

    @_compile.register
    def _compile_storage(self, storage: Storage):
        for ii in range(len(storage.width)):
            fixup = (storage.width, self.seg.offset, storage.elem[ii])
            try:
                self.resolve_expr(*fixup)
            except:
                # TODO: allow this?  if an expression can't be
                # resolved at this point, it may not be possible to
                # handle later due to shifting the expression width
                self.fixups.append(fixup)
            self.seg.offset += storage.byte_width

    @_compile.register
    def _compile_op(self, op: Op):
        self.data[self.seg.offset] = op.op.value
        self.seg.offset += 1
        if op.arg:
            fixup = (op.op.arg_width, self.seg.offset, op.arg)
            try:
                self.resolve_expr(*fixup)
            except Exception as e:
                raise e
                self.fixups.append(fixup)
        self.seg.offset += op.op.arg_width

    def compile(self, ast):
        self.seg = self.segments['text']
        self.start_scope()
        for item in ast:
            self._compile(item)
        self.end_scope()

        # TODO: evalute incomplete fixups
