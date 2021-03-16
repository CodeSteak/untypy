import inspect
from collections.abc import Callable as AbcCallable
from types import GenericAlias
from typing import Callable

from .itypechecker import ITypeChecker
from .itypecontext import ITypeContext

__all__ = ['all_typechecker_highest_priority_first']


class SimpleTypeChecker(ITypeChecker):
    def __init__(self, clas):
        super().__init__()
        self.clas = clas

    @staticmethod
    def create_from(ty, ctx: ITypeContext):
        if inspect.isclass(ty):
            return SimpleTypeChecker(ty)
        else:
            return None

    def check(self, this, arg, ctx):
        if issubclass(type(arg), self.clas):
            return arg
        else:
            ctx.fail(f"has class {type(arg)}, this class is not a subclass of {self.clas}.")


class ListTypeChecker(ITypeChecker):
    inner: ITypeChecker

    def __init__(self, inner):
        super().__init__()
        self.inner = inner

    @staticmethod
    def create_from(ty, ctx: ITypeContext):
        if type(ty) is GenericAlias and ty.__origin__ == list:
            if len(ty.__args__) != 1:
                ctx.fail("Can only check one generic argument in list type.")
            inner = ctx.type_manager().find(ty.__args__[0], ctx)
            # todo wrap ctx
            return ListTypeChecker(inner)
        else:
            return None

    def check(self, this, arg, ctx):
        if issubclass(type(arg), list):
            for elm in arg:
                self.inner.check(arg, elm, ctx)
                # TODO should lambda in list be supported?
            return arg
        else:
            ctx.fail(f"has class {type(arg)}, this class is not a subclass of list.")


class CallableTypeChecker(ITypeChecker):

    def __init__(self, argument_ty, return_ty):
        super().__init__()
        self.argument_ty = argument_ty
        self.return_ty = return_ty

    @staticmethod
    def create_from(ty, ctx: ITypeContext):
        # python is broken...
        if type(ty) is type(AbcCallable[[int], int]) or type(ty) is type(Callable[[int], int]):
            argument_ty = ty.__args__[:-1]
            return_ty = ty.__args__[-1]

            argument_ty = map(lambda arg: ctx.type_manager().find(arg, ctx), argument_ty)
            return_ty = ctx.type_manager().find(return_ty, ctx)
            # todo wrap ctx
            return CallableTypeChecker(argument_ty, return_ty)
        else:
            return None

    def check(self, this, arg, ctx):
        if not issubclass(type(arg), Callable):
            ctx.fail(f"has class {type(arg)}, this class is not a subclass of Callable.")
        return FunctionDecoratorForLambdaAsArgument(ctx.wrap_function(arg), self.argument_ty, self.return_ty,
                                                    ctx.rescope(arg))


# TOdo rename, rethink
class FunctionDecoratorForLambdaAsArgument(Callable):
    fun: Callable
    arguments: list[ITypeChecker]
    reti: ITypeChecker
    ctx: ITypeContext

    def __init__(self, fun: Callable, arguments: list[ITypeChecker], reti: ITypeChecker, ctx: ITypeContext):
        self.fun = fun
        self.arguments = arguments
        self.reti = reti
        self.ctx = ctx

    def __call__(self, *args, **kwargs):
        if len(args) != len(self.arguments):
            self.ctx.fail(f"{len(args)} were given, but {len(self.arguments)} expected in the type definition.")

        new_arg = []
        for (arg, checker) in zip(args, self.arguments):
            new_arg.append(checker.check(None, arg, self.ctx))

        ret = self.fun(*new_arg, **kwargs)
        return self.reti.check(None, ret, self.ctx)


###################################################

def all_typechecker_highest_priority_first():
    return [
        CallableTypeChecker,
        ListTypeChecker,
        SimpleTypeChecker
    ]
