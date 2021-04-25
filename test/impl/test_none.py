import unittest

from untypy.error import UntypyTypeError
from untypy.impl import DefaultCreationContext
from untypy.impl.none import NoneFactory
from untypy.util import DummyExecutionContext


class TestNone(unittest.TestCase):

    def test_wrap(self):
        checker = NoneFactory().create_from(None, DefaultCreationContext())

        res = checker.check_and_wrap(None, DummyExecutionContext())
        self.assertEqual(None, res)

    def test_wrap_negative(self):
        checker = NoneFactory().create_from(None, DefaultCreationContext())

        with self.assertRaises(UntypyTypeError) as cm:
            res = checker.check_and_wrap(12, DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "None")
        self.assertEqual(i, "^^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.frames[-1].file, "dummy")