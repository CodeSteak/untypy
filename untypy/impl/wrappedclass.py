import inspect
from types import ModuleType
from typing import Any, Callable, Union, Optional

from untypy.error import Location, UntypyAttributeError
from untypy.impl.any import SelfChecker, AnyChecker
from untypy.interfaces import TypeChecker, CreationContext, ExecutionContext, WrappedFunction, \
    WrappedFunctionContextProvider
from untypy.util import ArgumentExecutionContext, ReturnExecutionContext


def find_signature(member, ctx: CreationContext):
    signature = inspect.signature(member)
    checkers = {}
    for key in signature.parameters:
        if key == 'self':
            checkers[key] = SelfChecker()
        else:
            param = signature.parameters[key]
            if param.annotation is inspect.Parameter.empty:
                checkers[key] = AnyChecker()
                continue

            checker = ctx.find_checker(param.annotation)
            if checker is None:
                checkers[key] = AnyChecker()
                continue
            checkers[key] = checker

    if signature.return_annotation is inspect.Parameter.empty:
        checkers['return'] = AnyChecker()
    else:
        return_checker = ctx.find_checker(signature.return_annotation)
        if return_checker is None:
            raise ctx.wrap(UntypyAttributeError(f"\n\tUnsupported Type Annotation: {signature.return_annotation}\n"
                                                f"for Return Value of function {member.__name__}\n"))
        checkers['return'] = return_checker
    return signature, checkers


def wrap_arguments(signature: inspect.signature, checker: dict[str, TypeChecker],
                   ctxprv: WrappedFunctionContextProvider, args, kwargs):
    bindings = signature.bind(*args, **kwargs)
    bindings.apply_defaults()
    for name in bindings.arguments:
        check = checker[name]
        ctx = ctxprv(name)
        bindings.arguments[name] = check.check_and_wrap(bindings.arguments[name], ctx)
    return bindings.args, bindings.kwargs


class EmptyClass:
    pass


def WrappedType(template: Union[type, ModuleType], ctx: CreationContext, *, create_type: Optional[type] = None):
    blacklist = dir(EmptyClass)
    whitelist = ['__init__']

    create_fn = None
    if create_type is not None:
        create_fn = lambda: create_type.__new__(create_type)

    if type(template) is type and create_type is None:
        create_fn = lambda: template.__new__(template)

    if create_fn is None:
        def raise_err():
            raise TypeError("This is not a Callable")

        create_fn = raise_err

    list_of_attr = dict()
    for attr in dir(template):
        if attr in blacklist and attr not in whitelist:
            continue

        original = getattr(template, attr)
        if type(original) == type:  # Note: Order matters, types are also callable
            if type(template) is type:
                list_of_attr[attr] = WrappedType(original, ctx)

        elif callable(original):
            (signature, checker) = find_signature(original, ctx)
            list_of_attr[attr] = WrappedClassFunction(original, signature, checker, create_fn=create_fn).build()
    out = None
    if type(template) is type:
        out = type(f"{template.__name__}Wrapped", (template,), list_of_attr)
    elif inspect.ismodule(template):
        out = type("WrappedModule", (), list_of_attr)

    return out


class WrappedClassFunction(WrappedFunction):
    def __init__(self,
                 inner: Callable,
                 signature: inspect.Signature,
                 checker: dict[str, TypeChecker], *,
                 create_fn: Callable[[], Any]):
        self.inner = inner
        self.signature = signature
        self.checker = checker
        self.create_fn = create_fn

    def build(self):
        fn = self.inner
        name = fn.__name__

        def wrapper_cls(*args, **kwargs):
            caller = inspect.stack()[1]
            (args, kwargs) = self.wrap_arguments(lambda n: ArgumentExecutionContext(self, caller, n),
                                                 args, kwargs)
            ret = fn(*args, **kwargs)
            return self.wrap_return(ret, ReturnExecutionContext(self))

        def wrapper_self(me, *args, **kwargs):
            if name == '__init__':
                me.__inner = self.create_fn()
            caller = inspect.stack()[1]
            (args, kwargs) = self.wrap_arguments(lambda n: ArgumentExecutionContext(self, caller, n),
                                                 (me.__inner, *args), kwargs)
            ret = fn(*args, **kwargs)
            return self.wrap_return(ret, ReturnExecutionContext(self))

        async def async_wrapper(*args, **kwargs):
            raise AssertionError("Not correctly implemented see wrapper")

        if inspect.iscoroutine(self.inner):
            w = async_wrapper
        else:
            if 'self' in self.checker:
                w = wrapper_self
            else:
                w = wrapper_cls

        setattr(w, '__wrapped__', fn)
        setattr(w, '__name__', fn.__name__)
        setattr(w, '__signature__', self.signature)
        setattr(w, '__wf', self)
        return w

    def get_original(self):
        return self.inner

    def wrap_arguments(self, ctxprv: WrappedFunctionContextProvider, args, kwargs):
        bindings = self.signature.bind(*args, **kwargs)
        bindings.apply_defaults()
        for name in bindings.arguments:
            check = self.checker[name]
            ctx = ctxprv(name)
            bindings.arguments[name] = check.check_and_wrap(bindings.arguments[name], ctx)
        return bindings.args, bindings.kwargs

    def wrap_return(self, ret, ctx: ExecutionContext):
        check = self.checker['return']
        return check.check_and_wrap(ret, ctx)

    def describe(self) -> str:
        fn = WrappedFunction.find_original(self.inner)
        return f"{fn.__name__}" + str(self.signature)

    def checker_for(self, name: str) -> TypeChecker:
        return self.checker[name]

    def declared(self) -> Location:
        fn = WrappedFunction.find_original(self.inner)
        return WrappedFunction.find_location(self.inner)
