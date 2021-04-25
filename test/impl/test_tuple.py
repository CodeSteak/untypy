import unittest
from typing import Tuple

from untypy.error import UntypyTypeError
from untypy.impl import DefaultCreationContext
from untypy.impl.tuple import TupleFactory
from untypy.util import DummyExecutionContext


class TestNone(unittest.TestCase):

    def test_wrap_lower_case(self):
        checker = TupleFactory().create_from(tuple[int, str], DefaultCreationContext())
        res = checker.check_and_wrap((1, "2"), DummyExecutionContext())
        self.assertEqual((1, "2"), res)

    def test_wrap_upper_case(self):
        checker = TupleFactory().create_from(Tuple[int, str], DefaultCreationContext())
        res = checker.check_and_wrap((1, "2"), DummyExecutionContext())
        self.assertEqual((1, "2"), res)

    def test_not_a_tuple(self):
        checker = TupleFactory().create_from(tuple[int, str], DefaultCreationContext())

        with self.assertRaises(UntypyTypeError) as cm:
            res = checker.check_and_wrap(1, DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "tuple[int, str]")
        self.assertEqual(i, "^^^^^^^^^^^^^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.frames[-1].file, "dummy")

    def test_negative(self):
        checker = TupleFactory().create_from(tuple[int, str], DefaultCreationContext())

        with self.assertRaises(UntypyTypeError) as cm:
            res = checker.check_and_wrap((1, 2), DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "tuple[int, str]")
        self.assertEqual(i, "           ^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.frames[-1].file, "dummy")
