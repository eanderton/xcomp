# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

import os
from abc import *
from attr import attrib
from attr import attrs
from attr import Factory
from typing import *
from .cpu6502 import *
from .utils import *
from .reduce_parser import Pos
from .reduce_parser import NullPos


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


@attrs(auto_attribs=True)
class Encoding(object):
    pos: Pos
    name: str


class String(object):
    def __init__(self, pos, *chars):
        self.pos = pos
        self.value = ''.join(chars)


@attrs(auto_attribs=True)
class Include(object):
    pos: Pos
    filename: String


class Expr(ABC):
    pass


@attrs(auto_attribs=True)
class Label(Expr):
    pos: Pos
    name: str
    addr: int = 0


@attrs(auto_attribs=True)
class ExprUnaryOp(Expr):
    pos: Pos
    arg: Expr
    opname = '?'

    @abstractmethod
    def oper(self, a):
        pass


class Expr8(ExprUnaryOp):
    opname = ''
    def oper(self, a):
        return a

class Expr16(ExprUnaryOp):
    opname = '!'
    def oper(self, a):
        return a


class ExprNegate(ExprUnaryOp):
    opname = '-'
    def oper(self, a):
        return -a


class ExprLobyte(ExprUnaryOp):
    opname = '<'
    def oper(self, a):
        return lobyte(a)


class ExprHibyte(ExprUnaryOp):
    opname = '>'
    def oper(self, a):
        return hibyte(a)


@attrs(auto_attribs=True)
class ExprBinaryOp(Expr):
    pos: Pos
    left: Expr
    right: Expr
    opname = '?'


class ExprAdd(ExprBinaryOp):
    opname = '+'
    def oper(self, a, b):
        return a + b


class ExprSub(ExprBinaryOp):
    opname = '-'
    def oper(self, a, b):
        return a - b


class ExprMul(ExprBinaryOp):
    opname = '*'
    def oper(self, a, b):
        return a * b


class ExprDiv(ExprBinaryOp):
    opname = '/'
    def oper(self, a, b):
        return a / b


class ExprPow(ExprBinaryOp):
    opname = '^'
    def oper(self, a, b):
        return a ^ b


class ExprOr(ExprBinaryOp):
    opname = '|'
    def oper(self, a, b):
        return a | b


class ExprAnd(ExprBinaryOp):
    opname = '&'
    def oper(self, a, b):
        return a & b


@attrs(auto_attribs=True)
class ExprValue(Expr):
    pos: Pos
    value: int
    base: int = 10
    width: int = 8


@attrs(auto_attribs=True)
class ExprName(Expr):
    pos: Pos
    value: str


@attrs(auto_attribs=True)
class Define(Expr):
    pos: Pos
    name: str
    expr: Expr


@attrs(auto_attribs=True)
class Scope(object):
    pos: Pos = NullPos


@attrs(auto_attribs=True)
class EndScope(object):
    pos: Pos = NullPos


@attrs(auto_attribs=True)
class Fragment(object):
    pos: Pos
    body: List[Any] = Factory(list)


@attrs(auto_attribs=True)
class Macro(object):
    pos: Pos
    name: str
    params: tuple
    body: Fragment


@attrs(auto_attribs=True)
class MacroCall(object):
    pos: Pos
    name: str
    args: tuple


@attrs(auto_attribs=True)
class Op(object):
    pos: Pos
    name: str
    mode: AddressMode
    value: int
    arg: Expr = None

    def promote16bits(self):
        new_mode = addressmode_8to16.get(self.mode, None)
        if new_mode:
            self.mode = new_mode
            self.value = opcode_xref[self.name][new_mode]
            return True
        return False

    @property
    def width(self):
        return 1 + addressmode_arg_width[self.mode]



@attrs(auto_attribs=True)
class Storage(object):
    pos: Pos
    width: int
    items: List[int]


@attrs(auto_attribs=True)
class Segment(object):
    pos: Pos
    name: str
    start: [int, None]

