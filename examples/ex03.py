import untypy

untypy.enable()

from typing import *


def foo(functions: list[Callable[[], str]]) -> NoReturn:
    for fn in functions:
        print(fn())


foo([lambda: "Hello"])  # This should cause no type error
foo([lambda: 42])  # This is a type error
