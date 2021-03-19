import untypy
from test.util import ExTest


def simple(a: list[int]) -> int:
    return 42


def simple_return(a) -> list[int]:
    return a


def nested(a: list[list[str]]):
    pass


class TestListTypes(ExTest):

    def setUp(self):
        untypy.enable()

    def test_simple(self):
        simple([1, 2, 3, 4, 5, 6])
        simple([])
        with self.assertBlame("simple([1, 2, 3, 4, 5, 6, 'hello'])"):
            simple([1, 2, 3, 4, 5, 6, 'hello'])
        with self.assertBlame("simple([1, 2, 3, 4, [5], 6]) "):
            simple([1, 2, 3, 4, [5], 6])

    def test_simple_return(self):
        simple_return([])
        simple_return([1, 2, 3, 45])

        with self.assertBlame("def simple_return(a) -> list[int]:"):
            simple_return([1, 2, 3, 4, [5], 6])

    def test_nested(self):
        nested([])
        nested([[], []])
        nested([['a', 'bc'], ['de']])

        with self.assertBlame("nested([[[]]])"):
            nested([[[]]])

        with self.assertBlame("nested([[42]])"):
            nested([[42]])
