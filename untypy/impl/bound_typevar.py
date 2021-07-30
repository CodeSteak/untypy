from typing import Optional, Any, TypeVar

from untypy.interfaces import TypeCheckerFactory, CreationContext, TypeChecker


class BoundTypeVarFactory(TypeCheckerFactory):
    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if type(annotation) is TypeVar:
            (found, checker) = ctx.resolve_typevar(annotation)
            if found:
                return checker
