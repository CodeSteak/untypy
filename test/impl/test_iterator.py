import unittest
from typing import Iterator

from test.util import DummyDefaultCreationContext, DummyExecutionContext
from untypy.error import UntypyTypeError
from untypy.impl import IteratorFactory
from untypy.impl.dummy_delayed import DummyDelayedType


def normal_iterator():
    yield 1
    yield 2
    yield 3


def create_checker(annotation):
    return IteratorFactory().create_from(annotation, DummyDefaultCreationContext())


class TestIterator(unittest.TestCase):

    def test_normal(self):
        checker = create_checker(Iterator[int])
        wrapped = checker.check_and_wrap(normal_iterator(), DummyExecutionContext())

        self.assertEqual(next(wrapped), 1)
        self.assertEqual(next(wrapped), 2)
        self.assertEqual(next(wrapped), 3)

    def test_not_an_iterator(self):
        checker = create_checker(Iterator[int])
        with self.assertRaises(UntypyTypeError) as cm:
            checker.check_and_wrap("this is a string", DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Iterator[int]")
        self.assertEqual(i, "^^^^^^^^^^^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_yield_error(self):
        # annotation incorrect             V
        checker = create_checker(Iterator[str])
        wrapped = checker.check_and_wrap(normal_iterator(), DummyExecutionContext())

        with self.assertRaises(UntypyTypeError) as cm:
            next(wrapped)

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Iterator[str]")
        self.assertEqual(i, "         ^^^")

        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_yield_error_delayed(self):
        checker = create_checker(Iterator[DummyDelayedType])
        wrapped = checker.check_and_wrap(normal_iterator(), DummyExecutionContext())

        res = next(wrapped)
        with self.assertRaises(UntypyTypeError) as cm:
            res.use()

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Iterator[DummyDelayedType]")
        self.assertEqual(i, "         ^^^^^^^^^^^^^^^^")

        self.assertEqual(cm.exception.last_responsable().file, "dummy")
