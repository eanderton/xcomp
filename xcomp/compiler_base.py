# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

class CompilationError(Exception):
    def __init__(self, line, column, context, msg):
        super().__init__(f'{context} ({line}, {column}): {msg}')


class CompilerBase(object):
    def __init__(self, ctx_manager):
        self.ctx_manager = ctx_manager

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


