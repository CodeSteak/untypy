import unittest
from typing import Tuple, Union, Callable, Optional

from untypy.error import UntypyTypeError, UntypyAttributeError
from untypy.impl import DefaultCreationContext
from untypy.impl.dummy_delayed import DummyDelayedType
from untypy.impl.union import UnionFactory
from test.util import DummyExecutionContext, DummyDefaultCreationContext


class TestUnion(unittest.TestCase):

    def test_wrap(self):
        checker = UnionFactory().create_from(Union[int, str], DummyDefaultCreationContext())
        res = checker.check_and_wrap(1, DummyExecutionContext())
        self.assertEqual(1, res)

        res = checker.check_and_wrap("2", DummyExecutionContext())
        self.assertEqual("2", res)

    def test_wrap_negative(self):
        checker = UnionFactory().create_from(Union[int, str], DummyDefaultCreationContext())
        with self.assertRaises(UntypyTypeError) as cm:
            res = checker.check_and_wrap(23.5, DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Union[int, str]")
        self.assertEqual(i, "^^^^^^^^^^^^^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.frames[-1].responsable.file, "dummy")

    def test_wrap_negative_delayed(self):
        checker = UnionFactory().create_from(Union[DummyDelayedType, str], DummyDefaultCreationContext())

        res = checker.check_and_wrap(1, DummyExecutionContext())

        with self.assertRaises(UntypyTypeError) as cm:
            res.use()

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Union[DummyDelayedType, str]")
        self.assertEqual(i, "      ^^^^^^^^^^^^^^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.frames[-1].responsable.file, "dummy")

    def test_not_allowing_multiple_callables(self):
        with self.assertRaises(UntypyAttributeError):
            checker = UnionFactory().create_from(Union[int, str, Callable[[int], str], Callable[[str], str]],
                                                 DummyDefaultCreationContext())

        with self.assertRaises(UntypyAttributeError):
            checker = UnionFactory().create_from(Union[int, Callable[[int], str],
                                                 Union[Callable[[str], str], list[int]]],
                                                 DummyDefaultCreationContext())
