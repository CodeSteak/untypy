from typing import Any, Optional, Union

from untypy.error import UntypyTypeError, UntypyAttributeError
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from untypy.util import CompoundTypeExecutionContext

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

            return UnionChecker(inner, ctx)
        else:
            return None


class UnionChecker(TypeChecker):
    inner: list[TypeChecker]

    def __init__(self, inner: list[TypeChecker], ctx: CreationContext):
        # especially Protocols must be checked in a specific order.
        self.inner = sorted(inner, key=lambda t: -t.base_type_priority())
        dups = dict()
        for checker in inner:
            for base_type in checker.base_type():
                if base_type in dups:
                    raise ctx.wrap(UntypyAttributeError(f"{checker.describe()} is in conflict with "
                                                        f"{dups[base_type].describe()} "
                                                        f"in {self.describe()}. "
                                                        f"Types must be distinguishable inside one Union."
                                                        f"\nNote: Only one Protocol is allowed inside one Union. "
                                                        f"Classes could implement multiple Protocols by accident."
                                                        f"\nNote: Multiple Callables or Generics inside one Union are also unsupported."))
                else:
                    dups[base_type] = checker

    def check_and_wrap(self, arg: Any, upper: ExecutionContext) -> Any:
        idx = 0
        for checker in self.inner:
            ctx = UnionExecutionContext(upper, self.inner, idx)
            idx += 1
            try:
                return checker.check_and_wrap(arg, ctx)
            except UntypyTypeError as _e:
                pass

        raise upper.wrap(UntypyTypeError(
            arg,
            self.describe()
        ))

    def describe(self) -> str:
        desc = lambda s: s.describe()
        return f"Union[{', '.join(map(desc, self.inner))}]"

    def base_type(self) -> list[Any]:
        out = []
        for checker in self.inner:
            out.append(checker.base_type())
        return out


class UnionExecutionContext(CompoundTypeExecutionContext):
    def name(self):
        return "Union"
