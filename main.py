import inspect
from collections.abc import Callable

import untypy

NonZero = lambda x: x != 0


def test(x: int, y: NonZero) -> str:
    return str(x + y)


def test_wrong_ret(x: int, y: NonZero) -> str:
    return 42


def test_lst(x: list[int], y: list[list[int]]) -> str:
    return "ok"


def foo(i: int, fun: Callable[[int], str]) -> list[str]:
    return [fun(i), "42"]


def bar(i: int, fun: Callable[[int], str]) -> list[str]:
    return [fun(i), 42]


def baz(x: str) -> str:
    return x


run = [
    lambda: test(12, 34),
    lambda: test(1, 2),
    lambda: test("12", "34"),
    lambda: test(12, 0),
    lambda: test_wrong_ret(12, 0),
    lambda: test_lst([1, 2, 2, 3], []),
    lambda: test_lst([1, 2, 2, 3], [[1, '42']]),
    lambda: foo(42, lambda x: x + 1),  # callers's fault
    lambda: bar(42, lambda x: str(x + 1)),  # bar's fault
    lambda: bar(42, baz),
]


def main():
    for expr in run:
        try:
            print(f"RUNNING: {inspect.getsource(expr).replace('lambda:', '', 1).strip()}")
            ret = expr()
            print(f"= {ret} [OKAY]")
        except TypeError as e:
            print(e)
            pass
        print("")
        print("----")


if __name__ == "__main__":
    untypy.enable()
    main()
