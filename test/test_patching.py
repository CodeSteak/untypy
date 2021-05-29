import inspect
import unittest

import test.patching_dummy.unpatched
import untypy
from untypy.error import UntypyTypeError


class TestPatching(unittest.TestCase):

    def test_not_patching_other_modules(self):
        import test.patching_dummy.b
        import test.patching_dummy.b.b_sub
        untypy.enable(recursive=False, root=test.patching_dummy.b)

        with self.assertRaises(UntypyTypeError):
            test.patching_dummy.b.fn_one("wrong_arg")

        with self.assertRaises(UntypyTypeError):
            test.patching_dummy.b.fn_two("wrong_arg")

        # method of b_sub
        test.patching_dummy.b.b_sub.fn_two("wrong_arg")
        # test other modules
        test.patching_dummy.unpatched.fn_one("wrong_arg")

    def test_recursive_patching(self):
        import test.patching_dummy.a
        import test.patching_dummy.a.a_sub

        untypy.enable(recursive=True, root=test.patching_dummy.a)

        with self.assertRaises(UntypyTypeError):
            test.patching_dummy.a.fn_one("wrong_arg")

        with self.assertRaises(UntypyTypeError):
            test.patching_dummy.a.fn_two("wrong_arg")

        with self.assertRaises(UntypyTypeError):
            test.patching_dummy.a.a_sub.fn_two("wrong_arg")

        # test other modules
        test.patching_dummy.unpatched.fn_one("wrong_arg")

    def test_patching_classes(self):
        import test.patching_dummy.patching_classes as c
        untypy.enable(recursive=True, root=c)

        # ok
        self.assertEqual(c.A(10).add(5), 15)

        with self.assertRaises(UntypyTypeError):
            c.A("not an int")

        i = c.A(10)
        with self.assertRaises(UntypyTypeError):
            i.add("45")

    def test_patching_does_not_change_signature(self):
        import test.patching_dummy.patching_does_not_change_signature as p

        sig_before = inspect.getfullargspec(p.fun)
        sig_meth_before = inspect.getfullargspec(p.SomeClass.meth)

        untypy.enable(recursive=True, root=p)

        sig_after = inspect.getfullargspec(p.fun)
        sig_meth_after = inspect.getfullargspec(p.SomeClass.meth)

        self.assertEqual(sig_before, sig_after)
        self.assertEqual(sig_meth_before, sig_meth_after)

    def test_argument_types(self):
        import test.patching_dummy.argument_types as a

        untypy.enable(recursive=True, root=a)

        self.assertEqual(a.kwargs(c=True, b="hello", a=42), (True, 42, "hello"))
        with self.assertRaises(UntypyTypeError):
            a.kwargs(c=True, b="hello", a="not an int")

        self.assertEqual(a.default_args(10), "hello")
