from typing import Optional

from .icreationcontext import ICreationContext
from .itypechecker import ITypeChecker

__all__ = ['ITypeManager']


class ITypeManager:
    def find(self, obj, ctx: ICreationContext) -> Optional[ITypeChecker]:
        raise NotImplementedError
