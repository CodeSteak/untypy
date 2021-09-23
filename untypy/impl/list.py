import inspect
import sys
from types import GenericAlias
from typing import Any, Optional, List

from untypy.error import UntypyTypeError, Frame, Location
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext


class ListFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if (type(annotation) is GenericAlias and annotation.__origin__ == list) or (
                type(annotation) is type(List[int]) and annotation.__origin__ == list):
            assert len(annotation.__args__) == 1
            inner = ctx.find_checker(annotation.__args__[0])
            if inner is None:
                return None
            return ListChecker(inner, ctx.declared_location())
        else:
            return None


class ListChecker(TypeChecker):
    inner: TypeChecker
    declared: Location

    def __init__(self, inner: TypeChecker, declared: Location):
        self.inner = inner
        self.declared = declared

    def may_change_identity(self) -> bool:
        return True

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if not issubclass(type(arg), list):
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))

        return TypedList(arg, self.inner, ListExecutionContext(ctx), self.declared)

    def base_type(self) -> list[Any]:
        return [list]

    def describe(self) -> str:
        return f"list[{self.inner.describe()}]"


class ListExecutionContext(ExecutionContext):
    upper: ExecutionContext

    def __init__(self, upper: ExecutionContext):
        self.upper = upper

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        next_type, indicator = err.next_type_and_indicator()

        err = err.with_frame(Frame(
            f"list[{next_type}]",
            (" " * len("list[") + indicator),
            None,
            None
        ))
        return self.upper.wrap(err)


class ListCallerExecutionContext(ExecutionContext):
    stack: inspect.FrameInfo
    declared: Location

    def __init__(self, stack: inspect.FrameInfo, declared: Location):
        self.stack = stack
        self.declared = declared

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        next_type, indicator = err.next_type_and_indicator()
        return err.with_frame(Frame(
            f"list[{next_type}]",
            (" " * len("list[") + indicator),
            declared=self.declared,
            responsable=Location.from_stack(self.stack)
        ))


class TypedList(list):
    inner: list
    checker: TypeChecker
    ctx: ExecutionContext
    declared: Location

    def __init__(self, lst, checker, ctx, declared):
        super().__init__()
        self.checker = checker
        self.inner = lst
        self.ctx = ctx
        self.declared = declared

    # Perform type check
    def __getitem__(self, index):
        if type(index) is int:
            # list[1], flat get
            ret = self.inner.__getitem__(index)
            return self.checker.check_and_wrap(ret, self.ctx)
        else:
            # returned structure is an list itself.
            # e.g. list[1:3, ...]
            return list(map(lambda x: self.checker.check_and_wrap(x, self.ctx), self.inner.__getitem__(index)))

    def __iter__(self):
        return TypedListIterator(self)

    def append(self, x) -> None:
        caller = sys._getframe(1)
        ctx = ListCallerExecutionContext(caller, self.declared)
        self.inner.append(self.checker.check_and_wrap(x, ctx))

    def extend(self, iterable) -> None:
        caller = sys._getframe(1)
        ctx = ListCallerExecutionContext(caller, self.declared)
        return self.inner.extend(list(map(lambda x: self.checker.check_and_wrap(x, ctx), iterable)))

    def insert(self, index, obj) -> None:
        caller = sys._getframe(1)
        ctx = ListCallerExecutionContext(caller, self.declared)
        return self.inner.insert(index, self.checker.check_and_wrap(obj, ctx))

    # l += [...]
    def __iadd__(self, other):
        caller = sys._getframe(1)
        ctx = ListCallerExecutionContext(caller, self.declared)
        self.inner.extend(list(map(lambda x: self.checker.check_and_wrap(x, ctx), other)))
        return self

    # l[i] = x
    # l[i:j] = [...]
    def __setitem__(self, idx, value):
        caller = sys._getframe(1)
        ctx = ListCallerExecutionContext(caller, self.declared)
        if isinstance(idx, slice):
            self.inner.__setitem__(idx, list(map(lambda x: self.checker.check_and_wrap(x, ctx), value)))
        else:
            return self.inner.__setitem__(idx, self.checker.check_and_wrap(value, ctx))

    # l + ...
    def __add__(self, other):
        # Caller Context
        return self.inner + other

    # ... + l
    def __radd__(self, other):
        return other + self.inner

    def pop(self, *args, **kwargs):
        ret = self.inner.pop(*args, **kwargs)
        return ret

    # Delete, Copy, ...
    def index(self, *args, **kwargs):
        return self.inner.index(*args, **kwargs)

    def clear(self, *args, **kwargs):
        return self.inner.clear(*args, **kwargs)

    def copy(self, *args, **kwargs):
        return self.inner.copy(*args, **kwargs)

    def count(self, *args, **kwargs):
        return self.inner.count(*args, **kwargs)

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

    def __str__(self):
        return self.inner.__str__()

    def __copy__(self):
        return self.inner.copy()


class TypedListIterator:
    inner: TypedList
    index: int

    def __init__(self, inner):
        super().__init__()
        self.inner = inner
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= len(self.inner):
            raise StopIteration

        ret = self.inner[self.index]
        self.index += 1
        return ret
