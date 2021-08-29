from typing import Protocol, Callable

import untypy

X = Callable[[int], None]
Y = Callable[[str], None]


class Proto(Protocol):
    def meth(self, c: Callable[[X], None]) -> None:
        raise NotImplementedError

class Concrete:
    def meth(self, c: Callable[[Y], None]) -> None:
        g = lambda x: None
        c(g)

def foo(p : Proto) -> None:
    f = lambda x: \
        x("1000")
    p.meth(f)

untypy.enable()
foo(Concrete())