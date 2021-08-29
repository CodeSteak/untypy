from __future__ import annotations

import untypy

untypy.enable()

from typing import Annotated

IsEven = Annotated[int, lambda x: x % 2 == 0]


def divideBy2(x: IsEven) -> int:
    return x // 2


divideBy2(7)

# IsEven = Annotated[int, lambda x: x % 2 == 0]
