# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

import os
from attr import attrs
from attr import Factory
from typing import *

class FileContextException(Exception):
    pass


@attrs(auto_attribs=True, slots=True)
class FileContextManager():
    include_paths: list = Factory(list)
    files: Dict = Factory(dict)

    def search_file(self, filename):
        for inc in self.include_paths:
            test = os.path.expanduser(os.path.join(inc, filename))
            if os.path.isfile(test):
                return test
        return None

    def get_text(self, filename):
        if filename not in self.files:
            full_filename = self.search_file(filename)
            if not full_filename:
                raise FileContextException(
                        f'Cannot find "{filename}" on any configured search path.')
            with open(full_filename) as f:
                self.files[filename] = f.read()
        return self.files[filename]


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


