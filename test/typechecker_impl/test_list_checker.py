import unittest

from untypy.typechecker.typechecker_impl.list_checker import Checker, TypedList
from untypy.typechecker.typechecker_impl.simple_type_checker import Checker as SimpleChecker
from test.util import *


class TestListTypeChecker(ExTest):

    def test_not_a_list(self):
        with self.assertRaises(TypeError):
            Checker(SimpleChecker(int)).check("Not a list", Context())

    def test_access(self):
        lst = TypedList([1, "test", 3], SimpleChecker(int), Context())
        x = lst[0]
        with self.assertRaises(TypeError):
            x = lst[1]
        x = lst[2]

        with self.assertRaises(TypeError):
            x = lst[3::-1]

    def test_write(self):
        lst = TypedList([1, 2, 3], SimpleChecker(int), Context())
        lst += [3]
        lst += lst

        with self.assertRaises(TypeError):
           lst += ["test"]