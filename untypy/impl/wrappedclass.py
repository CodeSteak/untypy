import inspect
from typing import Any, Callable

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


class WrappedType:
    def __init__(self, inner_type: type, ctx: CreationContext):
        self.__inner_type = inner_type
        self.__ctx = ctx

        self.__constructor = getattr(inner_type, '__init__')
        (signature, checker) = find_signature(self.__constructor, ctx)
        self.__constructor_sig = signature
        self.__constructor_checker = checker

    def __call__(self, *args, **kwargs):
        caller = inspect.stack()[1]
        new = self.__inner_type.__new__(self.__inner_type)
        (args, kwargs) = wrap_arguments(self.__constructor_sig, self.__constructor_checker,
                                        lambda n: ArgumentExecutionContext(self.__constructor, caller, n),
                                        (new, *args), kwargs)
        self.__constructor(*args, **kwargs)
        return WrappedClass(new, self.__inner_type, self.__ctx)

    def __instancecheck__(cls, instance):
        if hasattr(instance, '__subclasscheck__'):
            return instance.__subclasscheck__(cls.__inner_type)
        else:
            return isinstance(instance, cls.__inner_type)

    # TODO allow static vars


class WrappedClass:

    def __init__(self, inner: Any, inner_type: type, ctx: CreationContext):
        self.__inner_type = inner_type
        self.__inner = inner
        self.__ctx = ctx

    def __getattr__(self, item):
        inner_item = getattr(self.__inner, item)
        if callable(inner_item):
            inner_item = getattr(self.__inner_type, item)
            (signature, checker) = find_signature(inner_item, self.__ctx)
            wf = WrappedClassFunction(self.__inner, inner_item, signature, checker).build()
        elif type(inner_item) == type:
            wf = WrappedType(inner_item, self.__ctx)
        else:
            # todo: allow direct access of member vars
            raise AttributeError()
        setattr(self, item, wf)
        return wf

    def __subclasscheck__(self, subclass):
        return issubclass(subclass, self.__inner_type)


class WrappedClassFunction(WrappedFunction):
    def __init__(self, me, inner: Callable,
                 signature: inspect.Signature,
                 checker: dict[str, TypeChecker]):
        self.me = me
        self.inner = inner
        self.signature = signature
        self.checker = checker

    def build(self):
        fn = self.inner

        def wrapper(*args, **kwargs):
            caller = inspect.stack()[1]
            (args, kwargs) = self.wrap_arguments(lambda n: ArgumentExecutionContext(self, caller, n),
                                                 (self.me, *args), kwargs)
            ret = fn(*args, **kwargs)
            return self.wrap_return(ret, ReturnExecutionContext(self))

        async def async_wrapper(*args, **kwargs):
            raise AssertionError("Not correctly implemented see wrapper")

        if inspect.iscoroutine(self.inner):
            w = async_wrapper
        else:
            w = wrapper

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
