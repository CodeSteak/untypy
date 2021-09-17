import unittest
from typing import Generic, TypeVar, NoReturn, Tuple

import untypy
from untypy.error import UntypyTypeError

T = TypeVar('T')

@untypy.patch
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

    def test_bound_generic_protocol_style_ok(self):
        instance = Aint()

        @untypy.patch
        def target(a: A[int]) -> None:
            a.insert(42)

        # fine
        target(instance)

    def test_bound_generic_protocol_style_conflict(self):
        @untypy.patch
        def target(a: A[int]) -> None:
            a.insert(42)

        with self.assertRaises(UntypyTypeError) as cm:
            target((A[str])())  # error

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "insert(self: Self, elm: ~T=str) -> None")
        self.assertEqual(i, "                        ^^^^^^")

    def test_bound_generic_protocol_style_wrong_class(self):
        @untypy.patch
        class B(A):
            pass

        @untypy.patch
        class C(Generic[T]):
            @untypy.patch
            def passthrough(self, t: T) -> Tuple[int, T]:
                return (42, t)

            @untypy.patch
            def insert(self, elm: T) -> NoReturn:
                pass

            @untypy.patch
            def some_string(self) -> T:
                return "this should be T"

        @untypy.patch
        def target(a: A[int]) -> None:
            a.insert(42)

        target((B[int])())  # ok

        with self.assertRaises(UntypyTypeError) as cm:
            target((C[int])())  # error

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()
        self.assertEqual(t, "target(a: A[~T=int]) -> None")
        self.assertEqual(i, "          ^^^^^^^^^")

    def test_bound_generic_return_error(self):
        instance = Aint()
        with self.assertRaises(UntypyTypeError) as cm:
            instance.some_string()

        self.assertTrue("def some_string(self) -> T:" in cm.exception.last_responsable().source_line)
