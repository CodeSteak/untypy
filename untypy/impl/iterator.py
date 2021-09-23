import collections.abc
import inspect
from collections import Iterator
from typing import Any, Optional
from typing import Iterator as OtherIterator

from untypy.error import UntypyTypeError, UntypyAttributeError, Location
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from untypy.util import CompoundTypeExecutionContext

IteratorTypeA = type(Iterator[int])
IteratorTypeB = type(OtherIterator[int])


class IteratorFactory(TypeCheckerFactory):
    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if type(annotation) in [IteratorTypeA, IteratorTypeB] and annotation.__origin__ == collections.abc.Iterator:
            if len(annotation.__args__) != 1:
                raise ctx.wrap(UntypyAttributeError(f"Expected 1 type arguments for iterator."))

            inner = ctx.find_checker(annotation.__args__[0])
            if inner is None:
                raise ctx.wrap(UntypyAttributeError(f"The inner type of the iterator could not be resolved."))
            return IteratorChecker(inner)
        else:
            return None


class IteratorChecker(TypeChecker):
    inner: TypeChecker

    def __init__(self, inner: TypeChecker):
        self.inner = inner

    def may_be_wrapped(self) -> bool:
        return True

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if not hasattr(arg, '__next__') or not hasattr(arg, '__iter__'):
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))

        me = self
        ctx = TypedIteratorExecutionContext(self.inner, arg, ctx)

        def wrapper():
            for item in arg:
                yield me.inner.check_and_wrap(item, ctx)

        return wrapper()

    def describe(self) -> str:
        return f"Iterator[{self.inner.describe()}]"

    def base_type(self) -> list[Any]:
        return [IteratorTypeA]


class TypedIteratorExecutionContext(CompoundTypeExecutionContext):
    iter: Iterator[Any]

    def __init__(self, inner: TypeChecker, iter: Iterator[Any], upper: ExecutionContext):
        self.iter = iter
        super().__init__(upper, [inner], 0)

    def name(self) -> str:
        return "Iterator"

    def responsable(self) -> Optional[Location]:
        try:
            if hasattr(self.iter, 'gi_frame'):
                return Location(
                    file=inspect.getfile(self.iter.gi_frame),
                    line_no=inspect.getsourcelines(self.iter.gi_frame)[1],
                    source_line="\n".join(inspect.getsourcelines(self.iter.gi_frame)[0]),
                )
        except OSError:  # this call does not work all the time
            pass
        except TypeError:
            pass
        return None
