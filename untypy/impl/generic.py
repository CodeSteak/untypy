import typing
from typing import Optional, TypeVar, Any

from untypy.error import UntypyTypeError
from untypy.impl.protocol import ProtocolChecker
from untypy.interfaces import TypeCheckerFactory, CreationContext, TypeChecker, ExecutionContext


class GenericProtocolChecker(ProtocolChecker):
    def protocol_type(self) -> str:
        return "Generic"

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if not isinstance(arg, self.proto):
            raise ctx.wrap(UntypyTypeError(
                expected=self.describe(),
                given=arg
            )).with_note(f"Type '{type(arg).__name__}' does not inherit from '{self.proto.__name__}'")
        return super().check_and_wrap(arg, ctx)


class GenericFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        # TODO: Support other typevar features
        if type(annotation) is TypeVar:
            (found, replacement_annotation) = ctx.resolve_typevar(annotation)
            if found:
                inner = ctx.find_checker(replacement_annotation)
                if inner is not None:
                    return BoundTypeVar(inner, annotation)
                else:
                    return None
            else:
                return UnboundTypeVar(annotation)
        elif hasattr(annotation, '__args__') and hasattr(annotation.__origin__,
                                                         '__mro__') and typing.Generic in annotation.__origin__.__mro__:
            return GenericProtocolChecker(annotation, ctx)
        else:
            return None


class BoundTypeVar(TypeChecker):
    def __init__(self, inner: TypeChecker, typevar: TypeVar):
        self.inner = inner
        self.typevar = typevar

    def describe(self) -> str:
        return f"{self.typevar}={self.inner.describe()}"

    def may_be_wrapped(self) -> bool:
        return self.inner.may_be_wrapped()

    def base_type(self) -> list[Any]:
        return self.inner.base_type()

    def base_type_priority(self) -> int:
        return self.inner.base_type_priority()

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        return self.inner.check_and_wrap(arg, BoundTypeVarCtx(self, ctx))


class BoundTypeVarCtx(ExecutionContext):

    def __init__(self, bv: BoundTypeVar, ctx: ExecutionContext):
        self.bv = bv
        self.upper = ctx

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        (nt, ni) = err.next_type_and_indicator()

        if nt == err.expected and nt == self.bv.inner.describe():
            err.expected = self.bv.describe()
            err.expected_indicator = "^" * len(self.bv.describe())

        return self.upper.wrap(err)


class UnboundTypeVar(TypeChecker):

    def __init__(self, typevar: TypeVar):
        self.typevar = typevar

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        return arg

    def describe(self) -> str:
        return str(self.typevar)

    def base_type(self) -> list[Any]:
        return [self.typevar]
