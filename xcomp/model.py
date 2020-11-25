from abc import *
from attr import attrib, attrs, Factory
from typing import *
from xcomp.reduce_parser import Pos
from xcomp.cpu6502 import OpCode, opcode_templates

def lobyte(value):
    return value & 0xFF


def hibyte(value):
    return (value >> 8) & 0xFF


def is8bit(value):
    return lobyte(value) == value


class EvalException(Exception):
    def __init__(self, pos, msg):
        self.pos = pos
        super().__init__(msg)

class AbstractContextManager(ABC):
    @abstractmethod
    def get_text(self, ctx_name):
        return None

    @abstractmethod
    def exists(self, ctx_name):
        return False


@attrs(auto_attribs=True, slots=True)
class FileContextManager(AbstractContextManager):
    files: Dict = Factory(dict)

    def get_text(self, filename):
        # TODO: normalize path
        # TODO: check for file existence

        if filename not in self.files:
            with open(filename) as f:
                self.files[filename] = f.read()
        return self.files[filename]

    def exists(self, filename):
        return filename in self.files


class String(object):
    def __init__(self, pos, *chars):
        self.pos = pos
        self.value = ''.join(chars)


@attrs(auto_attribs=True)
class Include(object):
    pos: Pos
    filename: String


@attrs(auto_attribs=True)
class Label(object):
    pos: Pos
    name: str
    addr: int = 0

    def eval(self, ctx):
        return self.addr

    def __str__(self):
        return f'{self.name}:'


class ExprContext(ABC):
    @abstractmethod
    def resolve(self, name):
        pass


class Expr(ABC):
    @abstractmethod
    def eval(self, ctx):
        pass


@attrs(auto_attribs=True)
class ExprUnaryOp(Expr):
    pos: Pos
    arg: Expr

    @abstractmethod
    def oper(self, a):
        pass

    def eval(self, ctx):
        return self.oper(self.arg.eval(ctx))


class Expr8(ExprUnaryOp):
    def oper(self, a):
        return a

    def __str__(self):
        return f'{self.arg}'


class Expr16(ExprUnaryOp):
    def oper(self, a):
        return a

    def __str__(self):
        return f'{self.arg}'


class ExprNegate(ExprUnaryOp):
    def oper(self, a):
        return -a

    def __str__(self):
        return f'-{self.arg}'


class ExprLobyte(ExprUnaryOp):
    def oper(self, a):
        return lobyte(a)

    def __str__(self):
        return f'<{self.arg}'


class ExprHibyte(ExprUnaryOp):
    def oper(self, a):
        return hibyte(a)

    def __str__(self):
        return f'<{self.arg}'


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

    def __str__(self):
        return f'({self.left} + {self.right})'


class ExprSub(ExprBinaryOp):
    def oper(self, a, b):
        return a - b

    def __str__(self):
        return f'({self.left} - {self.right})'


class ExprMul(ExprBinaryOp):
    def oper(self, a, b):
        return a * b

    def __str__(self):
        return f'({self.left} * {self.right})'


class ExprDiv(ExprBinaryOp):
    def oper(self, a, b):
        return a / b

    def __str__(self):
        return f'({self.left} / {self.right})'


class ExprPow(ExprBinaryOp):
    def oper(self, a, b):
        return a ^ b

    def __str__(self):
        return f'({self.left} ^ {self.right})'


@attrs(auto_attribs=True)
class ExprValue(Expr):
    pos: Pos
    value: int
    base: int = 10

    def eval(self, ctx):
        return self.value

    def __str__(self):
        if self.base == 2:
            return f'%{self.value:b}'
        if self.base == 16:
            return f'${self.value:x}'
        return str(self.value)


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

    def __str__(self):
        return self.value


@attrs(auto_attribs=True)
class Params(object):
    pos: Pos
    names: List[str] = Factory(list)

    def __str__(self):
        return ', '.join(self.names)


@attrs(auto_attribs=True)
class Define(Expr):
    pos: Pos
    name: str
    expr: Expr

    def eval(self, ctx):
        return self.expr.eval(ctx)

    def __str__(self):
        return f'.define {self.name} {self.expr}'


class Scope(object):
    def __str__(self):
        return '.scope'


class EndScope(object):
    def __str__(self):
        return '.endscope'


@attrs(auto_attribs=True)
class Fragment(object):
    pos: Pos
    body: List[Any] = Factory(list)


@attrs(auto_attribs=True)
class Macro(object):
    pos: Pos
    name: str
    params: Params
    body: List[Any] = Factory(list)

    def substitute(self, args):
        ''' Return copy of body with params defined. '''
        for ii in range(len(args.values)):
            name = self.params[ii]
            yield Define(Pos(0, 0), name, args.values[ii])
        for x in self.body:
            yield x


@attrs(auto_attribs=True)
class Args(object):
    pos: Pos
    values: List[Expr] = Factory(list)


@attrs(auto_attribs=True)
class MacroCall(object):
    pos: Pos
    name: str
    args: Args


@attrs(auto_attribs=True)
class Op(object):
    pos: Pos
    op: OpCode
    arg: Expr = None

    def __str__(self):
        if not self.arg:
            return f'    {self.op.name}'
        args = opcode_templates[self.op.mode].format(**{
            'arg16': str(self.arg),
            'arg8': str(self.arg),
        })
        return f'    {self.op.name} {args}'


@attrs(auto_attribs=True)
class Storage(object):
    pos: Pos
    width: int
    items: List[int]

    def __str__(self):
        items = map(str, self.items)
        if self.width == 1:
            return '.byte ' + (', '.join(items))
        return '.word ' + (', '.join(items))


@attrs(auto_attribs=True)
class Segment(object):
    pos: Pos
    name: str
    start: [int, None]

    def __str__(self):
        if self.start is not None:
            return f'.{self.name} {self.start}'
        return f'.{self.name}'
