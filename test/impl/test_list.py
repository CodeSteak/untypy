import unittest
from typing import Callable

from untypy.error import UntypyTypeError
from untypy.impl.dummy_delayed import DummyDelayedType
from untypy.impl.list import ListFactory, TypedList
from untypy.util import DummyExecutionContext
from untypy.impl import DefaultCreationContext


class TestList(unittest.TestCase):

    def setUp(self) -> None:
        self.checker = ListFactory() \
            .create_from(list[int], DefaultCreationContext())

        self.normal_list = [0, 1, 2, 3]
        self.wrapped_list = self.checker \
            .check_and_wrap(self.normal_list, DummyExecutionContext())

        self.faulty_normal_list = [0, 1, "2", 3]
        self.faulty_wrapped_list = self.checker \
            .check_and_wrap(self.faulty_normal_list, DummyExecutionContext())

    def test_side_effects(self):
        self.assertEqual(self.normal_list, self.wrapped_list)
        self.normal_list.append(4)
        self.assertEqual(self.normal_list, self.wrapped_list)
        self.wrapped_list.append(4)
        self.assertEqual(self.normal_list, self.wrapped_list)

    def test_error_delayed(self):
        checker = ListFactory()\
            .create_from(list[DummyDelayedType], DefaultCreationContext())

        lst = checker\
            .check_and_wrap([1], DummyExecutionContext())

        res = lst[0]
        with self.assertRaises(UntypyTypeError) as cm:
            res.use()

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "list[DummyDelayedType]")
        self.assertEqual(i, "     ^^^^^^^^^^^^^^^^")

        self.assertEqual(cm.exception.frames[-1].file, "dummy")


    def test_wrapping_resp(self):
        """
        The wrapping call is responsable for ensuring the list
        wrapped is typed correctly
        """
        with self.assertRaises(UntypyTypeError) as cm:
            var = self.faulty_wrapped_list[2]

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "list[int]")
        self.assertEqual(i, "     ^^^")

        self.assertEqual(cm.exception.frames[-1].file, "dummy")

    def test_wrapping_resp_by_side_effects(self):
        """
        The wrapping call is responsable for side effects not causing
        type errors
        """
        self.normal_list.append("4")
        with self.assertRaises(UntypyTypeError) as cm:
            var = self.wrapped_list[4]

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "list[int]")
        self.assertEqual(i, "     ^^^")

        self.assertEqual(cm.exception.frames[-1].file, "dummy")

    def test_self_resp(self):
        """
        when appending the caller of append is responsable
        """
        with self.assertRaises(UntypyTypeError) as cm:
            self.wrapped_list.append("4")

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "list[int]")
        self.assertEqual(i, "     ^^^")

        self.assertEqual(cm.exception.frames[-1].file, __file__)

    def test_not_a_list(self):
        with self.assertRaises(UntypyTypeError) as cm:
            self.checker.check_and_wrap("Hello", DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "list[int]")
        self.assertEqual(i, "^^^^^^^^^")

        self.assertEqual(cm.exception.frames[-1].file, "dummy")

    def test_iterator(self):
        out = []
        for i in self.wrapped_list:
            out.append(i)

        self.assertEqual(out, [0, 1, 2, 3])

        with self.assertRaises(UntypyTypeError):
            for i in self.faulty_wrapped_list:
                out.append(i)

    def test_some_basic_opts(self):
        self.assertEqual(self.wrapped_list[1], 1)
        self.assertEqual(self.wrapped_list[:], [0, 1, 2, 3])
        self.assertEqual(self.wrapped_list[1:], [1, 2, 3])

        self.wrapped_list.append(4)
        self.assertEqual(self.wrapped_list, [0, 1, 2, 3, 4])

        self.wrapped_list.pop()
        self.assertEqual(self.wrapped_list, [0, 1, 2, 3])

        self.assertEqual(f"{self.wrapped_list}", f"{self.normal_list}")
