import inspect

from untypy.error import Location
from untypy.impl.protocol import ProtocolChecker
from untypy.impl.wrappedclass import WrappedType
from untypy.interfaces import CreationContext


class BoundGenericProtocolChecker(ProtocolChecker):
    def protocol_type(self) -> str:
        return "Bound Generic"


class WrappedGenericAlias(WrappedType):
    def __init__(self, alias, ctx: CreationContext):
        s = inspect.stack()[1]
        d = Location(
            file=s.filename,
            line_no=s.lineno,
            source_line='\n'.join(s.code_context))

        self.alias = alias
        super(WrappedGenericAlias, self).__init__(alias.__origin__, ctx.with_typevars(
            dict(zip(alias.__origin__.__parameters__, alias.__args__))
        ))
        self.__origin__ = alias.__origin__
        self.__args__ = alias.__args__
