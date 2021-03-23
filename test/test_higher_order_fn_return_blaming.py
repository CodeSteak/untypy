from typing import Callable

import untypy
from test.util import ExTest


# wrong return
def foo() -> Callable[[int], str]:
    return lambda x: 42

def bar() -> Callable[[int], str]:
    return lambda x: str(x)

class TestHigherOrderFn(ExTest):

    def setUp(self):
        untypy.enable()

    def test_right(self):
        bar()(42)

    def test_wrong_args(self):
        f = bar()
        with self.assertBlame("f('hello')"):
            f('hello')

    def test_wrong_return(self):
        f = foo()
        with self.assertBlame("return lambda x: 42"):
            f(42)