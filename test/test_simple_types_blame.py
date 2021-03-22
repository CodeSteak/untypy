import untypy
from test.util import ExTest


def test(x: int, y: str) -> str:
    return str("Hello")


# Check for return args but no input args.
def test_return(x) -> int:
    return x


class TestSimpleTypes(ExTest):

    def setUp(self):
        untypy.enable()

    def test_right_params(self):
        test(42, 'str')

    def test_wrong_params(self):
        with self.assertBlame("test(1, 42)"):
            test(1, 42)

        with self.assertBlame("test('test', 'str')"):
            test('test', 'str')

    def test_wrong_return_args(self):
        with self.assertBlame("def test_return(x) -> int:"):
            test_return('hello')

    def test_right_return_args(self):
        test_return(42)