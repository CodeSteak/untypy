from typing import Protocol, Literal, Callable
import untypy


X = Callable[[int], None]
Y = Callable[[str], None]


class Proto(Protocol):
    def meth(self, x: int) -> None:
        raise NotImplementedError


class Proto2(Protocol):
    def meth(self, x: int) -> None:
        raise NotImplementedError

class Concrete:
    def meth(self, x: str) -> None:
        pass

def foo(p : Proto) -> None:
    bar(p)

def bar(p : Proto2) -> None:
    p.meth(10)

untypy.enable()
foo(Concrete())