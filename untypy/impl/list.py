from types import GenericAlias

from untypy.error import UntypyTypeError, Frame
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from typing import Any, Optional, Union


class ListFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if type(annotation) is GenericAlias and annotation.__origin__ == list:
            assert len(annotation.__args__) == 1
            inner = ctx.find_checker(annotation.__args__[0])
            if inner is None:
                return None
            return ListChecker(inner)
        else:
            return None


class ListChecker(TypeChecker):
    inner: TypeChecker

    def __init__(self, inner: TypeChecker):
        self.inner = inner

    def may_change_identity(self) -> bool:
        return True

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if not issubclass(type(arg), list):
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))
        new_list = []
        for item in arg:
            res = self.inner.check_and_wrap(item, ListExecutionContext(ctx))
            new_list.append(res)

        return new_list

    def describe(self) -> str:
        return f"List[{self.inner.describe()}]"


class ListExecutionContext(ExecutionContext):
    upper: ExecutionContext

    def __init__(self, upper : ExecutionContext):
        self.upper = upper

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        err = err.with_frame(Frame(
                f"List[{err.expected}]",
                (" "*len("List[") + err.expected_indicator),
                None,
                None,
                None
            ))
        return self.upper.wrap(err)