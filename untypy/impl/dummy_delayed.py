from typing import Any, Optional

from untypy.error import UntypyTypeError
from untypy.interfaces import TypeChecker, CreationContext, TypeCheckerFactory, ExecutionContext


class DummyDelayedType:
    """
    This class is used for raising delayed type checking errors.
    """
    pass


class DummyDelayedFactory(TypeCheckerFactory):
    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if annotation is DummyDelayedType:
            return DummyDelayedChecker()
        else:
            return None


class DummyDelayedChecker(TypeChecker):
    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        return DummyDelayedWrapper(ctx)

    def describe(self) -> str:
        return "DummyDelayedType"

    def base_type(self) -> list[Any]:
        return []


class DummyDelayedWrapper:
    upper: ExecutionContext

    def __init__(self, upper: ExecutionContext):
        self.upper = upper

    def use(self):
        raise self.upper.wrap(UntypyTypeError(
            "<omitted>",
            "DummyDelayedType"
        ))
