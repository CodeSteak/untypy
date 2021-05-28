import unittest
from typing import Protocol, Callable

import untypy
from test.util import DummyDefaultCreationContext, DummyExecutionContext, location_of
from untypy.error import UntypyTypeError
from untypy.impl import ProtocolFactory


class A:
    pass

class ParrentB:
    pass

class B(ParrentB):
    pass


class ProtoReturnB(Protocol):
    def meth(self) -> B:
        raise NotImplementedError


class ProtoReceiveB(Protocol):
    def meth(self, b: B) -> None:
        raise NotImplementedError


untypy.patch(ProtoReturnB)
untypy.patch(ProtoReceiveB)


class TestProtocol(unittest.TestCase):

    def setUp(self) -> None:
        self.checker_return = ProtocolFactory().create_from(ProtoReturnB, DummyDefaultCreationContext())
        self.checker_arg = ProtocolFactory().create_from(ProtoReceiveB, DummyDefaultCreationContext())

    def test_not_implementing_methods(self):
        class NoMeth:
            def foo(self) -> None:
                pass

        with self.assertRaises(UntypyTypeError) as cm:
            self.checker_return.check_and_wrap(NoMeth(), DummyExecutionContext())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "ProtoReturnB(Protocol)")
        self.assertEqual(i, "^^^^^^^^^^^^^^^^^^^^^^")
        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_receiving_wrong_arguments(self):
        class Concrete:
            def meth(self, b: ParrentB) -> None:
                pass

        untypy.patch(Concrete)

        instance = self.checker_arg.check_and_wrap(Concrete(), DummyExecutionContext())
        with self.assertRaises(UntypyTypeError) as cm:
            instance.meth(A())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "meth(self: Self, b: B) -> None")
        self.assertEqual(i, "                    ^")
        self.assertEqual(cm.exception.last_responsable().file, __file__)

        self.assertEqual(cm.exception.last_declared(), location_of(ProtoReceiveB.meth))

    def test_return_wrong_arguments(self):
        class Concrete:
            def meth(self) -> B:
                return A()

        untypy.patch(Concrete)

        instance = self.checker_return.check_and_wrap(Concrete(), DummyExecutionContext())
        with self.assertRaises(UntypyTypeError) as cm:
            instance.meth()

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "meth(self: Self) -> B")
        self.assertEqual(i, "                    ^")
        self.assertEqual(cm.exception.last_responsable().file, __file__)
        self.assertEqual(cm.exception.last_declared(), location_of(Concrete.meth))

    def test_concrete_wrong_argument_signature(self):
        class Concrete:
            def meth(self, b: A):
                pass
        untypy.patch(Concrete)

        instance = self.checker_arg.check_and_wrap(Concrete(), DummyExecutionContext())
        with self.assertRaises(UntypyTypeError) as cm:
            instance.meth(B())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "meth(self: Self, b: A) -> None")
        self.assertEqual(i, "                    ^")
        self.assertEqual(cm.exception.last_responsable(), location_of(Concrete.meth))
        self.assertEqual(cm.exception.last_declared(), location_of(ProtoReceiveB.meth))

    def test_concrete_wrong_return_signature(self):
        class Concrete:
            def meth(self) -> A:
                return A()
        untypy.patch(Concrete)

        instance = self.checker_return.check_and_wrap(Concrete(), DummyExecutionContext())
        with self.assertRaises(UntypyTypeError) as cm:
            instance.meth()

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "meth(self: Self) -> B")
        self.assertEqual(i, "                    ^")
        self.assertEqual(cm.exception.last_responsable(), location_of(Concrete.meth))
        self.assertEqual(cm.exception.last_declared(), location_of(ProtoReturnB.meth))

    def test_not_patching_if_signature_eq(self):
        class Concrete:
            def meth(self) -> B:
                return B()
        untypy.patch(Concrete)
        instance = self.checker_return.check_and_wrap(Concrete(), DummyExecutionContext())

        self.assertEqual(type(instance), Concrete)