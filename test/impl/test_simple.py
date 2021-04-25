import unittest

from untypy.error import UntypyTypeError
from untypy.impl import DefaultCreationContext
from untypy.impl.simple import SimpleFactory
from untypy.util import DummyExecutionContext


class A:
    pass

class ChildOfA(A):
    pass

class B:
    pass

class TestSimple(unittest.TestCase):

    def test_wrap(self):
        checker = SimpleFactory().create_from(A, DefaultCreationContext())

        a = A()
        child_a = ChildOfA()

        res = checker.check_and_wrap(a, DummyExecutionContext())
        self.assertIs(a, res)
        res = checker.check_and_wrap(child_a, DummyExecutionContext())
        self.assertIs(child_a, res)

    def test_wrap_negative(self):
        checker = SimpleFactory().create_from(A, DefaultCreationContext())

        with self.assertRaises(UntypyTypeError) as cm:
            res = checker.check_and_wrap(B(), DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "A")
        self.assertEqual(i, "^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.frames[-1].file, "dummy")