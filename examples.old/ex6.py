from typing import Protocol, Literal, Callable

import untypy


class Proto(Protocol):
    def meth(self) -> Callable[[int], int]:
        raise NotImplementedError

class Concrete:
    def meth(self) -> Callable[[Literal[0,1]], Literal[0,1]]:
        return lambda x: 47

def foo(p : Proto) -> None:
    f = p.meth()
    f(0)

untypy.enable()
foo(Concrete())