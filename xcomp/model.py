from attr import attrib, attrs
from typing import *


class Label(object):
    addr: int = 0
    resolved: bool = False


@attrs(auto_attribs=True)
class Directive(object):
    pass


@attrs(auto_attribs=True)
class Macro(object):
    pass


@attrs(auto_attribs=True)
class MacroCall(object):
    name: str
    arguments: List


@attrs(auto_attribs=True)
class Op(object):
    operator: str
    arg1: Any = None
    arg2: Any = None


@attrs(auto_attribs=True)
class Segment(object):
    name: str
    org: int
    code: List[Union[Label, Op, Directive, MacroCall]] = []


@attrs(auto_attribs=True)
class Macro(object):
    name: str
    arguments: List[Any] = []
    fragment: List[Any] = []


#@attrs(auto_attribs=True)
#class Program(object):
#    segments: dict[string, Segment]
#    name_table: dict[string, Union[Label, Macro]]

