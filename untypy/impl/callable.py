import inspect

from untypy.error import UntypyTypeError, UntypyAttributeError, Frame
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from typing import Any, Optional, Callable, Union, Tuple
from collections.abc import Callable as AbcCallable

# These Types are prefixed with an underscore...
CallableTypeOne = type(Callable[[], None])
CallableTypeTwo = type(AbcCallable[[], None])


class CallableFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if type(annotation) == CallableTypeOne or type(annotation) == CallableTypeTwo:
            return CallableChecker(annotation, ctx)
        else:
            return None


class CallableChecker(TypeChecker):
    return_checker: TypeChecker
    argument_checker: list[TypeChecker]

    def __init__(self, annotation: Union[CallableTypeOne, CallableTypeTwo], ctx: CreationContext):
        arguments_ty = annotation.__args__[:-1]
        return_ty = annotation.__args__[-1]

        # TODO:
        return_checker = ctx.find_checker(return_ty)
        if return_checker is None:
            raise UntypyAttributeError(f"TODO ERROR MESSAGE - Return Type Annotation not found. {return_ty}")

        argument_checker = []
        for arg in arguments_ty:
            checker = ctx.find_checker(arg)
            if checker is None:
                raise UntypyAttributeError(f"TODO ERROR MESSAGE - Argument Type Annotation not found. {arg}")
            argument_checker.append(checker)

        self.return_checker = return_checker
        self.argument_checker = argument_checker

    def may_be_wrapped(self) -> bool:
        return True

    def base_type(self) -> list[Any]:
        return [Callable]

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if callable(arg):
            return TypedCallable(arg, self.return_checker, self.argument_checker, ctx)
        else:
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))

    def describe(self) -> str:
        arguments = ", ".join(map(lambda e: e.describe(), self.argument_checker))
        return f"Callable[[{arguments}], {self.return_checker.describe()}]"


class TypedCallable(Callable):
    return_checker: TypeChecker
    argument_checker: list[TypeChecker]
    inner: Callable
    ctx: ExecutionContext

    def __init__(self, inner: Callable, return_checker: TypeChecker,
                 argument_checker: list[TypeChecker], ctx: ExecutionContext):
        self.inner = inner
        self.return_checker = return_checker
        self.argument_checker = argument_checker
        self.ctx = ctx

    def __call__(self, *args, **kwargs):
        # first is this fn
        stack = inspect.stack()[1:]
        # Use Callers of Callables
        caller = next((e for e in stack if not e.function == '__call__'), None)

        # TODO: KWARGS?
        new_args = []
        i = 0
        for (arg, checker) in zip(args, self.argument_checker):
            res = checker.check_and_wrap(arg, TypedCallableArgumentExecutionContext(self, caller, i))
            new_args.append(res)
            i += 1

        ret = self.inner(*new_args, **kwargs)
        ret = self.return_checker.check_and_wrap(ret, TypedCallableReturnExecutionContext(self.ctx, self))
        return ret


class TypedCallableReturnExecutionContext(ExecutionContext):
    upper: ExecutionContext
    fn: TypedCallable

    def __init__(self, upper: ExecutionContext, fn: TypedCallable):
        self.upper = upper
        self.fn = fn

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        (next_ty, indicator) = err.next_type_and_indicator()

        desc = lambda s: s.describe()
        front_str = f"Callable[[{', '.join(map(desc, self.fn.argument_checker))}], "

        # TODO: what if inside is TypedFunction?
        err = err.with_frame(Frame(
            f"{front_str}{next_ty}]",
            (" " * len(front_str)) + indicator,

            file=inspect.getfile(self.fn.inner),
            line_no=inspect.getsourcelines(self.fn.inner)[1],
            source_line="\n".join(inspect.getsourcelines(self.fn.inner)[0]),
        ))

        return self.upper.wrap(err)


class TypedCallableArgumentExecutionContext(ExecutionContext):
    fn: TypedCallable
    stack: inspect.FrameInfo
    argument_num: int

    def __init__(self, fn: TypedCallable, stack: inspect.FrameInfo, argument_num: int):
        self.fn = fn
        self.stack = stack
        self.argument_num = argument_num

    def declared_and_indicator(self, err: UntypyTypeError) -> Tuple[str, str]:
        (next_ty, indicator) = err.next_type_and_indicator()
        front_types = []
        back_types = []
        for n, ch in enumerate(self.fn.argument_checker):
            if n < self.argument_num:
                front_types.append(ch.describe())
            elif n > self.argument_num:
                back_types.append(ch.describe())

        l = len(f"Callable[[{', '.join(front_types)}")
        if len(front_types) > 0:
            l += len(', ')

        return f"Callable[[{', '.join(front_types + [next_ty] + back_types)}], {self.fn.return_checker.describe()}]", \
               (" " * l) + indicator

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        (type_declared, indicator_line) = self.declared_and_indicator(err)
        frame = Frame(
            type_declared,
            indicator_line,

            file=self.stack.filename,
            line_no=self.stack.lineno,
            source_line=self.stack.code_context[0]
        )
        return err.with_frame(frame)
