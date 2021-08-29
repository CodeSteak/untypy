import untypy

untypy.enable()

from typing import TypeVar, Protocol

X = TypeVar('X')


class ProtoX(Protocol):

    @untypy.postcondition(lambda ret: ret.startswith("a"))
    def foo(self) -> str:
        pass


class Concrete:
    def __init__(self):
        self.x = "This is an attribute of Concrete"

    def foo(self) -> str:
        return "bbb"


def meep(a: ProtoX) -> None:
    print(a.x)
    a.foo()


meep(Concrete())
