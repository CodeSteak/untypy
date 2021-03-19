import inspect
from collections.abc import Callable

from .typechecker import GlobalTypeManager
from .typechecker.interfaces import *

__all__ = ['wrap_function', 'TodoTypeError']


# TODO: Rewrite These Classes
class TodoExecutionContext(IExecutionContext):

    def __init__(self, caller, argument=None, parent=None, in_return=None):
        self.caller = caller
        self.parent = parent
        self.argument = argument
        self.in_return = in_return

    def blame(self, info):
        # TODO
        msg = "TYPE ERROR \n"
        responsable_line = None

        if isinstance(self.caller, inspect.FrameInfo):
            responsable_line = self.caller.code_context[0].strip()
            msg += f"{self.caller.filename[-9:]}:{self.caller.lineno} >> {self.caller.code_context[0].strip()}\n"
        elif inspect.isfunction(self.caller):
            msg += f">> {inspect.getsource(self.caller)}\n"
            responsable_line = inspect.getsource(self.caller).split('\n')[0].strip()
        else:
            msg += f">> {self.caller}\n"

        if self.argument is not None:
            msg += f"in argument {self.argument}\n"
        msg += f"{info}\n\n"

        # responsable_line is used in tests
        raise TodoTypeError(msg, responsable_line, self.in_return)

    def rescope(self, fun: Callable, argument=None, in_return=None) -> IExecutionContext:
        return TodoExecutionContext(fun, argument, self, in_return)


class TodoTypeError(TypeError):
    def __init__(self, msg, responsable_line, in_return):
        super().__init__(msg)
        self.in_return = in_return
        self.responsable_line = responsable_line


class TodoCreationContext(ICreationContext):
    def type_manager(self):
        return GlobalTypeManager


def wrap_function(fun: Callable) -> Callable:
    spec = inspect.getfullargspec(fun)
    argument_checks = {}

    for key in spec.annotations:
        ctx = TodoCreationContext()
        argument_checks[key] = GlobalTypeManager.find(spec.annotations[key], ctx)

    return FunctionDecorator(fun, spec, argument_checks)


class FunctionDecorator(Callable):
    fun: Callable

    def __init__(self, fun: Callable, spec: inspect.FullArgSpec, argument_checks):
        self.fun = fun
        self.spec = spec
        self.argument_checks = argument_checks
        self.__wrapped__ = True
        pass

    def __call__(self, *args, **kwargs):
        # TODO: varargs, kw
        # TODO: Optimise?
        stack = inspect.stack()[1:]  # first is this fn
        caller = next((e for e in stack if not e.function == '__call__'), None)

        new_args = []
        for (arg, name) in zip(args, self.spec.args):
            check = self.argument_checks.get(name)
            if check is not None:
                new_args.append(check.check(arg, TodoExecutionContext(caller, name)))
            else:
                new_args.append(arg)
        ret = self.fun(*new_args, **kwargs)
        check = self.argument_checks.get("return")
        if check is not None:
            return check.check(ret, TodoExecutionContext(self.fun, None, None, True))
        else:
            return ret
