import inspect
import typing
from typing import Callable, Dict

from untypy.error import UntypyAttributeError
from untypy.impl.any import SelfChecker
from untypy.interfaces import WrappedFunction, TypeChecker, CreationContext, WrappedFunctionContextProvider, \
    ExecutionContext
from untypy.util import ArgumentExecutionContext, ReturnExecutionContext


class TypedFunctionBuilder(WrappedFunction):
    inner: Callable
    signature: inspect.Signature
    checkers: Dict[str, TypeChecker]

    special_args = ['self', 'cls']
    method_name_ignore_return = ['__init__']

    def __init__(self, inner: Callable, ctx: CreationContext):
        self.inner = inner
        self.signature = inspect.signature(inner)

        # SEE: https://www.python.org/dev/peps/pep-0563/#id7
        annotations = typing.get_type_hints(inner)

        checkers = {}
        checked_keys = list(self.signature.parameters)

        # Remove self and cls from checking
        if len(checked_keys) > 0 and checked_keys[0] in self.special_args:
            checkers[checked_keys[0]] = SelfChecker()
            checked_keys = checked_keys[1:]

        for key in checked_keys:
            if self.signature.parameters[key].annotation is inspect.Parameter.empty:
                raise ctx.wrap(
                    UntypyAttributeError(f"\Missing Annotation for argument '{key}' of function {inner.__name__}\n"
                                         "Partial Annotation are not supported."))
            annotation = annotations[key]
            checker = ctx.find_checker(annotation)
            if checker is None:
                raise ctx.wrap(UntypyAttributeError(f"\n\tUnsupported Type Annotation: {annotation}\n"
                                                    f"\tin argument '{key}'"))
            else:
                checkers[key] = checker

        if inner.__name__ in self.method_name_ignore_return:
            checkers['return'] = SelfChecker()
        else:
            if not 'return' in annotations:
                raise ctx.wrap(
                    UntypyAttributeError(f"\Missing Annotation for return value of function {inner.__name__}\n"
                                         "Partial Annotation are not supported. Use 'None' or 'NoReturn'"
                                         "for specifying no return value."))
            annotation = annotations['return']
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
