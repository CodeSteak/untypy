import unittest

from test.util import DummyExecutionContext
from untypy.impl.any import AnyChecker


class TestAny(unittest.TestCase):

    def test_wrap(self):
        checker = AnyChecker()

        a = [1, 2, 3]
        res = checker.check_and_wrap(a, DummyExecutionContext())

        self.assertIs(a, res)
