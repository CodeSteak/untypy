__all__ = ['ITypeChecker', 'ITypeContext', 'GlobalTypeManager']

from .impl_typechecker import *
from .itypechecker import ITypeChecker
from .itypecontext import ITypeContext
from .itypemanager import ITypeManager


class EmptyITypeChecker(ITypeChecker):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    def create_from(ty, ctx: ITypeContext):
        EmptyITypeChecker(ctx)

    def check(self, this, arg):
        # TODO
        print("WARING: NO TYPE DEF")
        return arg


class TypeManager(ITypeManager):
    def __init__(self, type_checker_list=[]):
        self.list = []
        self.register_all(type_checker_list)

    def register(self, type_checker):
        self.list.append(type_checker)

    def register_all(self, callback_list):
        for cb in callback_list:
            self.list.append(cb)

    def find(self, obj, ctx):
        for cb in self.list:
            res = cb.create_from(obj, ctx)
            if res is not None:
                return res
        return EmptyITypeChecker.create_from(obj, ctx)


GlobalTypeManager = TypeManager(all_typechecker_highest_priority_first())
