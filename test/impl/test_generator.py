import unittest
from typing import Generator

from test.util import DummyDefaultCreationContext, DummyExecutionContext
from untypy.error import UntypyTypeError
from untypy.impl import GeneratorFactory
from untypy.impl.dummy_delayed import DummyDelayedType


def gen_normal() -> Generator[int, str, bool]:
    assert "a" == (yield 1)
    assert "b" == (yield 2)
    assert "c" == (yield 3)
    return True


def gen_use_sent():
    # use dummy type to raise type exception
    (yield).use()
    return None


def create_checker(annotation):
    return GeneratorFactory().create_from(annotation, DummyDefaultCreationContext())


class TestGenerator(unittest.TestCase):

    def test_normal(self):
        checker = create_checker(Generator[int, str, bool])

        not_wrapped = gen_normal()
        wrapped = checker.check_and_wrap(gen_normal(), DummyExecutionContext())

        def test_gen_normal(generator):
            self.assertEqual(generator.send(None), 1)
            self.assertEqual(generator.send("a"), 2)
            self.assertEqual(generator.send("b"), 3)
            with self.assertRaises(StopIteration) as cm:
                generator.send("c")

            self.assertEqual(cm.exception.value, True)

        # both wrapped an unwrapped has the same behaviour
        test_gen_normal(not_wrapped)
        test_gen_normal(wrapped)

    def test_not_a_generator(self):
        checker = create_checker(Generator[int, str, bool])
        with self.assertRaises(UntypyTypeError) as cm:
            checker.check_and_wrap(42, DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Generator[int, str, bool]")
        self.assertEqual(i, "^^^^^^^^^^^^^^^^^^^^^^^^^")

        # This DummyExecutionContext is responsable
        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_yield_error(self):
        # annotation incorrect             V
        checker = create_checker(Generator[str, str, bool])
        wrapped = checker.check_and_wrap(gen_normal(), DummyExecutionContext())

        with self.assertRaises(UntypyTypeError) as cm:
            next(wrapped)

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Generator[str, str, bool]")
        self.assertEqual(i, "          ^^^")

        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_send_error(self):
        # annotation incorrect                  V
        checker = create_checker(Generator[int, int, bool])
        wrapped = checker.check_and_wrap(gen_normal(), DummyExecutionContext())

        next(wrapped)
        with self.assertRaises(UntypyTypeError) as cm:
            wrapped.send("a")

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Generator[int, int, bool]")
        self.assertEqual(i, "               ^^^")

        self.assertEqual(cm.exception.last_responsable().file, __file__)

    def test_return_error(self):
        # annotation incorrect
        # Fun-Fact: bools are also ints              V
        checker = create_checker(Generator[int, str, str])

        wrapped = checker.check_and_wrap(gen_normal(), DummyExecutionContext())

        wrapped.send(None)
        wrapped.send("a")
        wrapped.send("b")
        with self.assertRaises(UntypyTypeError) as cm:
            wrapped.send("c")

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Generator[int, str, str]")
        self.assertEqual(i, "                    ^^^")

        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_yield_error_delayed(self):
        checker = create_checker(Generator[DummyDelayedType, str, bool])
        wrapped = checker.check_and_wrap(gen_normal(), DummyExecutionContext())

        res = next(wrapped)
        with self.assertRaises(UntypyTypeError) as cm:
            res.use()

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Generator[DummyDelayedType, str, bool]")
        self.assertEqual(i, "          ^^^^^^^^^^^^^^^^")

        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_send_error_delayed(self):
        checker = create_checker(Generator[None, DummyDelayedType, None])
        wrapped = checker.check_and_wrap(gen_use_sent(), DummyExecutionContext())

        wrapped.send(None)
        with self.assertRaises(UntypyTypeError) as cm:
            wrapped.send(42)

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Generator[None, DummyDelayedType, None]")
        self.assertEqual(i, "                ^^^^^^^^^^^^^^^^")

        self.assertEqual(cm.exception.last_responsable().file, __file__)

    def test_return_error_delayed(self):
        checker = create_checker(Generator[int, str, DummyDelayedType])
        wrapped = checker.check_and_wrap(gen_normal(), DummyExecutionContext())

        wrapped.send(None)
        wrapped.send("a")
        wrapped.send("b")
        with self.assertRaises(StopIteration) as si:
            wrapped.send("c")

        with self.assertRaises(UntypyTypeError) as cm:
            si.exception.value.use()  # use dummy

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "Generator[int, str, DummyDelayedType]")
        self.assertEqual(i, "                    ^^^^^^^^^^^^^^^^")

        self.assertEqual(cm.exception.last_responsable().file, "dummy")
