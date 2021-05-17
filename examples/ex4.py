from typing import Protocol, Literal

import untypy


class Inter(Protocol):
    def meth(self, x: int) -> int:
        pass


class Concrete:
    def meth(self, x: Literal[0, 1]) -> int:
        return 42


def foo(ob: Inter) -> None:
    print(ob.meth(2))
    pass

untypy.enable()

foo(Concrete())