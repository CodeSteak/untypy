from .itypecontext import ITypeContext


class ITypeChecker:
    @staticmethod
    def create_from(ty, ctx: ITypeContext):
        """
        Try to create instance of this object

        :param ty: The Object that was given to the signature
        :param ctx: Context for raising exceptions
        :return:
        """
        raise Exception("This is an interface")

    def check(self, this, arg, ctx: ITypeContext):
        """
        Performs type checking and wrapping.

        :param ctx: context to raise exceptions
        :param this: instance that this is checked on
        :param arg: the argument to check
        :return:
        """
        raise Exception("This is an interface")
