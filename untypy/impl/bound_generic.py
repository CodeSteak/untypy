import inspect

from untypy.error import Location
from untypy.impl import DefaultCreationContext
from untypy.impl.protocol import ProtocolChecker
from untypy.interfaces import WrappedFunction
from untypy.util import GenericExecutionContext


class BoundGenericProtocolChecker(ProtocolChecker):
    def protocol_type(self) -> str:
        return "Bound Generic"


class WrappedGenericAlias:
    def __init__(self, alias):
        self.alias = alias
        self.__origin__ = alias.__origin__
        self.__args__ = alias.__args__

    def __call__(self, *args, **kwargs):
        s = inspect.stack()[1]
        r = self.__origin__(*args, **kwargs)
        d = Location(
            file=s.filename,
            line_no=s.lineno,
            source_line='\n'.join(s.code_context))

        ctx = GenericExecutionContext(
            declared=d,
            responsable=WrappedFunction.find_location(self.alias.__origin__)
        )

        return BoundGenericProtocolChecker(self.alias, DefaultCreationContext(
            typevars=dict(),
            declared_location=d,
        )).check_and_wrap(r, ctx, signature_diff=True)
