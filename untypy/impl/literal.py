from typing import Any, Optional, Literal

from untypy.error import UntypyTypeError
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext

LiteralType = type(Literal[42])


class LiteralFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if type(annotation) is LiteralType and annotation.__origin__ == Literal:
            return LiteralChecker(annotation.__args__)
        else:
            return None


class LiteralChecker(TypeChecker):
    inner: list[Any]

    def __init__(self, inner: list[Any]):
        self.inner = inner

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if arg in self.inner:
            return arg
        else:
            raise ctx.wrap(UntypyTypeError(
                arg,
                self.describe()
            ))

    def base_type(self) -> list[Any]:
        return self.inner[:]

    def describe(self) -> str:
        strings = map(lambda v: "%r" % v, self.inner)
        return f"Literal[{', '.join(strings)}]"
