import unittest
from typing import Optional

from test.util import DummyExecutionContext, DummyDefaultCreationContext
from untypy.error import UntypyTypeError
from untypy.impl.dummy_delayed import DummyDelayedType
from untypy.impl.optional import OptionalFactory


class TestOptional(unittest.TestCase):

    def test_wrap(self):
        checker = OptionalFactory().create_from(Optional[int], DummyDefaultCreationContext())
        res = checker.check_and_wrap(1, DummyExecutionContext())
        self.assertEqual(1, res)

        res = checker.check_and_wrap(None, DummyExecutionContext())
        self.assertEqual(None, res)

    def test_wrap_negative(self):
        checker = OptionalFactory().create_from(Optional[int], DummyDefaultCreationContext())
        with self.assertRaises(UntypyTypeError) as cm:
            res = checker.check_and_wrap(23.5, DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Optional[int]")
        self.assertEqual(i, "         ^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_wrap_negative_delayed(self):
        checker = OptionalFactory().create_from(Optional[DummyDelayedType], DummyDefaultCreationContext())

        res = checker.check_and_wrap(1, DummyExecutionContext())

        with self.assertRaises(UntypyTypeError) as cm:
            res.use()

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Optional[DummyDelayedType]")
        self.assertEqual(i, "         ^^^^^^^^^^^^^^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.last_responsable().file, "dummy")
