import inspect
from typing import Any, Optional, TypeVar, List

from untypy.interfaces import CreationContext, TypeChecker
from .any import AnyFactory
from .callable import CallableFactory
from .dummy_delayed import DummyDelayedFactory
from .generator import GeneratorFactory
from .generic import GenericFactory
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
    GenericFactory(),
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

    def __init__(self, typevars: dict[TypeVar, Any], declared_location: Location, checkedpkgprefixes: List[str]):
        self.typevars = typevars
        self.declared = declared_location
        self.checkedpkgprefixes = checkedpkgprefixes

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

    def resolve_typevar(self, var: TypeVar) -> (bool, Any):
        # Not result may be None
        if var in self.typevars:
            return True, self.typevars[var]
        else:
            return False, None

    def with_typevars(self, typevars: dict[TypeVar, Any]) -> CreationContext:
        tv = self.typevars.copy()
        tv.update(typevars)
        return DefaultCreationContext(tv, self.declared, self.checkedpkgprefixes)

    def should_be_type_checked(self, annotation: type) -> bool:
        m = inspect.getmodule(annotation)
        if m.__name__ in self.checkedpkgprefixes:
            return True

        for pkgs in self.checkedpkgprefixes:
            if m.__name__.startswith(pkgs + ".") or pkgs == "":
                return True

        return False
