import inspect
from typing import Any, Optional

from ..interfaces import *


class TypeFactory(ITypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: ICreationContext) -> Optional[ITypeChecker]:
        if inspect.isclass(annotation):
            return Checker(annotation)
        else:
            return None


class Checker(ITypeChecker):
    def __init__(self, ty):
        super().__init__()
        self.ty = ty

    def check(self, arg, ctx):
        if issubclass(type(arg), self.ty):
            return arg
        else:
            ctx.blame(f"has class {type(arg)}, this class is not a subclass of {self.ty}.")
