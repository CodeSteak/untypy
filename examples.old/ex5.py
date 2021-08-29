from typing import Protocol, Literal, Callable

import untypy


class Proto(Protocol):
    def meth(self) -> Callable[[int], None]:
        raise NotImplementedError

class Concrete:
    def meth(self) -> Callable[[Literal[0,1]], None]:
        return lambda x: None

def foo(p : Proto) -> None:
    f = p.meth()
    f(2)

untypy.enable()
foo(Concrete())