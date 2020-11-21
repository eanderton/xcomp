from attr import attrib, attrs, Factory
from typing import *
from functools import singledispatchmethod
from xcomp.model import *
from xcomp.parser import Parser
from xcomp.reduce_parser import ParseError


class CompilationError(Exception):
    def __init__(self, line, column, context, msg):
        super().__init__(f'{context} ({line}, {column}): {msg}')


@attrs(auto_attribs=True, slots=True)
class SegmentData(object):
    offset: int = 0
    labels: Dict = Factory(dict)
    fixups: List = Factory(list)


@attrs(auto_attribs=True, slots=True)
class VirtualSegment(object):
    offset: int = 0
    labels: Dict = Factory(dict)
    fixups: List = Factory(list)

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


class Compiler(CompilerBase):
    def __init__(self, ctx_manager):
        self.reset()

    def reset(self):
        self.defs = {}
        self.segments = {
            'text': SegmentData,
            'data': SegmentData,
            'bss': VirtualSegment,
            'zero': VirtualSegment,
        }
        self.labels = {}
        self.fixups = []
        self.unresolved_labels = []

    @singledispatchmethod
    def _compile(self, item):
        raise Exception(f'no defined compile handler for item: {type(item)}')

    @_compile.register
    def _compile_label(self, label: Label):
        ofs = current_seg.offset
        self.current_seg.labels[label.name] = ofs
        self.labels[label.name] = ofs

    @_compile.register
    def _compile_storage(self, storage: Storage):
        current_seg.extend(x.bytes(ctx))

    @_compile.register
    def _compile_op(self, op: Op):
        # TODO: branch based on address mode
        # TODO: ensure enough information is stored to handle fixup errors on semantic pass
        current_seg.append(x.op.value)
        if x.arg:
            fixup, value = x.arg.eval(self)
            if fixup:
                fixups.append(fixup)
            current.seg.extend(value)

    def compile(self, ctx_name):
        # parse root file and pre-process
        ast = self._parse(ctx_name)

        self.current_seg = self.segments['text']
        ast = list(self._pre_process(ast, macros))

        # TODO: evaluation context that contains segments, current segment, and labels
        # TODO: eval() will have to return fixup information

        # reset current segment and compile
        current_seg = segments['text']
        current_seg.offset = 0x0800  # TODO: set some default
        for item in ast:
            self._compile(item)

        # apply fixups
        for seg in segments.values():
            for fixup in seg.fixups:
                pass #self.resolve_fixup(fixup)

        # TODO: semantic pass
