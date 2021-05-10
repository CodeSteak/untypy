import inspect

from collections import namedtuple
from types import ModuleType, FunctionType
from typing import Callable, Dict, Tuple, Protocol
from untypy.impl import DefaultCreationContext

from untypy.error import UntypyAttributeError, UntypyTypeError, Frame, Location
from untypy.impl.any import AnyChecker
from untypy.interfaces import CreationContext, TypeChecker, ExecutionContext
from untypy.util import WrappedFunction, ArgumentExecutionContext, ReturnExecutionContext

Config = namedtuple('PatchConfig', 'verbose')

DefaultConfig = Config(verbose=True)

not_patching = ['__class__']


def patch_module(mod: ModuleType, cfg: Config = DefaultConfig) -> None:
    _patch_module_or_class(mod, cfg)


def patch_class(clas: type, cfg: Config = DefaultConfig) -> None:
    _patch_module_or_class(clas, cfg)


def _patch_module_or_class(unit, cfg) -> None:
    if cfg.verbose:
        if inspect.ismodule(unit):
            print(f"Patching Module: {unit}")
        elif inspect.isclass(unit):
            print(f"Patching Class: {unit}")
        else:
            print(f"Skipping: {unit}")

    if hasattr(unit, "__patched") is True:
        # Skip, already patched
        return

    setattr(unit, "__patched", True)

    for [name, member] in inspect.getmembers(unit):
        if name in not_patching:
            pass
        elif inspect.isfunction(member):
            setattr(unit, name, patch_function(member, cfg))
        elif inspect.isclass(member):
            patch_class(member, cfg)
        # else skip


def patch_function(fn: FunctionType, cfg: Config = DefaultConfig) -> Callable:
    if len(inspect.getfullargspec(fn).annotations) > 0:
        if cfg.verbose:
            print(f"Patching Function: {fn.__name__}")

        return TypedFunctionBuilder(fn, DefaultCreationContext(Location(
            file=inspect.getfile(fn),
            line_no=inspect.getsourcelines(fn)[1],
            source_line="".join(inspect.getsourcelines(fn)[0]),
        ))).build()
    else:
        return fn


class TypedFunctionBuilder(WrappedFunction):
    inner: Callable
    spec: inspect.FullArgSpec
    checkers: Dict[str, TypeChecker]

    special_args = ['self', 'cls']
    method_name_ignore_return = ['__init__']

    def __init__(self, inner: Callable, ctx: CreationContext):
        self.inner = inner
        self.spec = inspect.getfullargspec(inner)
        checkers = {}

        checked_keys = self.spec.args
        if inner.__name__ in self.method_name_ignore_return:
            checkers['return'] = AnyChecker()
        else:
            checked_keys += ['return']

        # Remove self and cls from checking
        if checked_keys[0] in self.special_args:
            checkers[checked_keys[0]] = AnyChecker()
            checked_keys = checked_keys[1:]

        for key in checked_keys:
            if key not in self.spec.annotations:
                raise UntypyAttributeError(f"\Missing Annotation for argument '{key}' of function {inner.__name__}\n"
                                           f"{inspect.getfile(inner)}:{inspect.getsourcelines(inner)[1]}\n"
                                           "Partial Annotation are not supported."
                                           )
            checker = ctx.find_checker(self.spec.annotations[key])
            if checker is None:
                # TODO: Maybe Nicer Error
                raise UntypyAttributeError(f"\n\tUnsupported Type Annotation: {self.spec.annotations[key]}\n"
                                           f"\tin argument '{key}' of function {inner.__name__}\n"
                                           f"\n"
                                           f"\tdef {inner.__name__}{inspect.signature(inner)}\t\n"
                                           f"\n"
                                           f"\t{inspect.getfile(inner)}:{inspect.getsourcelines(inner)[1]}"
                                           )
            else:
                checkers[key] = checker
        self.checkers = checkers

    def build(self):
        if inspect.isasyncgenfunction(self.inner):
            # matching type annotation currently not supported
            return self.build_coroutine()
        elif inspect.isgeneratorfunction(self.inner):
            # TODO: Error if return annotation is not Generator or Iterator
            return self.build_method()
        elif inspect.iscoroutinefunction(self.inner):
            return self.build_coroutine()
        else:
            return self.build_method()

    def build_coroutine(self):
        me = self

        async def wrapper(*args, **kwargs):
            # first is this fn
            caller = inspect.stack()[1]

            new_args = []
            for (arg, name) in zip(args, self.spec.args):
                check = me.checkers[name]
                ctx = ArgumentExecutionContext(me, caller, name)
                res = check.check_and_wrap(arg, ctx)
                new_args.append(res)

            ret = await me.inner(*new_args, **kwargs)
            check = me.checkers['return']
            ret = check.check_and_wrap(ret, ReturnExecutionContext(me))
            return ret

        wrap = wrapper
        # add in signature so it can be retrieved by inspect.
        sig = inspect.Signature.from_callable(me.inner)
        setattr(wrap, '__signature__', sig)
        setattr(wrap, '__wrapped__', self.inner)
        setattr(wrap, '__name__', self.inner.__name__)
        setattr(wrap, '__file__', inspect.getfile(self.inner))

        setattr(wrap, '__checkers', self.checkers)
        setattr(wrap, '__wf', self)
        return wrap

    def build_method(self):
        me = self

        def wrapper(*args, **kwargs):
            # first is this fn
            caller = inspect.stack()[1]

            new_args = []
            for (arg, name) in zip(args, self.spec.args):
                check = me.checkers[name]
                ctx = ArgumentExecutionContext(me, caller, name)
                res = check.check_and_wrap(arg, ctx)
                new_args.append(res)

            ret = me.inner(*new_args, **kwargs)
            check = me.checkers['return']
            ret = check.check_and_wrap(ret, ReturnExecutionContext(me))
            return ret

        wrap = wrapper
        # add in signature so it can be retrieved by inspect.
        sig = inspect.Signature.from_callable(me.inner)
        setattr(wrap, '__signature__', sig)
        setattr(wrap, '__wrapped__', self.inner)
        setattr(wrap, '__name__', self.inner.__name__)
        setattr(wrap, '__file__', inspect.getfile(self.inner))

        setattr(wrap, '__checkers', self.checkers)
        setattr(wrap, '__wf', self)
        return wrap

    def wrapped_original(self) -> Callable:
        return self.inner

    def wrapped_fullspec(self) -> inspect.FullArgSpec:
        return self.spec

    def wrapped_checker(self) -> dict[str, TypeChecker]:
        return self.checkers
