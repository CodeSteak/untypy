from typing import Any, Optional

from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext


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

    def base_type(self) -> type:
        return [Any]


class SelfChecker(TypeChecker):
    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        return arg

    def describe(self) -> str:
        return "Self"

    def base_type(self) -> type:
        return [Any]
