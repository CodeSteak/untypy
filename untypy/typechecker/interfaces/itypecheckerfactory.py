from typing import Any, Optional

from .icreationcontext import ICreationContext
from .itypechecker import ITypeChecker

__all__ = ['ITypeCheckerFactory']


class ITypeCheckerFactory:

    def create_from(self, annotation: Any, ctx: ICreationContext) -> Optional[ITypeChecker]:
        """
        Try to create instance of this object

        :param annotation: The Type the function was annotated with
        :param ctx: context
        :return:
        """
        raise NotImplementedError
