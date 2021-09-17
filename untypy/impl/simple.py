import abc
from typing import Any, Optional, Callable

from untypy.error import UntypyTypeError
from untypy.impl.protocol import ProtocolChecker
from untypy.impl.wrappedclass import WrappedType
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext


class SimpleFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if type(annotation) is type or type(annotation) is abc.ABCMeta:
            return SimpleChecker(annotation, ctx)
        else:
            return None


class ParentProtocolChecker(ProtocolChecker):
    def protocol_type(self) -> str:
        return "Parent"

class SimpleChecker(TypeChecker):
    annotation: type
    always_wrap: bool = False
    parent_checker: Optional[Callable[[Any, ExecutionContext], Any]]

    def __init__(self, annotation: type, ctx: CreationContext):
        self.annotation = annotation
        self.always_wrap = False

        # use protocol like wrapping only if there are some signatures
        if ctx.should_be_inheritance_checked(annotation):
            if hasattr(annotation, '__patched'):
                p = ParentProtocolChecker(annotation, ctx)
                self.parent_checker = p.check_and_wrap
            else:
                # annotation is from an wrapped import
                t = WrappedType(annotation, ctx)

                def wrap(i, ctx):
                    instance = t.__new__(t)
                    instance._WrappedClassFunction__inner = i
                    instance._WrappedClassFunction__return_ctx = None
                    return instance

                # TODO: Use only on import_wrapped module
                # self.always_wrap = True
                self.parent_checker = wrap
        else:
            self.parent_checker = None


    def may_be_wrapped(self) -> bool:
        return True

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if type(arg) is self.annotation and not self.always_wrap:
            return arg
        if isinstance(arg, self.annotation):
            if self.parent_checker is None:
                return arg
            else:
                return self.parent_checker(arg, ctx)
        else:
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))

    def describe(self) -> str:
        return self.annotation.__name__

    def base_type(self) -> Any:
        return [self.annotation]
