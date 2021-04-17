from typing import Optional, Union, Literal, Tuple, Callable
import untypy

def foo(x : Union[Callable[[], int], int]) -> Callable[[], int]:
    if callable(x):
        return x
    else:
        return lambda z=x: x

# # raises AttributeError
# def undecidable_by_wrapping(f: Union[Callable[[], int], Callable[[str], int]]) -> None:
#     pass


untypy.enable()

fn = foo(1)
print(fn())

fn = foo(lambda: 2)
print(fn())

fn = foo(lambda: "3")
# print(fn())  # TypeError

