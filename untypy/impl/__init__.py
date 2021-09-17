import inspect
from typing import Any, Optional, TypeVar, List, Dict

from untypy.interfaces import CreationContext, TypeChecker
from .annotated import AnnotatedFactory
from .any import AnyFactory
from .callable import CallableFactory
from .dummy_delayed import DummyDelayedFactory
from .generator import GeneratorFactory
from .generic import GenericFactory
from .interface import InterfaceFactory
from .iterator import IteratorFactory
from .list import ListFactory
from .literal import LiteralFactory
from .none import NoneFactory
from .optional import OptionalFactory
from .protocol import ProtocolFactory
from .simple import SimpleFactory
from .tuple import TupleFactory
from .union import UnionFactory
from ..error import Location, UntypyAttributeError

# More Specific Ones First
_FactoryList = [
    AnyFactory(),
    NoneFactory(),
    AnnotatedFactory(),
    ProtocolFactory(),  # must be higher then Generic
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
    InterfaceFactory(),
    #
    SimpleFactory()
]


class DefaultCreationContext(CreationContext):

    def __init__(self, typevars: Dict[TypeVar, Any], declared_location: Location, checkedpkgprefixes: List[str]):
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

    def all_typevars(self) -> List[TypeVar]:
        return list(self.typevars.keys())

    def with_typevars(self, typevars: Dict[TypeVar, Any]) -> CreationContext:
        tv = self.typevars.copy()
        tv.update(typevars)
        return DefaultCreationContext(tv, self.declared, self.checkedpkgprefixes)

    def should_be_inheritance_checked(self, annotation: type) -> bool:
        m = inspect.getmodule(annotation)

        for pkgs in self.checkedpkgprefixes:
            # Inheritance should be checked on types
            # when the type's module or its parent lies in the "user code".
            # Inheritance of types of extern modules should be not be checked.
            if m.__name__ == pkgs or m.__name__.startswith(pkgs + "."):
                return True

        return False
