import inspect
from collections import namedtuple
from types import ModuleType, FunctionType
from typing import Callable, Dict

from untypy.error import UntypyAttributeError, Location
from untypy.impl import DefaultCreationContext
from untypy.impl.any import SelfChecker
from untypy.interfaces import CreationContext, TypeChecker, ExecutionContext, WrappedFunctionContextProvider
from untypy.util import WrappedFunction, ArgumentExecutionContext, ReturnExecutionContext

Config = namedtuple('PatchConfig', 'verbose')
DefaultConfig = Config(verbose=True)
not_patching = ['__class__']

GlobalPatchedList = set()


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

    if unit in GlobalPatchedList:
        if cfg.verbose:
            print(f" Skip, already patched")
        return

    GlobalPatchedList.add(unit)

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

        return TypedFunctionBuilder(fn, DefaultCreationContext(
            typevars=dict(),
            declared_location=Location(
                file=inspect.getfile(fn),
                line_no=inspect.getsourcelines(fn)[1],
                source_line="".join(inspect.getsourcelines(fn)[0]),
            ))).build()
    else:
        return fn


class TypedFunctionBuilder(WrappedFunction):
    inner: Callable
    signature: inspect.Signature
    checkers: Dict[str, TypeChecker]

    special_args = ['self', 'cls']
    method_name_ignore_return = ['__init__']

    def __init__(self, inner: Callable, ctx: CreationContext):
        self.inner = inner
        self.signature = inspect.signature(inner)

        checkers = {}
        checked_keys = list(self.signature.parameters)

        # Remove self and cls from checking
        if len(checked_keys) > 0 and checked_keys[0] in self.special_args:
            checkers[checked_keys[0]] = SelfChecker()
            checked_keys = checked_keys[1:]

        for key in checked_keys:
            annotation = self.signature.parameters[key].annotation
            if annotation is inspect.Parameter.empty:
                raise ctx.wrap(
                    UntypyAttributeError(f"\Missing Annotation for argument '{key}' of function {inner.__name__}\n"
                                         "Partial Annotation are not supported."))

            checker = ctx.find_checker(annotation)
            if checker is None:
                raise ctx.wrap(UntypyAttributeError(f"\n\tUnsupported Type Annotation: {annotation}\n"
                                                    f"\tin argument '{key}'"))
            else:
                checkers[key] = checker

        if inner.__name__ in self.method_name_ignore_return:
            checkers['return'] = SelfChecker()
        else:
            annotation = self.signature.return_annotation
            return_checker = ctx.find_checker(annotation)
            if return_checker is None:
                raise ctx.wrap(UntypyAttributeError(f"\n\tUnsupported Type Annotation: {annotation}\n"
                                                    f"\tin return"))

            checkers['return'] = return_checker

        self.checkers = checkers

    def build(self):
        def wrapper(*args, **kwargs):
            # first is this fn
            caller = inspect.stack()[1]
            (args, kwargs) = self.wrap_arguments(lambda n: ArgumentExecutionContext(self, caller, n), args, kwargs)
            ret = self.inner(*args, **kwargs)
            return self.wrap_return(ret, ReturnExecutionContext(self))

        async def async_wrapper(*args, **kwargs):
            # first is this fn
            caller = inspect.stack()[1]
            (args, kwargs) = self.wrap_arguments(lambda n: ArgumentExecutionContext(self, caller, n), args, kwargs)
            ret = await self.inner(*args, **kwargs)
            return self.wrap_return(ret, ReturnExecutionContext(self))

        if inspect.iscoroutine(self.inner):
            w = async_wrapper
        else:
            w = wrapper

        setattr(w, '__wrapped__', self.inner)
        setattr(w, '__name__', self.inner.__name__)
        setattr(w, '__signature__', self.signature)
        setattr(w, '__wf', self)
        return w

    def wrap_arguments(self, ctxprv: WrappedFunctionContextProvider, args, kwargs):
        bindings = self.signature.bind(*args, **kwargs)
        bindings.apply_defaults()
        for name in bindings.arguments:
            check = self.checkers[name]
            ctx = ctxprv(name)
            bindings.arguments[name] = check.check_and_wrap(bindings.arguments[name], ctx)
        return (bindings.args, bindings.kwargs)

    def wrap_return(self, ret, ctx: ExecutionContext):
        check = self.checkers['return']
        return check.check_and_wrap(ret, ctx)

    def describe(self):
        return str(self.signature)

    def get_original(self):
        return self.inner

    def checker_for(self, name: str) -> TypeChecker:
        return self.checkers[name]
