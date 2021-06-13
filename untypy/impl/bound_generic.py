from untypy.impl.protocol import ProtocolChecker
from untypy.impl.wrappedclass import WrappedType
from untypy.interfaces import CreationContext


class BoundGenericProtocolChecker(ProtocolChecker):
    def protocol_type(self) -> str:
        return "Bound Generic"


def WrappedGenericAlias(alias, ctx: CreationContext):
    ctx = ctx.with_typevars(
        dict(zip(alias.__origin__.__parameters__, alias.__args__))
    )
    return WrappedType(alias.__origin__, ctx)
