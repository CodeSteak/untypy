from types import GenericAlias
from typing import Any, Optional

from untypy.interfaces import CreationContext, TypeChecker
from .any import AnyFactory

from .callable import CallableFactory
from .list import ListFactory
from .literal import LiteralFactory
from .none import NoneFactory
from .simple import SimpleFactory
from .tuple import TupleFactory
from .union import UnionFactory

# More Specific Ones First
_FactoryList = [
    AnyFactory(),
    NoneFactory(),
    CallableFactory(),
    ListFactory(),
    LiteralFactory(),
    UnionFactory(),
    TupleFactory(),
    #
    SimpleFactory()
]


class DefaultCreationContext(CreationContext):

    def find_checker(self, annotation: Any) -> Optional[TypeChecker]:
        print(annotation)
        print(issubclass(type(annotation), GenericAlias))
        print("---")
        for fac in _FactoryList:
            res = fac.create_from(annotation=annotation, ctx=self)
            if res is not None:
                return res
        return None