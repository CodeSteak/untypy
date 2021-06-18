from untypy.impl.protocol import ProtocolChecker
from untypy.impl.wrappedclass import WrappedType
from untypy.interfaces import CreationContext


class BoundGenericProtocolChecker(ProtocolChecker):
    def protocol_type(self) -> str:
        return "Bound Generic"


def WrappedGenericAlias(alias, ctx: CreationContext):
    typevars = dict(zip(alias.__origin__.__parameters__, alias.__args__))
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
