from untypy.error import UntypyTypeError
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from typing import Any, Optional, Union, Literal

UnionType = type(Union[int, str])


class UnionFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if type(annotation) is UnionType:
            inner = []
            for arg in annotation.__args__:
                checker = ctx.find_checker(arg)
                if checker is None:
                    return None
                else:
                    inner.append(checker)

            return UnionChecker(inner)
        else:
            return None


class UnionChecker(TypeChecker):
    inner: list[TypeChecker]

    def __init__(self, inner: list[TypeChecker]):
        self.inner = inner

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        for checker in self.inner:
            try:
                return checker.check_and_wrap(arg, ctx)
            except UntypyTypeError as _e:
                pass

        raise UntypyTypeError(
            arg,
            self.describe()
        )

    def describe(self) -> str:
        desc = lambda s: s.describe()
        return f"Union[{', '.join(map(desc, self.inner))}]"
