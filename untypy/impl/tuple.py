from untypy.error import UntypyTypeError
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from typing import Any, Optional, Tuple

TupleType = type(Tuple[str, int])


class TupleFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if type(annotation) is TupleType:
            inner = []
            for arg in annotation.__args__:
                checker = ctx.find_checker(arg)
                if checker is None:
                    return None
                else:
                    inner.append(checker)

            return TupleChecker(inner)
        else:
            return None


class TupleChecker(TypeChecker):
    inner: list[TypeChecker]

    def __init__(self, inner: list[TypeChecker]):
        self.inner = inner

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        return arg

    def describe(self) -> str:
        desc = lambda s: s.describe()
        return f"Tuple[{', '.join(map(desc, self.inner))}]"
