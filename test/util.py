import unittest
from contextlib import contextmanager

from untypy.decorator import TodoTypeError


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
