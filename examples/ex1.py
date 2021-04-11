import inspect
from typing import Optional, Union, Literal, Tuple, Callable
import untypy
from untypy.error import UntypyTypeError


def main():
    fn1 = lambda x: x + 1
    fn2 = lambda x: str(x + 1)

    run = [
        lambda: simple_int(42),
        lambda: simple_int("42"),

        lambda: foo(42, fn1),  # callers's fault
        lambda: bar(42, fn2),  # bar's fault
        lambda: bar(42, baz),
    ]

    for expr in run:
        try:
            print(f"RUNNING: {inspect.getsource(expr).replace('lambda:', '', 1).strip()}")
            ret = expr()
            print(f"= {ret} [OKAY]")
        except UntypyTypeError as e:
            print("err")
            print(e)
            pass
        print("")
        print("----")


def foo(i: int, fun: Callable[[int], str]) -> list[str]:
    return [fun(i), "42"]


def bar(i: int, fun: Callable[[int], str]) -> list[str]:
    return [fun(i), 42]


def baz(x: str) -> str:
    return x


def simple_int(x: int) -> str:
    return str(x)

if __name__ == '__main__':
    untypy.enable()
    main()
