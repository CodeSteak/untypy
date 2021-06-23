from typing import Any, Optional, Tuple

from untypy.error import UntypyTypeError
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from untypy.util import CompoundTypeExecutionContext

TupleType = type(Tuple[str, int])
TupleTypeB = type(tuple[str, int])


class TupleFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if (type(annotation) is TupleType or type(annotation) is TupleTypeB) and annotation.__origin__ == tuple:
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
        if not type(arg) is tuple or len(arg) != len(self.inner):
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))

        out = []
        idx = 0
        for elm, checker in zip(arg, self.inner):
            out.append(checker.check_and_wrap(elm, TupleExecutionContext(ctx, self.inner, idx)))
            idx += 1

        return tuple(out)

    def base_type(self) -> Any:
        out = []
        for checker in self.inner:
            out.append(checker.base_type())
        return tuple(out)

    def describe(self) -> str:
        desc = lambda s: s.describe()
        return f"Tuple[{', '.join(map(desc, self.inner))}]"


class TupleExecutionContext(CompoundTypeExecutionContext):
    def name(self):
        return "Tuple"
