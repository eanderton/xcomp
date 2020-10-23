from attr import attrib, attrs, Factory
from typing import *


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

