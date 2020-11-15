from abc import *
from attr import attrib, attrs, Factory
from typing import *
from enum import Enum, auto
from xcomp.reduce_parser import Pos

# TODO: flesh this out with search paths
class FileLoader(object):
    def __call__(self, path):
        with open(path) as f:
            return f.read()


@attrs(auto_attribs=True)
class String(object):
    pos: Pos
    value: str


@attrs(auto_attribs=True)
class Include(object):
    pos: Pos
    filename: String


@attrs(auto_attribs=True)
class Label(object):
    pos: Pos
    addr: int = 0
    resolved: bool = False


class Expr(ABC):
    @abstractmethod
    def eval(self, ctx):
        pass

    @abstractmethod
    def validate(self, ctx):
        return False


@attrs(auto_attribs=True)
class ExprContext(object):
    lookup: Factory(dict)

    @abstractmethod
    def resolve_name(self, label_name):
        return self.lookup.get(label_name, None)


@attrs(auto_attribs=True)
class ExprUnaryOp(Expr):
    pos: Pos
    arg: Expr

    def eval(self, ctx):
        return self.oper(self.arg.eval(ctx))

    def validate(self, ctx):
        return arg.validate(ctx)


class Expr8(ExprUnaryOp):
    def oper(self, a):
        return a


class Expr16(ExprUnaryOp):
    def oper(self, a):
        return a


class ExprNegate(ExprUnaryOp):
    def oper(self, a):
        return -a


class ExprLobyte(ExprUnaryOp):
    def oper(self, a):
        return -a


class ExprHibyte(ExprUnaryOp):
    def oper(self, a):
        return -a


@attrs(auto_attribs=True)
class ExprBinaryOp(Expr):
    pos: Pos
    left: Expr
    right: Expr

    def eval(self, ctx):
        return self.oper(self.left.eval(ctx), self.right.eval(ctx))

    def validate(self, ctx):
        return a.validate(ctx) and b.validate(ctx)


class ExprAdd(ExprBinaryOp):
    def oper(self, a, b):
        return a + b


class ExprSub(ExprBinaryOp):
    def oper(self, a, b):
        return a - b


class ExprSub(ExprBinaryOp):
    def oper(self, a, b):
        return a - b


class ExprMul(ExprBinaryOp):
    def oper(self, a, b):
        return a * b


class ExprDiv(ExprBinaryOp):
    def oper(self, a, b):
        return a / b


class ExprPow(ExprBinaryOp):
    def oper(self, a, b):
        return a ^ b


@attrs(auto_attribs=True)
class ExprValue(Expr):
    pos: Pos
    value: int

    def eval(self, ctx):
        return self.value

    def validate(self, ctx):
        return True


@attrs(auto_attribs=True)
class ExprName(Expr):
    pos: Pos
    value: str

    def eval(self, ctx):
        return ctx.resolve_name(self.value)
        value = ctx.resolve_name(self.value)
        if value is None:
            raise Exception(f'Identifier {self.value} is undefined.')
        return value

    def validate(self, ctx):
        value =  ctx.resolve_name(self.value)
        return value is not None


@attrs(auto_attribs=True)
class Params(object):
    pos: Pos
    names: List[str] = Factory(list)


@attrs(auto_attribs=True)
class Fragment(object):
    pos: Pos
    body: List[Any] = Factory(list)


@attrs(auto_attribs=True)
class Macro(object):
    pos: Pos
    name: str
    params: List[str] = Factory(list)
    body: List[Any] = Factory(list)

    def is_singlet(self):
        return len(self.params) == 0

    def get_param_id(self, name):
        if isinstance(name, int):
            name = self.params[name]
        return f'@{id(self)}_{name}'


@attrs(auto_attribs=True)
class MacroCall(object):
    pos: Pos
    name: str
    args: List[Expr] = Factory(list)


@attrs(auto_attribs=True)
class Args(object):
    pos: Pos
    values: List[Expr] = Factory(list)

class AddressMode(Enum):
    accumulator = auto()
    absolute = auto()
    absolute_x = auto()
    absolute_y = auto()
    immediate = auto()
    implied = auto()
    indirect = auto()
    indirect_x = auto()
    indirect_y = auto()
    relative = auto()
    zeropage = auto()
    zeropage_x = auto()
    zeropage_y = auto()
    unknown = auto()


@attrs(auto_attribs=True)
class OpCode(object):
    name: str
    mode: AddressMode
    value: int


@attrs(auto_attribs=True)
class Op(object):
    pos: Pos
    op: OpCode
    arg: Any = Factory(list)


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
    code: List[Any] = Factory(list)


@attrs(auto_attribs=True)
class Program(object):
    segments: Dict[str, Segment] = Factory(dict)
    macros: Dict[str, Macro] = Factory(dict)
    defs: Dict[str, Macro] = Factory(dict)
