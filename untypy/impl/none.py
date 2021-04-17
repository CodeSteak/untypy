from untypy.error import UntypyTypeError
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from typing import Any, Optional


class NoneFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if annotation is None:
            return NoneChecker()
        else:
            return None


class NoneChecker(TypeChecker):
    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if arg is None:
            return arg
        else:
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))

    def describe(self) -> str:
        return "None"

    def base_type(self) -> list[Any]:
        return [None]