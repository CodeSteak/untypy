from typing import Protocol, Literal, Callable
import untypy

class A:
    pass

class B(A):
    pass

# class Inter(Protocol):
#     def meth(self) -> Callable[[], B]:
#         raise NotImplementedError
#
# class Concrete:
#     def meth(self) -> Callable[[], B]:
#         return lambda : A()
#
# def foo(ob: Inter) -> None:
#     fn = ob.meth()
#     fn = fn()
#     fn()
#     pass
#
# untypy.enable()
# foo(Concrete())


# class Proto(Protocol):
#     def meth(self, c: Callable[[A], None]) -> None:
#         raise NotImplementedError
#
# class Concrete:
#     def meth(self, c: Callable[[B], None]) -> None:
#         return c(A())
#
# def foo(p : Proto) -> None:
#     return p.meth(lambda x: None)
#
# untypy.enable()
# foo(Concrete())

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