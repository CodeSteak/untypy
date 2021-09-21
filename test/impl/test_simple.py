import unittest
from typing import Union

import untypy
from test.util import DummyExecutionContext, DummyDefaultCreationContext
from untypy.error import UntypyTypeError, UntypyAttributeError
from untypy.impl.simple import SimpleFactory
from untypy.impl.union import UnionFactory


@untypy.patch
class A:
    pass


@untypy.patch
class ChildOfA(A):
    pass


@untypy.patch
class B:
    pass

@untypy.patch
class SomeParent:
    @untypy.patch
    def meth(self) -> str:
        return "Hello"


@untypy.patch
class ChildOfSomeParent(SomeParent):
    @untypy.patch
    def meth(self) -> int:  # Signature does not match.
        return 42


class TestSimple(unittest.TestCase):

    def test_wrap(self):
        checker = SimpleFactory().create_from(A, DummyDefaultCreationContext())

        a = A()
        child_a = ChildOfA()

        res = checker.check_and_wrap(a, DummyExecutionContext())
        self.assertIs(a, res)
        res = checker.check_and_wrap(child_a, DummyExecutionContext())
        self.assertIsNot(child_a, res)  # Wrapped with AWrapper

    def test_attributes(self):
        a = ChildOfA()
        a.foo = 42

        # Note: Attributes are not checked, but they need to be accessible

        @untypy.patch
        def m(x: A) -> None:
            self.assertEqual(x.foo, 42)
            x.foo = 43

        m(a)
        self.assertEqual(a.foo, 43)

    def test_wrap_negative(self):
        checker = SimpleFactory().create_from(A, DummyDefaultCreationContext())

        with self.assertRaises(UntypyTypeError) as cm:
            res = checker.check_and_wrap(B(), DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "A")
        self.assertEqual(i, "^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_wrap_inheritance(self):
        checker = SimpleFactory().create_from(SomeParent, DummyDefaultCreationContext())

        res = checker.check_and_wrap(ChildOfSomeParent(), DummyExecutionContext())
        with self.assertRaises(UntypyTypeError):
            res.meth()

    def test_unions_simple_types_negative(self):
        class U1:
            def meth(self) -> None:
                pass

        class U2:
            def meth(self) -> None:
                pass

        with self.assertRaises(UntypyAttributeError):
            # Should fail because both have the same methods
            # Wrapping cannot distinguish
            UnionFactory().create_from(Union[U1, U2], DummyDefaultCreationContext())

    def test_unions_simple_types_negative(self):
        class U3:
            def meth(self) -> None:
                pass

        class U4:
            def meth(self) -> None:
                pass

            def somethingelse(self) -> None:
                pass

        # this should also be fine. A and B don't have any signatures,
        # so protocol like wrapping does not apply
        UnionFactory().create_from(Union[A, B], DummyDefaultCreationContext())

        # this must be fine: Names of Signatures differ.
        UnionFactory().create_from(Union[U3, U4], DummyDefaultCreationContext())

    def test_no_inheritance_checking_of_builtins(self):
        class SubInt(int):
            pass

        @untypy.patch
        def take_number(number: int) -> None:
            # SubInt should not be wrapped.
            self.assertEqual(type(number), SubInt)

        take_number(SubInt("42"))

    def test_int_as_float(self):
        @untypy.patch
        def f(x: float) -> float:
            return x + 1
        self.assertEqual(f(1), 2)
