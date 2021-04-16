import inspect
from types import GenericAlias
from untypy.error import UntypyTypeError, Frame
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from typing import Any, Optional, Union


class ListFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if type(annotation) is GenericAlias and annotation.__origin__ == list:
            assert len(annotation.__args__) == 1
            inner = ctx.find_checker(annotation.__args__[0])
            if inner is None:
                return None
            return ListChecker(inner)
        else:
            return None


class ListChecker(TypeChecker):
    inner: TypeChecker

    def __init__(self, inner: TypeChecker):
        self.inner = inner

    def may_change_identity(self) -> bool:
        return True

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if not issubclass(type(arg), list):
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))

        return TypedList(arg, self.inner, ctx)

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
                None,
                None
            ))
        return self.upper.wrap(err)


class ListCallerExecutionContext(ExecutionContext):
    stack: inspect.FrameInfo

    def __init__(self, stack: inspect.FrameInfo):
        self.stack = stack

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        next_type, indicator = err.next_type_and_indicator()
        return err.with_frame(Frame(
            f"list[{next_type}]",
            (" " * len("list[") + indicator),
            file=self.stack.filename,
            line_no=self.stack.lineno,
            source_line=self.stack.code_context[0]
        ))


class TypedList(list):
    inner: list
    checker: TypeChecker
    ctx: ExecutionContext

    def __init__(self, lst, checker, ctx):
        super().__init__()
        self.checker = checker
        self.inner = lst
        self.ctx = ctx

    # Perform type check
    def __getitem__(self, index):
        if type(index) is int:
            # list[1], flat get
            ret = self.inner.__getitem__(index)
            return self.checker.check_and_wrap(ret, self.ctx)
        else:
            # returned structure is an list itself.
            # e.g. list[1:3, ...]
            return list(map(lambda x: self.checker.check(x, self.ctx), self.inner.__getitem__(index)))

    def __iter__(self):
        return TypedListIterator(self)

    def append(self, x) -> None:
        # first is this fn
        stack = inspect.stack()[1:]
        # Use Callers of Callables
        caller = next((e for e in stack if not e.function == '__call__'), None)
        ctx = ListCallerExecutionContext(caller)
        self.inner.append(self.checker.check_and_wrap(x, ctx))

    def extend(self, iterable) -> None:
        # first is this fn
        stack = inspect.stack()[1:]
        # Use Callers of Callables
        caller = next((e for e in stack if not e.function == '__call__'), None)
        ctx = ListCallerExecutionContext(caller)
        return self.inner.extend(list(map(lambda x: self.checker.check_and_wrap(x, ctx), iterable)))

    def insert(self, index, obj) -> None:
        # first is this fn
        stack = inspect.stack()[1:]
        # Use Callers of Callables
        caller = next((e for e in stack if not e.function == '__call__'), None)
        ctx = ListCallerExecutionContext(caller)

        return self.inner.insert(index, self.checker.check_and_wrap(obj, ctx))

    def __iadd__(self, other):
        # first is this fn
        stack = inspect.stack()[1:]
        # Use Callers of Callables
        caller = next((e for e in stack if not e.function == '__call__'), None)
        ctx = ListCallerExecutionContext(caller)

        self.inner.extend(list(map(lambda x: self.checker.check_and_wrap(x, ctx), other)))
        return self

    def __setitem__(self, idx, value):
        # first is this fn
        stack = inspect.stack()[1:]
        # Use Callers of Callables
        caller = next((e for e in stack if not e.function == '__call__'), None)
        ctx = ListCallerExecutionContext(caller)

        return self.inner.__setitem__(idx, self.checker.check_and_wrap(value, ctx))

    def __add__(self, *args, **kwargs):
        # Caller Context
        return self.inner.__add__(*args, **kwargs)

    def pop(self, *args, **kwargs):
        ret = self.inner.pop(*args, **kwargs)
        return self.checker.check_and_wrap(ret, self.ctx)

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


class TypedListIterator:
    inner: TypedList
    index: int

    def __init__(self, inner):
        super().__init__()
        self.inner = inner
        self.index = 0

    def __next__(self):
        if self.index >= len(self.inner):
            raise StopIteration

        ret = self.inner[self.index]
        self.index += 1
        return ret
