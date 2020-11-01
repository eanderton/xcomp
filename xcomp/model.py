from abc import *
from attr import attrib, attrs, Factory
from typing import *
from enum import Enum, auto
from parsimonious.nodes import Node

# TODO: flesh this out with search paths
class FileLoader(object):
    def __call__(self, path):
        with open(path) as f:
            return f.read()


class Model(object):
    def prettily(self, error=None):
        ret = f'Model <{self.__class__.name}>'

@attrs(auto_attribs=True)
class String(Model):
    node: Node
    value: str


@attrs(auto_attribs=True)
class Include(Model):
    node: Node
    filename: String


@attrs(auto_attribs=True)
class Label(Model):
    node: Node
    addr: int = 0
    resolved: bool = False


class Expr(ABC):
    @abstractmethod
    def eval(self, ctx):
        pass


class ExprContext(ABC):
    @abstractmethod
    def resolve_name(self, label_name):
        pass


@attrs(auto_attribs=True)
class ExprBinaryOp(Expr):
    node: Node
    oper: Callable
    left: Any = None
    right: Any = None

    def eval(self, ctx):
        return oper(left.eval(ctx), right.eval(ctx))


@attrs(auto_attribs=True)
class ExprUnaryOp(Expr):
    node: Node
    oper: Callable
    arg: Any = None

    def eval(self, ctx):
        return oper(arg.eval(ctx))


@attrs(auto_attribs=True)
class ExprValue(Expr):
    node: Node
    value: int

    def eval(self, ctx):
        return self.value

@attrs(auto_attribs=True)
class ExprName(Expr):
    node: Node
    value: str

    def eval(self, ctx):
        return ctx.resolve_name(self.value)


@attrs(auto_attribs=True)
class Macro(Model):
    node: Node
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
class OpCode(Model):
    name: str
    mode: AddressMode
    value: int

@attrs(auto_attribs=True)
class Op(Model):
    node: Node
    op: OpCode
    mode: AddressMode = AddressMode.unknown
    arg: Any = None


@attrs(auto_attribs=True)
class Storage(Model):
    node: Node
    width: int
    items: List[int]


@attrs(auto_attribs=True)
class Segment(Model):
    node: Node
    name: str
    start: [int, None]
    code: List[Any] = Factory(list)

@attrs(auto_attribs=True)
class Program(Model):
    segments: Dict[str, Segment] = Factory(dict)
    macros: Dict[str, Macro] = Factory(dict)
    defs: Dict[str, Macro] = Factory(dict)
