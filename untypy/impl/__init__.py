from typing import Any, Optional

from untypy.interfaces import CreationContext, TypeChecker
from .any import AnyFactory
from .callable import CallableFactory
from .dummy_delayed import DummyDelayedFactory
from .generator import GeneratorFactory
from .iterator import IteratorFactory
from .list import ListFactory
from .literal import LiteralFactory
from .none import NoneFactory
from .optional import OptionalFactory
from .protocol import ProtocolFactory
from .simple import SimpleFactory
from .tuple import TupleFactory
from .union import UnionFactory
# More Specific Ones First
from ..error import Location, UntypyAttributeError

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
    IteratorFactory(),
    ProtocolFactory(),
    #
    SimpleFactory()
]


class DefaultCreationContext(CreationContext):

    def __init__(self, declared_location: Location):
        self.declared = declared_location

    def declared_location(self) -> Location:
        return self.declared

    def find_checker(self, annotation: Any) -> Optional[TypeChecker]:
        for fac in _FactoryList:
            res = fac.create_from(annotation=annotation, ctx=self)
            if res is not None:
                return res
        return None

    def wrap(self, err: UntypyAttributeError) -> UntypyAttributeError:
        return err.with_location(self.declared)
