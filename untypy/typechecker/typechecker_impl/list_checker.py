from types import GenericAlias
from typing import Any, Optional

from ..interfaces import *


class ListFactory(ITypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: ICreationContext) -> Optional[ITypeChecker]:
        if type(annotation) is GenericAlias and annotation.__origin__ == list:
            assert len(annotation.__args__) == 1
            inner = ctx.type_manager().find(annotation.__args__[0], ctx)
            return Checker(inner)


class Checker(ITypeChecker):
    inner: ITypeChecker

    def __init__(self, inner: ITypeChecker):
        super().__init__()
        self.inner = inner

    def check(self, arg, ctx):
        if issubclass(type(arg), list):
            for elm in arg:
                self.inner.check(elm, ctx)
                # TODO should lambda in list be supported?
            return arg
        else:
            ctx.blame(f"has class {type(arg)}, this class is not a subclass of list.")
