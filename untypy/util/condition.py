import inspect
import re
from collections.abc import Callable
from typing import Optional

from untypy.error import UntypyAttributeError, UntypyTypeError, Frame
from untypy.interfaces import ExecutionContext, WrappedFunction

WrappedFunctionContextProvider = Callable[[str], ExecutionContext]


class FunctionCondition:

    def __init__(self):
        self.precondition = []
        self.postcondition = []
        self.func = None
        pass

    def prehook(self, boundargs, ctx: WrappedFunctionContextProvider):
        for p in self.precondition:
            bindings = {}
            for name in inspect.signature(p).parameters:
                if name in boundargs.arguments:
                    bindings[name] = boundargs.arguments[name]
                else:
                    raise UntypyAttributeError(
                        f"Did not find argument {name} of precondition in function.",
                        locations=[
                            WrappedFunction.find_location(p),
                            WrappedFunction.find_location(self.func),
                        ]
                    )
            if not p(**bindings):
                lsource = find_lambdasource(p)
                if lsource is not None:
                    expected = f"passing: {lsource}"
                else:
                    expected = "passing precondition"

                err = UntypyTypeError(
                    bindings,
                    expected
                )
                err = err.with_note("Failed precondition.")
                err = err.with_frame(Frame(
                    expected,
                    "",
                    declared=WrappedFunction.find_location(p),
                    responsable=None,
                ))
                raise ctx(0).wrap(err)

    def posthook(self, ret, boundargs, ctx: ExecutionContext):
        for p in self.postcondition:
            bindings = {}
            for name in inspect.signature(p).parameters:
                if name == "ret":
                    bindings["ret"] = ret
                elif name in boundargs.arguments:
                    bindings[name] = boundargs.arguments[name]
                else:
                    raise UntypyAttributeError(
                        f"Did not find argument {name} of postcondition in function.",
                        locations=[
                            WrappedFunction.find_location(p),
                            WrappedFunction.find_location(self.func),
                        ]
                    )
            if not p(**bindings):
                lsource = find_lambdasource(p)
                if lsource is not None:
                    expected = f"passing: {lsource}"
                else:
                    expected = "passing postcondition"

                given = ret.__repr__()
                err = UntypyTypeError(
                    given,
                    expected,
                ).with_note("Failed postcondition").with_frame(Frame(
                    expected,
                    "",
                    declared=WrappedFunction.find_location(p),
                    responsable=None,
                ))
                raise ctx.wrap(err)


def find_lambdasource(fn) -> Optional[str]:
    """
    tries to retuns body of precondition or postcondition annotation
    """
    try:
        fn = WrappedFunction.find_original(fn)
        source = inspect.getsource(fn).split('\n')
        m = re.match('@[a-zA-Z_\.]+\((.*)\)', source[0])
        if m is not None and len(m.groups()) == 1:
            return m.group(1)
    except:
        return None
