from .iexecutioncontext import IExecutionContext

__all__ = ['ITypeChecker']


class ITypeChecker:
    def check(self, arg, ctx: IExecutionContext):
        """
        Performs type checking and wrapping.

        :param ctx: context to raise exceptions
        :param arg: the argument to check
        :return:
        """
        raise NotImplementedError
