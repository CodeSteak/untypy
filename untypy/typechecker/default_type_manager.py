from .interfaces import *

__all__ = ['DefaultTypeManager']


class DefaultTypeManager(ITypeManager):
    factory_list: list[ITypeCheckerFactory]

    def __init__(self, factory_list=None):
        if factory_list is None:
            factory_list = []
        self.factory_list = factory_list.copy()

    def find(self, obj, ctx):
        for fac in self.factory_list:
            res = fac.create_from(obj, ctx)
            if res is not None:
                return res
        return None
