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


def main():
    print("\n\n---- test(12, 34)")
    print("=> " + test(12, 34))

    print("\n\n---- test(1, 2)")
    print("=> " + test(1, 2))

    print("\n\n---- test(\"12\", \"34\")")
    print("=> " + test("12", "34"))

    print("\n\n---- test(12, 0)")
    print("=> " + test(12, 0))

    print("\n\n---- test_wrong_ret(12, 0)")
    print("=> " + str(test_wrong_ret(12, 0)))

    print("\n\n---- test_lst([1,2,2,3], [])")
    print("=> " + test_lst([1, 2, 2, 3], []))

    print("\n\n---- test_lst([1, 2, 2, 3], [[1, '42']]))")
    print("=> " + test_lst([1, 2, 2, 3], [[1, '42']]))

    ###

    print("\n\n----  foo(42, lambda x: x + 1)  [callers's fault]")
    print("=> " + str(foo(42, lambda x: x + 1)))

    print("\n\n----  foo(42, lambda x: x + 1)  [bar's fault]")
    print("=> " + str(bar(42, lambda x: str(x + 1))))

    print("\n\n----  bar(42, baz))  [type def error in lambba]")
    print("=> " + str(bar(42, baz)))

    ##


if __name__ == "__main__":
    untypy.enable()
main()
