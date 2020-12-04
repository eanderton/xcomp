import os
from abc import *
from attr import attrib
from attr import attrs
from attr import Factory
from typing import *
from xcomp.reduce_parser import Pos
from xcomp.reduce_parser import NullPos
from xcomp.cpu6502 import OpCode

# TODO: move str rendering to decompiler
# TOOD: move expr visit to compiler

def lobyte(value):
    return value & 0xFF


def hibyte(value):
    return (value >> 8) & 0xFF


def is8bit(value):
    return lobyte(value) == value


def stringbytes(value, encoding):
    return list([x for x in bytes(value, encoding)])


class EvalException(Exception):
    def __init__(self, pos, msg):
        self.pos = pos
        super().__init__(msg)

class AbstractContextManager(ABC):
    @abstractmethod
    def get_text(self, ctx_name):
        return None


class FileContextException(Exception):
    pass


@attrs(auto_attribs=True, slots=True)
class FileContextManager(AbstractContextManager):
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

    def eval(self, ctx):
        return self.value


@attrs(auto_attribs=True)
class Include(object):
    pos: Pos
    filename: String


class ExprContext(ABC):
    @abstractmethod
    def resolve(self, name):
        pass


class Expr(ABC):
    @abstractmethod
    def eval(self, ctx):
        pass


@attrs(auto_attribs=True)
class Label(Expr):
    pos: Pos
    name: str
    addr: int = 0

    def eval(self, ctx):
        return self.addr


@attrs(auto_attribs=True)
class ExprUnaryOp(Expr):
    pos: Pos
    arg: Expr
    opname = '?'

    @abstractmethod
    def oper(self, a):
        pass

    def eval(self, ctx):
        return self.oper(self.arg.eval(ctx))

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

    def eval(self, ctx):
        return self.oper(self.left.eval(ctx), self.right.eval(ctx))


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


@attrs(auto_attribs=True)
class ExprValue(Expr):
    pos: Pos
    value: int
    base: int = 10
    width: int = 8

    def eval(self, ctx):
        return self.value


@attrs(auto_attribs=True)
class ExprName(Expr):
    pos: Pos
    value: str

    def eval(self, ctx):
        value = ctx.resolve(self.value)
        if value is None:
            raise EvalException(self.pos, f'Identifier {self.value} is undefined.')
        if isinstance(value, Expr):
            return value.eval(ctx)
        return value


@attrs(auto_attribs=True)
class Define(Expr):
    pos: Pos
    name: str
    expr: Expr

    def eval(self, ctx):
        return self.expr.eval(ctx)


class Scope(object):
    pos: Pos = NullPos


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

    def substitute(self, args):
        ''' Return copy of body with params defined. '''
        for ii in range(len(args)):
            name = self.params[ii]
            yield Define(Pos(0, 0), name, args[ii])
        for x in self.body:
            yield x


@attrs(auto_attribs=True)
class MacroCall(object):
    pos: Pos
    name: str
    args: tuple


@attrs(auto_attribs=True)
class Op(object):
    pos: Pos
    op: OpCode
    arg: Expr = None


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

