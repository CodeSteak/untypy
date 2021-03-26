import inspect
from types import GenericAlias
from typing import Any, Optional

from ..interfaces import *
from ... import UntypyError


class ListFactory(ITypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: ICreationContext) -> Optional[ITypeChecker]:
        if type(annotation) is GenericAlias and annotation.__origin__ == list:
            assert len(annotation.__args__) == 1
            inner = ctx.type_manager().find(annotation.__args__[0], ctx)
            return Checker(inner)


class Checker(ITypeChecker):
    inner: ITypeChecker

    def __init__(self, inner: ITypeChecker):
        super().__init__()
        self.inner = inner

    def check(self, arg, ctx):
        if issubclass(type(arg), list):
            return TypedList(arg, self.inner, ctx)
        else:
            ctx.blame(f"has class {type(arg)}, this class is not a subclass of list.", list)


class TypedList(list):
    inner : list
    checker : ITypeChecker
    ctx : IExecutionContext

    def __init__(self, lst, checker, ctx):
        super().__init__()
        self.checker = checker
        self.inner = lst
        self.ctx = ctx

    # Perform type check
    def __getitem__(self, index):
        try:
            if type(index) is int:
                # list[1], flat get
                ret = self.inner.__getitem__(index)
                return self.checker.check(ret, self.ctx)
            else:
                # returned structure is an list itself.
                # e.g. list[1:3, ...]
                return list(map(lambda x: self.checker.check(x, self.ctx), self.inner.__getitem__(index)))
        except UntypyError as e:
            self.ctx.blame_with_previous(e, 'inside list', list)

    def append(self, x) -> None:
        # Caller of append is responsable.

        stack = inspect.stack()[1:]  # first is this fn
        caller = next((e for e in stack if not e.function == '__call__'), None)

        self.inner.append(self.checker.check(x, self.ctx.rescope(caller, argument='item')))

    def extend(self, iterable) -> None:
        # Caller of this is responsable.

        stack = inspect.stack()[1:]  # first is this fn
        caller = next((e for e in stack if not e.function == '__call__'), None)

        return self.inner.extend(list(map(lambda x: self.checker.check(x, self.ctx.rescope(caller, argument='item')), iterable)))

    def insert(self, index, obj) -> None:

        stack = inspect.stack()[1:]  # first is this fn
        caller = next((e for e in stack if not e.function == '__call__'), None)

        return self.inner.insert(index, self.checker.check(obj.rescope(caller, argument='item'), self.ctx))

    def __iadd__(self, other):
        self.extend(other)
        return self

    def __setitem__(self, *args, **kwargs):
        return self.inner.__setitem__(*args, **kwargs)

    def __add__(self, *args, **kwargs):
        return self.inner.__add__(*args, **kwargs)

    # Delete, Copy, ...
    def index(self, *args, **kwargs):
        return self.inner.index(*args, **kwargs)

    def clear(self, *args, **kwargs):
        return self.inner.clear(*args, **kwargs)

    def copy(self, *args, **kwargs):
        return self.inner.copy(*args, **kwargs)

    def count(self, *args, **kwargs):
        return self.inner.count(*args, **kwargs)

    def pop(self, *args, **kwargs):
        return self.inner.pop(*args, **kwargs)

    def remove(self, *args, **kwargs):
        return self.inner.remove(*args, **kwargs)

    def reverse(self, *args, **kwargs):
        return self.inner.reverse(*args, **kwargs)

    def sort(self, *args, **kwargs):
        return self.inner.sort(*args, **kwargs)

    def __class_getitem__(self, *args, **kwargs):
        return self.inner.__class_getitem__(*args, **kwargs)

    def __contains__(self, *args, **kwargs):
        return self.inner.__contains__(*args, **kwargs)

    def __delitem__(self, *args, **kwargs):
        return self.inner.__delitem__(*args, **kwargs)

    def __eq__(self, *args, **kwargs):
        return self.inner.__eq__(*args, **kwargs)

    def __ge__(self, *args, **kwargs):
        return self.inner.__ge__(*args, **kwargs)

    def __gt__(self, *args, **kwargs):
        return self.inner.__gt__(*args, **kwargs)

    def __imul__(self, *args, **kwargs):
        return self.inner.__imul__(*args, **kwargs)

    def __len__(self, *args, **kwargs):
        return self.inner.__len__(*args, **kwargs)

    def __le__(self, *args, **kwargs):
        return self.inner.__le__(*args, **kwargs)

    def __lt__(self, *args, **kwargs):
        return self.inner.__lt__(*args, **kwargs)

    def __mul__(self, *args, **kwargs):
        return self.inner.__mul__(*args, **kwargs)

    def __ne__(self, *args, **kwargs):
        return self.inner.__ne__(*args, **kwargs)

    def __repr__(self, *args, **kwargs):
        return self.inner.__repr__(*args, **kwargs)

    def __reversed__(self, *args, **kwargs):
        return self.inner.__reversed__(*args, **kwargs)

    def __rmul__(self, *args, **kwargs):
        return self.inner.__rmul__(*args, **kwargs)


    def __sizeof__(self, *args, **kwargs):
        return self.inner.__sizeof__(*args, **kwargs)


