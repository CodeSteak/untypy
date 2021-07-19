from typing import TypeVar, Any

from untypy.error import UntypyAttributeError
from untypy.impl.protocol import ProtocolChecker
from untypy.impl.wrappedclass import WrappedType
from untypy.interfaces import CreationContext


class BoundGenericProtocolChecker(ProtocolChecker):
    def protocol_type(self) -> str:
        return "Bound Generic"


def WrappedGenericAlias(alias, ctx: CreationContext):
    typevars = dict(zip(alias.__origin__.__parameters__, alias.__args__))
    for key, value in typevars.items():
        _checktypevar(key, value)
    ctx = ctx.with_typevars(typevars)
    # This WrappedType must also be a generic alias.
    # So it can be as Typennotation
    tname = []
    for t in typevars:
        a = ctx.find_checker(typevars[t])
        if a is None:
            tname.append(str(typevars[t]))
        else:
            tname.append(a.describe())

    wt = WrappedType(alias.__origin__, ctx, name=f"{alias.__origin__.__name__}[" + (', '.join(tname)) + "]")
    wt.__origin__ = alias.__origin__
    wt.__args__ = alias.__args__
    return wt


def _checktypevar(typevar: TypeVar, bound: Any) -> None:
    # See https://www.python.org/dev/peps/pep-0484/#covariance-and-contravariance
    if len(typevar.__constraints__) > 0:
        if typevar.__covariant__ == True:
            if not issubclass(bound, typevar.__constraints__):
                raise UntypyAttributeError(
                    f"Violation in TypeVar {typevar}: {bound} must be a covariant of one of type {typevar.__constraints__}."
                )
        elif typevar.__contravariant__ == True:
            found = False
            for c in typevar.__constraints__:
                if issubclass(c, bound):
                    found = True
            if not found:
                raise UntypyAttributeError(
                    f"Violation in TypeVar {typevar}: {bound} must be a contravariant of one of type {typevar.__constraints__}."
                )
        else:
            if not bound in typevar.__constraints__:
                raise UntypyAttributeError(
                    f"Violation in TypeVar {typevar}: {bound} must be a exactly of one of type {typevar.__constraints__}."
                    f"\nYou may want to use TypeVar(..., bound=...) instead."
                )
    elif typevar.__bound__ is not None:
        if not type(typevar.__bound__) is type:
            raise UntypyAttributeError(
                f"Bound {bound} of TypeVar {typevar} must be a type."
            )
        if not issubclass(bound, typevar.__bound__):
            raise UntypyAttributeError(
                f"Violation in TypeVar {typevar}: {bound} must be a subclass of {typevar.__bound__}."
            )
