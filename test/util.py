from untypy.error import UntypyTypeError, Frame, Location
from untypy.impl import DefaultCreationContext
from untypy.interfaces import ExecutionContext, WrappedFunction


class DummyExecutionContext(ExecutionContext):
    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        (t, i) = err.next_type_and_indicator()

        return err.with_frame(Frame(
            t,
            i,
            declared=None,
            responsable=Location(
                file="dummy",
                line_no=0,
                source_line="dummy"
            )
        ))


class DummyDefaultCreationContext(DefaultCreationContext):

    def __init__(self):
        super().__init__(Location(
            file="dummy",
            line_no=0,
            source_line="dummy"
        ))


def location_of(fn):
    return WrappedFunction.find_location(fn)
