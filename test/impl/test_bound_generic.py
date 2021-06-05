from typing import Generic, TypeVar, NoReturn, Tuple

from twisted.trial import unittest

import untypy
from untypy.error import UntypyTypeError

T = TypeVar('T')


@untypy.patch_class
class A(Generic[T]):
    @untypy.patch
    def passthrough(self, t: T) -> Tuple[int, T]:
        return (42, t)

    @untypy.patch
    def insert(self, elm: T) -> NoReturn:
        pass

    @untypy.patch
    def some_string(self) -> T:
        return "this should be T"


Aint = A[int]


class TestBoundGeneric(unittest.TestCase):

    def test_bound_generic_ok(self):
        instance = Aint()
        self.assertEqual(instance.passthrough(30), (42, 30))

    def test_bound_generic_caller_error(self):
        instance = Aint()
        with self.assertRaises(UntypyTypeError) as cm:
            instance.insert("this should be an int")

        self.assertTrue("instance.insert" in cm.exception.last_responsable().source_line)

    def test_bound_generic_return_error(self):
        instance = Aint()
        with self.assertRaises(UntypyTypeError) as cm:
            instance.some_string()

        self.assertTrue("def some_string(self) -> T:" in cm.exception.last_responsable().source_line)
