from untypy.error import UntypyTypeError
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from typing import Any, Optional, Union


class SimpleFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if type(annotation) is type:
            return SimpleChecker(annotation)
        else:
            return None


class SimpleChecker(TypeChecker):
    annotation: type

    def __init__(self, annotation: type):
        self.annotation = annotation

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if issubclass(type(arg), self.annotation):
            return arg
        else:
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))

    def describe(self) -> str:
        return self.annotation.__name__

    def base_type(self) -> Any:
        return [self.annotation]
