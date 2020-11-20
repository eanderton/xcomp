from abc import *
from attr import attrib, attrs, Factory
from typing import *
from xcomp.reduce_parser import Pos
from xcomp.cpu6502 import OpCode, opcode_templates

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
    name: str
    addr: int = 0
    resolved: bool = False

    def __str__(self):
        return f'{self.name}:'


@attrs(auto_attribs=True)
class ExprContext(object):
    lookup: Factory(dict)

    @abstractmethod
    def resolve_name(self, label_name):
        return self.lookup.get(label_name, None)


class Expr(ABC):
    @abstractmethod
    def eval(self, ctx):
        pass

    @abstractmethod
    def validate(self, ctx):
        return False

    def substitute(self, name, value):
        pass


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
        return a & 0xFF

    def __str__(self):
        return f'<{self.arg}'


class ExprHibyte(ExprUnaryOp):
    def oper(self, a):
        return (a >> 8) & 0xFF

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

    def eval(self, ctx):
        return self.value

    def validate(self, ctx):
        return True

    def __str__(self):
        return str(self.value)


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

    def __str__(self):
        return self.value


@attrs(auto_attribs=True)
class Params(object):
    pos: Pos
    names: List[str] = Factory(list)

    def __str__(self):
        return ', '.join(self.names)


@attrs(auto_attribs=True)
class Define(object):
    pos: Pos
    name: str
    expr: Expr

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

    def is_singlet(self):
        return len(self.params) == 0

    def get_param_id(self, name):
        if isinstance(name, int):
            name = self.params[name]
        return f'@{id(self)}_{name}'

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
        if self.width == 8:
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
