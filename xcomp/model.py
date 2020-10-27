from abc import *
from attr import attrib, attrs, Factory
from typing import *
from enum import Enum, auto

# TODO: flesh this out with search paths
class FileLoader(object):
    def __call__(self, path):
        with open(path) as f:
            return f.read()


@attrs(auto_attribs=True)
class Position(object):
    line: int
    column: int
    source: str

    @classmethod
    def create(cls, other):
        return cls(other.line, other.column, other.source)


@attrs(auto_attribs=True)
class Label(object):
    pos: Position
    addr: int = 0
    resolved: bool = False


class ExprContext(ABC):
    @abstractmethod
    def resolve_name(self, label_name):
        pass


@attrs(auto_attribs=True)
class ExprBinaryOp(object):
    pos: Position
    oper: Callable
    left: Any = None
    right: Any = None

    def eval(self, ctx):
        return oper(left.eval(ctx), right.eval(ctx))


@attrs(auto_attribs=True)
class ExprUnaryOp(object):
    pos: Position
    oper: Callable
    arg: Any = None

    def eval(self, ctx):
        return oper(arg.eval(ctx))


@attrs(auto_attribs=True)
class ExprValue(object):
    pos: Position
    value: int

    def eval(self, ctx):
        return value


@attrs(auto_attribs=True)
class ExprName(object):
    pos: Position
    value: str

    def eval(self, ctx):
        return ctx.resolve_name(self.value)


@attrs(auto_attribs=True)
class Directive(object):
    pass


@attrs(auto_attribs=True)
class Macro(object):
    name: str = None
    params: List[str] = Factory(list)
    body: List[Any] = Factory(list)

    def is_singlet(self):
        return len(self.params) == 0

    def get_param_id(self, name):
        if isinstance(name, int):
            name = self.params[name]
        return f'@{id(self)}_{name}'


class AddressMode(Enum):
    accumulator = auto()  # implied?
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
    pseduo_number = auto()
    unknown = auto()

@attrs(auto_attribs=True)
class OpCode(object):
    name: str
    mode: AddressMode
    value: int

@attrs(auto_attribs=True)
class Op(object):
    pos: Position
    op: OpCode
    mode: AddressMode = AddressMode.unknown
    arg: Any = None

@attrs(auto_attribs=True)
class Segment(object):
    name: str
    org: int
    code: List[Any] = Factory(list)
