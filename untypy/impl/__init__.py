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
from .dummy_delayed import DummyDelayedFactory
from .optional import OptionalFactory
from .generator import GeneratorFactory

# More Specific Ones First
from ..error import Location

_FactoryList = [
    AnyFactory(),
    NoneFactory(),
    CallableFactory(),
    ListFactory(),
    LiteralFactory(),
    OptionalFactory(),  # must be higher then Union
    UnionFactory(),
    TupleFactory(),
    DummyDelayedFactory(),
    GeneratorFactory(),
    #
    SimpleFactory()
]


class DefaultCreationContext(CreationContext):

    def __init__(self, declared_location : Location):
        self.declared = declared_location

    def declared_location(self) -> Location:
        return self.declared

    def find_checker(self, annotation: Any) -> Optional[TypeChecker]:
        for fac in _FactoryList:
            res = fac.create_from(annotation=annotation, ctx=self)
            if res is not None:
                return res
        return None
