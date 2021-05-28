import unittest

import untypy
from untypy.error import UntypyTypeError
from untypy.impl import DefaultCreationContext
from untypy.impl.simple import SimpleFactory
from test.util import DummyExecutionContext, DummyDefaultCreationContext


class A:
    pass

class ChildOfA(A):
    pass

class B:
    pass

class SomeParent:
    def meth(self) -> str:
        return "Hello"

class ChildOfSomeParent(SomeParent):
    def meth(self) -> int: # Signature does not match.
        return 42

class TestSimple(unittest.TestCase):

    def test_wrap(self):
        checker = SimpleFactory().create_from(A, DummyDefaultCreationContext())

        a = A()
        child_a = ChildOfA()

        res = checker.check_and_wrap(a, DummyExecutionContext())
        self.assertIs(a, res)
        res = checker.check_and_wrap(child_a, DummyExecutionContext())
        self.assertIs(child_a, res)

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
        untypy.patch(SomeParent)
        untypy.patch(ChildOfSomeParent)

        checker = SimpleFactory().create_from(SomeParent, DummyDefaultCreationContext())

        res = checker.check_and_wrap(ChildOfSomeParent(), DummyExecutionContext())
        with self.assertRaises(UntypyTypeError) as cm:
            res.meth()