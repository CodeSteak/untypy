from typing import Tuple


def kwargs(a: int, b: str, c: bool) -> Tuple[bool, int, str]:
    return c, a, b


def default_args(a: int, b: str = "hello") -> str:
    return b
