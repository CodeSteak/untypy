import unittest
from typing import Callable

from untypy.error import UntypyTypeError
from untypy.impl.callable import CallableChecker, CallableFactory
from untypy.util import DummyExecutionContext
from untypy.impl import DefaultCreationContext


class TestCallable(unittest.TestCase):
    fn1: Callable
    fn2: Callable

    def setUp(self) -> None:
        checker = CallableFactory().create_from(Callable[[int, int], str], DefaultCreationContext())
        self.fn1 = checker.check_and_wrap(lambda x, y: str(x // y), DummyExecutionContext())
        self.fn2 = checker.check_and_wrap(lambda x, y: x // y, DummyExecutionContext())

    def test_normal(self):
        self.assertEqual(self.fn1(100, 20), "5")

    def test_is_callable(self):
        self.assertTrue(callable(self.fn1))

    def test_arg_error(self):
        with self.assertRaises(UntypyTypeError) as cm:
            self.fn1(100, "20")

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Callable[[int, int], str]")
        self.assertEqual(i, "               ^^^")

        # This file is responsable
        self.assertEqual(cm.exception.frames[-1].file, __file__)

    def test_ret_error(self):
        with self.assertRaises(UntypyTypeError) as cm:
            self.fn2(100, 20)

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Callable[[int, int], str]")
        self.assertEqual(i, "                     ^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.frames[-1].file, "dummy")