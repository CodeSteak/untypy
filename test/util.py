import unittest
from contextlib import contextmanager
from typing import Callable

from untypy.decorator import TodoTypeError
from untypy.typechecker.interfaces import IExecutionContext

__all__ = ['ExTest', 'Context']

class ExTest(unittest.TestCase):

    @contextmanager
    def assertBlame(self, responsable_line):
        """
        Can be used via with statement to check blaming of type checking in unit tests.

        :param responsable_line: the line that was responsable
        """
        has_thrown = False
        try:
            yield None  # trigger body
        except TodoTypeError as e:
            has_thrown = True
            # Ignore whitespace in asserion
            self.assertEqual(e.responsable_line.strip().replace(' ', ''), responsable_line.strip().replace(' ', ''),
                             "Didn't assign blame correctly")

        self.assertTrue(has_thrown, "No type error was thrown")


class Context(IExecutionContext):
    def blame(self, param):
        raise TypeError

    def rescope(self, fun: Callable, argument=None, in_return=None) -> IExecutionContext:
        return self