import unittest
from typing import Protocol, Union, TypeVar, Generic, NoReturn

import untypy
from test.util import DummyDefaultCreationContext, DummyExecutionContext, location_of
from untypy.error import UntypyTypeError
from untypy.impl import ProtocolFactory, GenericFactory
from untypy.impl.union import UnionFactory


class A:
    pass


class ParrentB:
    pass


class B(ParrentB):
    pass


class ProtoReturnB(Protocol):
    @untypy.patch
    def meth(self) -> B:
        raise NotImplementedError


class ProtoReceiveB(Protocol):
    @untypy.patch
    def meth(self, b: B) -> None:
        raise NotImplementedError


class TestProtocolTestCommon(unittest.TestCase):

    def setUp(self) -> None:
        self.sig_b = "B"
        self.ProtoReturnB = ProtoReturnB
        self.ProtoReceiveB = ProtoReceiveB
        self.ProtoReturnBName = "ProtoReturnB(Protocol)"
        self.ProtoReceiveBName = "ProtoReceiveB(Protocol)"
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

        self.assertEqual(t, self.ProtoReturnBName)
        self.assertEqual(i, "^" * len(self.ProtoReturnBName))
        self.assertEqual(cm.exception.last_responsable().file, "dummy")

    def test_receiving_wrong_arguments(self):
        class Concrete:
            @untypy.patch
            def meth(self, b: ParrentB) -> None:
                pass

        instance = self.checker_arg.check_and_wrap(Concrete(), DummyExecutionContext())
        with self.assertRaises(UntypyTypeError) as cm:
            instance.meth(A())

        (t, i) = cm.exception.next_type_and_indicator()

        self.assertEqual(t, f"meth(self: Self, b: {self.sig_b}) -> None")
        self.assertEqual(cm.exception.last_responsable().file, __file__)

        self.assertEqual(cm.exception.last_declared(), location_of(self.ProtoReceiveB.meth))

    def test_return_wrong_arguments(self):
        class Concrete:
            @untypy.patch
            def meth(self) -> B:
                return A()

        instance = self.checker_return.check_and_wrap(Concrete(), DummyExecutionContext())
        with self.assertRaises(UntypyTypeError) as cm:
            instance.meth()

        (t, i) = cm.exception.next_type_and_indicator()

        self.assertEqual(t, f"meth(self: Self) -> B")
        self.assertEqual(cm.exception.last_responsable().file, __file__)
        self.assertEqual(cm.exception.last_declared(), location_of(Concrete.meth))

    def test_concrete_wrong_argument_signature(self):
        class Concrete:
            @untypy.patch
            def meth(self, b: A) -> NoReturn:
                pass

        instance = self.checker_arg.check_and_wrap(Concrete(), DummyExecutionContext())
        with self.assertRaises(UntypyTypeError) as cm:
            instance.meth(B())

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, "meth(self: Self, b: A) -> None")
        self.assertEqual(i, "                    ^")
        self.assertEqual(cm.exception.last_responsable(), location_of(Concrete.meth))
        self.assertEqual(cm.exception.last_declared(), location_of(self.ProtoReceiveB.meth))

    def test_concrete_wrong_return_signature(self):
        class Concrete:
            @untypy.patch
            def meth(self) -> A:
                return A()

        instance = self.checker_return.check_and_wrap(Concrete(), DummyExecutionContext())
        with self.assertRaises(UntypyTypeError) as cm:
            instance.meth()

        (t, i) = cm.exception.next_type_and_indicator()
        i = i.rstrip()

        self.assertEqual(t, f"meth(self: Self) -> {self.sig_b}")
        self.assertEqual(cm.exception.last_responsable(), location_of(Concrete.meth))
        self.assertEqual(cm.exception.last_declared(), location_of(self.ProtoReturnB.meth))


class TestProtocolGenerics(TestProtocolTestCommon):
    def setUp(self) -> None:
        T = TypeVar("T")

        class ProtoReturnGeneric(Protocol[T]):
            @untypy.patch
            def meth(self) -> T:
                raise NotImplementedError

        class ProtoReceiveGeneric(Protocol[T]):
            @untypy.patch
            def meth(self, b: T) -> None:
                raise NotImplementedError

        self.sig_b = "~T=B"
        self.ProtoReturnB = ProtoReturnGeneric
        self.ProtoReceiveB = ProtoReceiveGeneric
        self.ProtoReturnBName = "ProtoReturnGeneric[~T=B]"
        self.ProtoReceiveBName = "ProtoReceiveGeneric(Protocol)"
        self.checker_return = ProtocolFactory().create_from(ProtoReturnGeneric[B], DummyDefaultCreationContext())
        self.checker_arg = ProtocolFactory().create_from(ProtoReceiveGeneric[B], DummyDefaultCreationContext())


class TestProtocolGenericTypeRepr(unittest.TestCase):

    def test_protocol_type_repr(self):
        T = TypeVar("T")

        # There was a bug, causing T to be listet multiple Times.
        @untypy.patch
        class Proto(Generic[T]):
            @untypy.patch
            def do_it(self, a: T, b: T) -> None:
                return

        fac = GenericFactory().create_from(Proto[int], DummyDefaultCreationContext())
        with self.assertRaises(UntypyTypeError) as cm:
            fac.check_and_wrap(42, DummyExecutionContext())
        self.assertEqual(cm.exception.expected, "Proto[~T=int]")


class TestProtocolSpecific(unittest.TestCase):

    def test_union_protocols(self):
        class U1:
            @untypy.patch
            def meth(self) -> str:
                return "s"

        class U2:
            @untypy.patch
            def meth(self) -> int:
                return 42

            @untypy.patch
            def meth2(self) -> int:
                return 42

        # when wrapping order matters
        UnionFactory() \
            .create_from(Union[U1, U2], DummyDefaultCreationContext()) \
            .check_and_wrap(U1(), DummyExecutionContext()) \
            .meth()
        UnionFactory() \
            .create_from(Union[U1, U2], DummyDefaultCreationContext()) \
            .check_and_wrap(U2(), DummyExecutionContext()) \
            .meth()
        UnionFactory() \
            .create_from(Union[U2, U1], DummyDefaultCreationContext()) \
            .check_and_wrap(U1(), DummyExecutionContext()) \
            .meth()
        UnionFactory() \
            .create_from(Union[U2, U1], DummyDefaultCreationContext()) \
            .check_and_wrap(U2(), DummyExecutionContext()) \
            .meth()

    def test_not_patching_if_signature_eq(self):
        class Concrete:
            @untypy.patch
            def meth(self) -> B:
                return B()

        instance = ProtocolFactory().create_from(ProtoReturnB, DummyDefaultCreationContext()).check_and_wrap(Concrete(),
                                                                                                             DummyExecutionContext())

        self.assertEqual(type(instance), Concrete)
