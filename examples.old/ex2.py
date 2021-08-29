from typing import Callable

import untypy


def adders(n: list[int]) -> list[Callable[[int], int]]:
    out = []
    for i in n:
        out.append(lambda x, add=i: x + add)

    return out

untypy.enable()

lst = adders([1,2,3,4,5,6])

lst.append(lambda x: 0)

return_some_string_fn = lambda x: "hello"

lst.append(return_some_string_fn)

for fn in lst:
    print(fn(100))

