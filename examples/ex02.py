import untypy

untypy.enable()

from typing import *


class PointDisplay:
    def show(self, x: int, y: str) -> str:
        return f"({x}, {y})"


T = TypeVar('T')
K = TypeVar('K')


class MyProtocol(Protocol[T, K]):
    def show(self, x: T, y: T) -> K:
        pass


def use_my_protocol(fn: MyProtocol[int, str]) -> None:
    print(fn.show(10, 10))


use_my_protocol(PointDisplay())
