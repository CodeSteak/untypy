from typing import Callable

import untypy
from test.util import ExTest


def correct(i: int, fun: Callable[[int], str]) -> list[str]:
    return [fun(i), "42"]


def this_fn_uses_wrong_args(i: int, fun: Callable[[int], str]):
    fun("hello")


def bar(x: str) -> str:
    return x


def baz(x: int) -> str:
    return str(x)


def foo(x: int) -> str:
    return x


class TestHigherOrderFn(ExTest):

    def setUp(self):
        untypy.enable()

    def test_lambda_wrong_args(self):
        with self.assertBlame('fun("hello")'):
            this_fn_uses_wrong_args(1, lambda x: str(x))

    def test_lambda_does_not_match(self):
        # input of bar does not match signature
        with self.assertBlame('correct(2, bar)'):
            correct(2, bar)

        # return does not match
        with self.assertBlame('correct(3, lambda x: x)'):
            correct(3, lambda x: x)

    def test_right_signature_bad_implementation(self):
        with self.assertBlame('def foo(x: int) -> str:'):
            correct(4, foo)

    def test_positive_cases(self):
        correct(5, lambda x: str(x))
        correct(6, baz)

