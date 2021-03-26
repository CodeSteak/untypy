from __future__ import annotations
import inspect
from collections.abc import Callable
from typing import Optional, Any

from .error import *
from .typechecker import GlobalTypeManager
from .typechecker.interfaces import *

__all__ = ['wrap_function']

# TODO: Rewrite These Classes
class TodoExecutionContext(IExecutionContext):

    def __init__(self, caller, argument=None, parent=None, in_return=None):
        self.caller = caller
        self.parent = parent
        self.argument = argument
        self.in_return = in_return

    def _create_frame(self, typ, info) -> UntypyFrame:
        argument_name = None
        if self.in_return:
            argument_name = 'return'
        else:
            argument_name = self.argument

        return UntypyFrame(
            info=info,
            typ=typ,
            callsite=self.caller,
            argument_name=argument_name
        )

    def blame(self, info, typ=None):
        frame = self._create_frame(typ, info)
        raise UntypyError([frame])

    def blame_with_previous(self, e, info=None, typ=None):
        frame = self._create_frame(typ, info)
        raise e.with_frame(frame)

    def rescope(self, fun: Callable, argument=None, in_return=None) -> IExecutionContext:
        return TodoExecutionContext(fun, argument, self, in_return)


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
