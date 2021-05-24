from typing import Protocol, Literal, Callable
import untypy


class Proto(Protocol):
    def meth(self,  c: Callable[[int], None]) -> None:
        raise NotImplementedError

class Concrete:
    def meth(self, c: Callable[[Literal[0,1]], None]) -> None:
        c(42) # Violates its own signature of c

def foo(p : Proto) -> None:
    p.meth(lambda x: None)

untypy.enable()
foo(Concrete())
