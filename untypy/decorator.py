import inspect
from collections.abc import Callable

from .typechecker import GlobalTypeManager
from .typechecker.interfaces import *

__all__ = ['wrap_function']


class TodoExecutionContext(IExecutionContext):

    def __init__(self, caller, argument=None, parent=None):
        self.caller = caller
        self.parent = parent
        self.argument = argument

    def blame(self, msg):
        # TODO
        print("FAILED")
        if isinstance(self.caller, inspect.FrameInfo):
            print(f"{self.caller.filename[-9:]}:{self.caller.lineno} >> {self.caller.code_context[0].strip()}")
        elif inspect.isfunction(self.caller):
            print(f">> {inspect.getsource(self.caller)}")
        else:
            print(f">> {self.caller}")

        if self.argument is not None:
            print(f"in argument {self.argument}")
        print(f"{msg}")
        print(f" ")

        raise TypeError()

    def rescope(self, fun: Callable, argument=None) -> IExecutionContext:
        return TodoExecutionContext(fun, argument, self)


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
        caller = next((e for e in stack if not hasattr(e.function, '__wrapped__')), None)

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
            return check.check(ret, TodoExecutionContext(self.fun))
        else:
            return ret
