import inspect
from collections.abc import Callable

from .typechecker import GlobalTypeManager, ITypeContext

__all__ = ['wrap_function']


class TodoContext(ITypeContext):
    def __init__(self, fun=None, arg=None, extra=None):
        self.fun = fun
        self.arg = arg
        self.extra = extra

    def fail(self, info):
        print("FAILED")
        if self.fun is not None:
            print(f"fn: {inspect.getsource(self.fun)}")
        if self.arg is not None:
            print(f"in argument {self.arg}")
        if self.extra is not None:
            for e in self.extra:
                print(f"{e}")
        print(f"{info}")
        print(f" ")

    def type_manager(self):
        return GlobalTypeManager

    def wrap_function(self, fun: Callable):
        if hasattr(fun, '__wrapped__'):
            return fun
        else:
            return wrap_function(fun)

    def rescope(self, fun=None, arg=None, extra=None) -> ITypeContext:
        return TodoContext(fun, arg, extra)


def wrap_function(fun: Callable) -> Callable:
    spec = inspect.getfullargspec(fun)
    argument_checks = {}

    for key in spec.annotations:
        ctx = TodoContext(fun, key)
        argument_checks[key] = GlobalTypeManager.find(spec.annotations[key], ctx)

    ctx = TodoContext(fun)
    return FunctionDecorator(fun, spec, argument_checks, ctx)


class FunctionDecorator(Callable):
    fun: Callable

    def __init__(self, fun: Callable, spec: inspect.FullArgSpec, argument_checks, ctx):
        self.fun = fun
        self.spec = spec
        self.argument_checks = argument_checks
        self.ctx = ctx
        self.__wrapped__ = True
        pass

    def __call__(self, *args, **kwargs):
        # TODO: varargs, kw
        new_args = []
        for (arg, name) in zip(args, self.spec.args):
            check = self.argument_checks.get(name)
            if check is not None:
                new_args.append(check.check(self.fun, arg, self.ctx.rescope(self.fun, name)))
            else:
                new_args.append(arg)

        ret = self.fun(*args, **kwargs)
        check = self.argument_checks.get("return")
        if check is not None:
            return check.check(self.fun, ret, self.ctx.rescope(self.fun, None, ["In return"]))
        else:
            return ret
