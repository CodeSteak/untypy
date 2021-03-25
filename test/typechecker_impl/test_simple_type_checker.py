from untypy.typechecker.typechecker_impl.simple_type_checker import Checker
from test.util import *


class A:
    pass


class B(A):
    pass


class C(B):
    pass


class Other:
    pass


class TestSimpleTypeChecker(ExTest):

    def test_check_right(self):
        Checker(int).check(42, Context())

    def test_check_wrong(self):
        with self.assertRaises(TypeError):
            Checker(int).check('AA', Context())

    def test_inheritance(self):
        Checker(A).check(A(), Context())
        Checker(A).check(B(), Context())
        Checker(A).check(C(), Context())
        #
        Checker(B).check(B(), Context())
        Checker(B).check(C(), Context())
        #
        with self.assertRaises(TypeError):
            Checker(B).check(A(), Context())
        with self.assertRaises(TypeError):
            Checker(A).check(Other(), Context())

        # Class as param
        Checker(type(A)).check(A, Context())
        with self.assertRaises(TypeError):
            Checker(A).check(A, Context())