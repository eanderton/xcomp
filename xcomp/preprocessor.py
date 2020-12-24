# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

import logging
from functools import singledispatchmethod
from .model import *
from .parser import Parser
from .parser import ParseError
from .compiler_base import CompilerBase
from .compiler_base import FileContextException

log = logging.getLogger(__name__)

class PreProcessor(CompilerBase):
    '''Parses an input file and returns an AST stream representative of the parsed
       file data.

       The pre-processor implements the following "first pass" activites on the
       sourcecode:

       - Root file is parsed and evaluted for tokens that can be processed
       - .include directives are expanded to additional pre-processed output
       - .macro definitions are consumed
       - macro calls are substituted from their corresponding macros

       A single stream of tokens representative of the entire graph of files,
       included from the root file, is returned.
    '''

    def __init__(self, ctx_manager):
        super().__init__(ctx_manager)
        self.reset()

    def reset(self):
        self.macros = {}

    def _parse(self, ctx_name):
        parser = Parser()
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
        if len(call.args) != len(macro.params):
            log.debug('call: %s', call)
            log.debug('macro: %s', macro)
            self._error(call.pos,
                    f'Invalid number of arguments; expected {len(macro.params)}')
        yield Scope()
        for ii in range(len(call.args)):
            name = macro.params[ii]
            yield Define(Pos(0, 0), name, call.args[ii])
        for x in macro.body:
            yield x
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

