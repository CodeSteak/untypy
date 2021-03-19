import inspect
from collections.abc import Callable as AbcCallable
from typing import Any, Optional, Callable

from ..interfaces import *


class LambdaFactory(ITypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: ICreationContext) -> Optional[ITypeChecker]:
        # python is broken...
        # there are two callables and if evaluated neither of them has a 'public' type.
        # also they DO NOT inherit from GenericAlias
        if type(annotation) is type(Callable[[int], int]) or type(annotation) is type(AbcCallable[[int], int]):
            argument_ty = annotation.__args__[:-1]
            return_ty = annotation.__args__[-1]
            argument_ty = list(map(lambda arg: ctx.type_manager().find(arg, ctx), argument_ty))
            return_ty = ctx.type_manager().find(return_ty, ctx)
            return Checker(argument_ty, return_ty)
        else:
            return None


class Checker(ITypeChecker):
    argument_ty: list[ITypeChecker]
    return_ty: ITypeChecker

    def __init__(self, argument_ty, return_ty):
        self.argument_ty = argument_ty
        self.return_ty = return_ty

    def check(self, arg, ctx):
        if not issubclass(type(arg), Callable):
            ctx.blame(f"has class {type(arg)}, this class is does not implement of Callable.")
        return FunctionDecorator(arg, self.argument_ty, self.return_ty, ctx)


# TOdo rename, rethink
class FunctionDecorator(Callable):
    _fun: Callable
    _argument_check: list[ITypeChecker]
    _reti: ITypeChecker
    _ctx: IExecutionContext

    def __init__(self, fun: Callable, argument_check: list[ITypeChecker], reti: ITypeChecker, ctx: IExecutionContext):
        self._fun = fun
        self._argument_check = argument_check
        self._reti = reti
        self._ctx = ctx
        self.__wrapped__ = True

    def __call__(self, *args, **kwargs):
        # TODO: varargs, kw
        # TODO: Optimise?
        stack = inspect.stack()[1:]  # first is this fn
        caller = next((e for e in stack if not e.function == '__call__'), None)

        if len(args) != len(self._argument_check):
            self._ctx.blame(f"{len(args)} were given, but {len(self._argument_check)} expected in the type definition.")

        new_arg = []
        for (arg, checker) in zip(args, self._argument_check):
            new_arg.append(checker.check(arg, self._ctx.rescope(caller)))

        try:
            ret = self._fun(*new_arg, **kwargs)
        except TypeError as e:
            if e.in_return:  # TODO refactor
                raise e
            else:
                self._ctx.blame(f"the given function does not match signature.")

        return self._reti.check(ret, self._ctx.rescope(self._fun, None, True))
