import inspect

from untypy.error import Location
from untypy.impl import DefaultCreationContext
from untypy.impl.protocol import ProtocolChecker
from untypy.interfaces import WrappedFunction
from untypy.util import GenericExecutionContext


class ImportedClassProtocolChecker(ProtocolChecker):
    def protocol_type(self) -> str:
        return "Imported Class"


class WrappedGenericImportedClass:
    def __init__(self, clas, wrap_fn):
        self.__origin__ = clas
        self.__wrap_fn = wrap_fn

    def __call__(self, *args, **kwargs):
        s = inspect.stack()[1]
        # TODO: Check Constructor
        r = self.__origin__(*args, **kwargs)
        d = Location(
            file=s.filename,
            line_no=s.lineno,
            source_line='\n'.join(s.code_context))

        ctx = GenericExecutionContext(
            declared=d,
            responsable=WrappedFunction.find_location(self.__origin__)
        )

        return ImportedClassProtocolChecker(self.__origin__, DefaultCreationContext(
            typevars=dict(),
            declared_location=d,
        )).check_and_wrap(r, ctx, signature_diff=True)

    def __getattr__(self, item):
        if hasattr(self.__origin__, item):
            w = self.__wrap_fn(getattr(self.__origin__, item))
            setattr(self, item, w)
            return w
        else:
            raise KeyError(item)
