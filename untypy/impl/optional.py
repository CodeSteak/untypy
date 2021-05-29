from typing import Any, Optional, Union

from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from untypy.util import CompoundTypeExecutionContext

UnionType = type(Union[int, str])


class OptionalFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if type(annotation) is UnionType and len(annotation.__args__) == 2 and annotation.__args__[1] is type(None):
            checker = ctx.find_checker(annotation.__args__[0])
            if checker is None:
                return None
            else:
                return OptionalChecker(checker)
        else:
            return None


class OptionalChecker(TypeChecker):
    inner: TypeChecker

    def __init__(self, inner: TypeChecker):
        self.inner = inner

    def check_and_wrap(self, arg: Any, upper: ExecutionContext) -> Any:
        if arg is None:
            return arg
        else:
            ctx = OptionalExecutionContext(upper, [self.inner], 0)
            return self.inner.check_and_wrap(arg, ctx)

    def describe(self) -> str:
        return f"Optional[{self.inner.describe()}]"

    def base_type(self) -> list[Any]:
        return [self.inner.base_type()]


class OptionalExecutionContext(CompoundTypeExecutionContext):
    def name(self):
        return "Optional"
