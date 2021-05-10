from typing import Protocol, Literal

import untypy


class Proto(Protocol):
    def meth(self, x: int) -> int:
        pass


class Concrete:
    def meth(self, x: Literal[1]) -> int:
        return 42

def foo(ob: Proto) -> None:
    print(ob.meth("str"))
    pass

untypy.enable()

foo(Concrete())