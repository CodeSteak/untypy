import untypy

untypy.enable()
from typing import *

EvenNumber = Annotated[int, lambda x: x % 2 == 0, "Number must be even."]


def foo(funtions: List[Callable[[], EvenNumber]]) -> NoReturn:
    for fn in funtions:
        print(fn())


func = lambda: 41
foo([func])  # This is a type error
