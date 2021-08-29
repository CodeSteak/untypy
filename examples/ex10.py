import untypy

untypy.enable()

from typing import Callable


def showoperator(name: str, fn: Callable[[int, int], int]) -> None:
    print(f"5 {name} 4 = {fn(5, 4)}")


def mul(x: int, y: float) -> int:
    return x * y


showoperator("+", lambda x, y: x + y)
showoperator("*", mul)
