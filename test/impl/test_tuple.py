import unittest
from typing import Tuple

from untypy.error import UntypyTypeError
from untypy.impl import DefaultCreationContext
from untypy.impl.dummy_delayed import DummyDelayedType
from untypy.impl.tuple import TupleFactory
from test.util import DummyExecutionContext, DummyDefaultCreationContext


class TestTuple(unittest.TestCase):

    def test_wrap_lower_case(self):
        checker = TupleFactory().create_from(tuple[int, str], DummyDefaultCreationContext())
        res = checker.check_and_wrap((1, "2"), DummyExecutionContext())
        self.assertEqual((1, "2"), res)

    def test_wrap_upper_case(self):
        checker = TupleFactory().create_from(Tuple[int, str], DummyDefaultCreationContext())
        res = checker.check_and_wrap((1, "2"), DummyExecutionContext())
        self.assertEqual((1, "2"), res)

    def test_not_a_tuple(self):
        checker = TupleFactory().create_from(tuple[int, str], DummyDefaultCreationContext())

        with self.assertRaises(UntypyTypeError) as cm:
            res = checker.check_and_wrap(1, DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "tuple[int, str]")
        self.assertEqual(i, "^^^^^^^^^^^^^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_negative(self):
        checker = TupleFactory().create_from(tuple[int, str], DummyDefaultCreationContext())

        with self.assertRaises(UntypyTypeError) as cm:
            res = checker.check_and_wrap((1, 2), DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "tuple[int, str]")
        self.assertEqual(i, "           ^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_negative_delayed(self):
        checker = TupleFactory().create_from(tuple[int, DummyDelayedType], DummyDefaultCreationContext())

        res = checker.check_and_wrap((1, 2), DummyExecutionContext())
        with self.assertRaises(UntypyTypeError) as cm:
            res[1].use()

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "tuple[int, DummyDelayedType]")
        self.assertEqual(i, "           ^^^^^^^^^^^^^^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.last_responsable().file, "dummy")
