from attr import attrib, attrs, Factory
from typing import *
from enum import Enum, auto

# TODO: flesh this out with search paths
class FileLoader(object):
    def __call__(self, path):
        with open(path) as f:
            return f.read()


@attrs(auto_attribs=True)
class Label(object):
    addr: int = 0
    resolved: bool = False


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

@attrs(auto_attribs=True)
class OpCode(object):
    name: str
    mode: AddressMode
    value: int

@attrs(auto_attribs=True)
class Op(object):
    op: OpCode
    arg1: Any = None
    arg2: Any = None


@attrs(auto_attribs=True)
class Segment(object):
    name: str
    org: int
    code: List[Any] = Factory(list)
