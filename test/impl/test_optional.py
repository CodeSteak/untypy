import unittest
from typing import Union, Optional

from untypy.error import UntypyTypeError
from untypy.impl import DefaultCreationContext
from untypy.impl.dummy_delayed import DummyDelayedType
from untypy.impl.optional import OptionalFactory
from untypy.util import DummyExecutionContext


class TestOptional(unittest.TestCase):

    def test_wrap(self):
        checker = OptionalFactory().create_from(Optional[int], DefaultCreationContext())
        res = checker.check_and_wrap(1, DummyExecutionContext())
        self.assertEqual(1, res)

        res = checker.check_and_wrap(None, DummyExecutionContext())
        self.assertEqual(None, res)

    def test_wrap_negative(self):
        checker = OptionalFactory().create_from(Optional[int], DefaultCreationContext())
        with self.assertRaises(UntypyTypeError) as cm:
            res = checker.check_and_wrap(23.5, DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Optional[int]")
        self.assertEqual(i, "         ^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.frames[-1].file, "dummy")

    def test_wrap_negative_delayed(self):
        checker = OptionalFactory().create_from(Optional[DummyDelayedType], DefaultCreationContext())

        res = checker.check_and_wrap(1, DummyExecutionContext())

        with self.assertRaises(UntypyTypeError) as cm:
            res.use()

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Optional[DummyDelayedType]")
        self.assertEqual(i, "         ^^^^^^^^^^^^^^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.frames[-1].file, "dummy")