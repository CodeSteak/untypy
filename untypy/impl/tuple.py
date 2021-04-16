from untypy.error import UntypyTypeError, Frame
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
        if not type(arg) is tuple or len(arg) != len(self.inner):
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))

        out = []
        idx = 0
        for elm, checker in zip(arg, self.inner):
            out.append(checker.check_and_wrap(elm, TupleExecutionContext(ctx, self.inner, idx)))
            idx += 1

        return tuple(out)

    def describe(self) -> str:
        desc = lambda s: s.describe()
        return f"Tuple[{', '.join(map(desc, self.inner))}]"


class TupleExecutionContext(ExecutionContext):
    upper: ExecutionContext
    checkers: list[TypeChecker]
    idx: int

    def __init__(self, upper: ExecutionContext, checkers: list[TypeChecker], idx: int):
        self.upper = upper
        self.checkers = checkers
        self.idx = idx

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        type_declared = "Tuple["
        indicator = " " * len(type_declared)

        for i, checker in enumerate(self.checkers):
            if i == self.idx:
                next_type, next_indicator = err.next_type_and_indicator()
                type_declared += next_type
                indicator += next_indicator
            else:
                type_declared += checker.describe()
                indicator += " " * len(checker.describe())

            if i != len(self.checkers) -1: # not last element
                type_declared += ", "
                indicator += "  "

        type_declared += "]"

        return err.with_frame(Frame(
            type_declared,
            indicator,
            None,
            None,
            None
        ))