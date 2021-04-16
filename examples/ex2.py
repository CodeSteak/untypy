from typing import Optional, Union, Literal, Tuple, Callable
import untypy

def adders(n : list[int]) -> list[Callable[[int], int]]:
    out = []
    for i in n:
        out.append(lambda x, add=i: x + add)

    return out

untypy.enable()

lst = adders([1,2,3,4,5,6])

lst.append(lambda x: 0)

lst.append(lambda x: "hello")

for fn in lst:
    print(fn(100))
