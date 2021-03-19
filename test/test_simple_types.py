import untypy
from test.util import ExTest


class A:
    pass


class B(A):
    pass


class C(B):
    pass


class Other:
    pass


def test(x: int, y: B) -> str:
    return str("Hello")


# Check for return args but no input args.
def test_return(x) -> B:
    return x


class TestSimpleTypes(ExTest):

    def setUp(self):
        untypy.enable()

    def test_right_params(self):
        test(42, B())

    def test_inheritance(self):
        with self.assertBlame("test(1, A())"):
            test(1, A())

        test(2, B())

        test(3, C())

        with self.assertBlame("test(4, Other())"):
            test(4, Other())

    def test_passing_class_as_param(self):
        with self.assertBlame("test(1, B)"):
            test(1, B)

        with self.assertBlame("test(1, C)"):
            test(1, C)

    def test_return_args(self):
        with self.assertBlame("def test_return(x) -> B:"):
            test_return(A())

        with self.assertBlame("def test_return(x) -> B:"):
            test_return(Other())

        test_return(B())
        test_return(C())
