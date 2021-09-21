import unittest
from typing import Union, ForwardRef

import untypy
from untypy.error import UntypyTypeError

Shape = Union['Square', 'Circle']
Shape2 = Union[ForwardRef('Square'), ForwardRef('Circle')]

class Square:
    pass

class Circle:
    pass

@untypy.typechecked
def useShape(s: Shape) -> None:
    pass

@untypy.typechecked
def useShape2(s: Shape2) -> None:
    pass

@untypy.typechecked
def useUnion(s: Union[Square, Circle]) -> None:
    pass

@untypy.typechecked
def useSquare(s: Square) -> None:
    pass

class TestForwardRef(unittest.TestCase):

    def test_failing(self):
        with self.assertRaises(UntypyTypeError):
            useShape(0)
        with self.assertRaises(UntypyTypeError):
            useShape2(0)
        with self.assertRaises(UntypyTypeError):
            useUnion(0)
        with self.assertRaises(UntypyTypeError):
            useSquare(Circle())

    def test_useSquare(self):
        useSquare(Square())

    def test_useShape(self):
        useShape(Square())
        useShape(Circle())

    def test_useShape2(self):
        useShape2(Square())
        useShape2(Circle())

    def test_useUnion(self):
        useUnion(Square())
        useUnion(Circle())
