import inspect

from untypy.error import UntypyTypeError, UntypyAttributeError
from untypy.impl.protocol import ProtocolChecker
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from typing import Any, Optional, Union


class SimpleFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if type(annotation) is type:
            return SimpleChecker(annotation, ctx)
        else:
            return None


class ParentProtocolChecker(ProtocolChecker):
    def protocol_type(self) -> str:
        return "Parent"


class SimpleChecker(TypeChecker):
    annotation: type
    parent_checker: Optional[ParentProtocolChecker]

    def __init__(self, annotation: type, ctx: CreationContext):
        self.annotation = annotation

        # use protocol like wrapping only there are some signatures
        if class_has_some_type_signatures(annotation):
            self.parent_checker = ParentProtocolChecker(annotation, ctx)
        else:
            self.parent_checker = None

    def may_be_wrapped(self) -> bool:
        return True

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if type(arg) is self.annotation:
            return arg
        if issubclass(type(arg), self.annotation):
            if self.parent_checker is None:
                return arg
            else:
                return self.parent_checker.check_and_wrap(arg, ctx)
        else:
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))

    def describe(self) -> str:
        return self.annotation.__name__

    def base_type(self) -> Any:
        if self.parent_checker is not None:
            return self.parent_checker.base_type()
        else:
            return [self.annotation]


def class_has_some_type_signatures(clas) -> bool:
    for [name, member] in inspect.getmembers(clas):
        if inspect.isfunction(member):
            if len(inspect.getfullargspec(member).annotations) > 0:
                return True
    else:
        return False