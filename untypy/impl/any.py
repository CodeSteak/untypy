from untypy.error import UntypyTypeError
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from typing import Any, Optional, Union


class AnyFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if annotation is Any:
            return AnyChecker()
        else:
            return None


class AnyChecker(TypeChecker):
    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        return arg

    def describe(self) -> str:
        return "Any"