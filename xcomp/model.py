# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

from abc import abstractmethod
from attr import attrs
from attr import attrib
from attr import Factory
from typing import *
from .cpu6502 import *
from .utils import is8bit
from .utils import lobyte
from .utils import hibyte
from .utils import stringbytes
from .reduce_parser import Pos
from .reduce_parser import NullPos


@attrs(auto_attribs=True)
class Comment(object):
    pos: Pos
    full_line: bool
    text: str


@attrs(auto_attribs=True)
class ModelBase(object):
    pos: Pos
    comment: Comment = attrib(init=False, default=None)


@attrs(auto_attribs=True)
class Expr(ModelBase):
    pass


@attrs(auto_attribs=True)
class Pragma(ModelBase):
    name: str
    expr: Expr


@attrs(auto_attribs=True)
class Encoding(ModelBase):
    name: str


@attrs(auto_attribs=True)
class String(ModelBase):
    value: str


@attrs(auto_attribs=True)
class Include(ModelBase):
    filename: String


@attrs(auto_attribs=True)
class BinaryInclude(ModelBase):
    filename: str


@attrs(auto_attribs=True)
class Label(ModelBase):
    name: str


@attrs(auto_attribs=True)
class ExprUnaryOp(Expr):
    arg: Expr
    opname = '?'

    @abstractmethod
    def oper(self, a):
        pass

class ExprInvert(ExprUnaryOp):
    opname = '~'
    def oper(self, a):
        clamp = 0xFF if is8bit(a) else 0xFFFF
        return ~a & clamp

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
    value: int
    base: int = 10
    width: int = 8


@attrs(auto_attribs=True)
class ExprName(Expr):
    value: str


@attrs(auto_attribs=True)
class Define(ModelBase):
    name: str
    expr: Expr


@attrs(auto_attribs=True)
class Scope(ModelBase):
    pos: Pos = NullPos


@attrs(auto_attribs=True)
class EndScope(ModelBase):
    pos: Pos = NullPos


@attrs(auto_attribs=True)
class Fragment(ModelBase):
    body: List[Any] = Factory(list)


@attrs(auto_attribs=True)
class Macro(ModelBase):
    name: str
    params: tuple
    body: Fragment


@attrs(auto_attribs=True)
class MacroCall(ModelBase):
    name: str
    args: tuple


@attrs(auto_attribs=True)
class Op(ModelBase):
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
class Storage(ModelBase):
    width: int
    items: List[int]


@attrs(auto_attribs=True)
class Segment(ModelBase):
    name: str
    start: [int, None]


@attrs(auto_attribs=True)
class Dim(ModelBase):
    length: Expr
    init: List[Expr] = Factory(list)


@attrs(auto_attribs=True)
class Var(ModelBase):
    name: str
    size: Expr
    init: List[Expr] = Factory(list)

@attrs(auto_attribs=True)
class Struct(ModelBase):
    name: str
    offset: Expr
    fields: List[Var] = Factory(list)
