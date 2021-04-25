import unittest
from untypy.impl.any import AnyChecker
from test.util import DummyExecutionContext, DummyDefaultCreationContext


class TestAny(unittest.TestCase):

    def test_wrap(self):
        checker = AnyChecker()

        a = [1, 2, 3]
        res = checker.check_and_wrap(a, DummyExecutionContext())

        self.assertIs(a, res)
