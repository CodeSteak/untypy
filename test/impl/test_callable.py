import unittest
from typing import Callable

from untypy.error import UntypyTypeError
from untypy.impl.callable import CallableChecker, CallableFactory
from untypy.impl.dummy_delayed import DummyDelayedType
from test.util import DummyExecutionContext, DummyDefaultCreationContext
from untypy.impl import DefaultCreationContext


class TestCallable(unittest.TestCase):
    fn1: Callable
    fn2: Callable

    def setUp(self) -> None:
        self.checker = CallableFactory().create_from(Callable[[int, int], str], DummyDefaultCreationContext())
        self.fn1 = self.checker.check_and_wrap(lambda x, y: str(x // y), DummyExecutionContext())
        self.fn2 = self.checker.check_and_wrap(lambda x, y: x // y, DummyExecutionContext())

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
        self.assertEqual(cm.exception.frames[-1].responsable.file, __file__)

    def test_ret_error(self):
        with self.assertRaises(UntypyTypeError) as cm:
            self.fn2(100, 20)

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Callable[[int, int], str]")
        self.assertEqual(i, "                     ^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.frames[-1].responsable.file, "dummy")

    def test_not_a_callable(self):
        with self.assertRaises(UntypyTypeError) as cm:
            self.checker.check_and_wrap("Hello", DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Callable[[int, int], str]")
        self.assertEqual(i, "^^^^^^^^^^^^^^^^^^^^^^^^^")

        self.assertEqual(cm.exception.frames[-1].responsable.file, "dummy")

    def test_error_delayed(self):
        self.checker = CallableFactory().create_from(Callable[[int, int], DummyDelayedType], DummyDefaultCreationContext())
        fn = self.checker.check_and_wrap(lambda x, y: x // y, DummyExecutionContext())
        res = fn(1, 2)

        with self.assertRaises(UntypyTypeError) as cm:
            res.use()

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Callable[[int, int], DummyDelayedType]")
        self.assertEqual(i, "                     ^^^^^^^^^^^^^^^^")

        self.assertEqual(cm.exception.frames[-1].responsable.file, "dummy")