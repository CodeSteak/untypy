import unittest
from typing import Literal

from untypy.error import UntypyTypeError
from untypy.impl import DefaultCreationContext
from untypy.impl.literal import LiteralChecker, LiteralFactory
from untypy.util import DummyExecutionContext


class TestLiteral(unittest.TestCase):

    def setUp(self) -> None:
        self.checker = LiteralFactory().create_from(Literal[1, 2, "3"], DefaultCreationContext())

    def test_positive_checking(self):
        self.assertEqual(self.checker.check_and_wrap(1, DummyExecutionContext()), 1)
        self.assertEqual(self.checker.check_and_wrap("3", DummyExecutionContext()), "3")

    def test_neg_checking(self):
        with self.assertRaises(UntypyTypeError) as cm:
            self.checker.check_and_wrap(4, DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Literal[1, 2, '3']")
        self.assertEqual(i, "^^^^^^^^^^^^^^^^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.frames[-1].file, "dummy")