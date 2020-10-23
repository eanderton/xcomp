from attr import attrib, attrs, Factory
from typing import *


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

    def is_const(self):
        return len(self.params) == 0

    def get_param_id(self, name):
        return f'@{id(self)}_{name}'


@attrs(auto_attribs=True)
class Op(object):
    operator: str
    arg1: Any = None
    arg2: Any = None


@attrs(auto_attribs=True)
class Segment(object):
    name: str
    org: int
    code: List[Any] = Factory(list)

#@attrs(auto_attribs=True)
#class Program(object):
#    segments: dict[string, Segment]
#    name_table: dict[string, Union[Label, Macro]]

