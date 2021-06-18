from typing import Any, Optional, TypeVar, Callable

from untypy.error import UntypyTypeError
from untypy.impl.wrappedclass import WrappedType
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from untypy.util import ReplaceTypeExecutionContext

K = TypeVar('Key')
V = TypeVar('Value')


class DictDecl(dict):

    def __getitem__(self, item: K) -> V:
        pass

    def __setitem__(self, idx: K, value: V):
        pass


class WrappedClassReturnExecutionContext(ExecutionContext):

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        pass


class DictFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if hasattr(annotation, '__origin__') and hasattr(annotation, '__args__') and annotation.__origin__ == dict:
            assert len(annotation.__args__) == 2

            bindings = dict()
            bindings[K] = annotation.__args__[0]
            bindings[V] = annotation.__args__[1]

            # todo find better code to handle this
            k = ctx.find_checker(annotation.__args__[0])
            v = ctx.find_checker(annotation.__args__[1])

            name = f"Dict[{k.describe()}, {v.describe()}]"

            t = WrappedType(DictDecl, ctx.with_typevars(bindings))

            def wrap(i, ctx):
                instance = t.__new__(t)
                instance._WrappedClassFunction__inner = i
                instance._WrappedClassFunction__return_ctx = ReplaceTypeExecutionContext(ctx, name)
                return instance

            return DictChecker(wrap)
        else:
            return None


class DictChecker(TypeChecker):

    def __init__(self, inner: Callable[[Any, ExecutionContext], Any]):
        self.inner = inner

    def may_change_identity(self) -> bool:
        return True

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if not issubclass(type(arg), dict):
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))

        return self.inner(arg, ctx)

    def base_type(self) -> list[Any]:
        return [dict]

    def describe(self) -> str:
        return f"dict[TODO]"  # TODO
