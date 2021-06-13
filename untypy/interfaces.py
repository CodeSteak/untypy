from __future__ import annotations

import inspect
from typing import Optional, Any, Callable, TypeVar, List

from untypy.error import UntypyTypeError, Location, UntypyAttributeError


class CreationContext:
    def find_checker(self, annotation: Any) -> Optional[TypeChecker]:
        raise NotImplementedError

    def declared_location(self) -> Location:
        raise NotImplementedError

    def wrap(self, err: UntypyAttributeError) -> UntypyAttributeError:
        raise NotImplementedError

    def resolve_typevar(self, var: TypeVar) -> (bool, Any):
        raise NotImplementedError

    def all_typevars(self) -> List[TypeVar]:
        raise NotImplementedError

    def with_typevars(self, typevars: dict[TypeVar, Any]) -> CreationContext:
        raise NotImplementedError

    def should_be_type_checked(self, annotation: type) -> bool:
        raise NotImplementedError


class ExecutionContext:
    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        raise NotImplementedError


class TypeChecker:

    def describe(self) -> str:
        raise NotImplementedError

    def may_be_wrapped(self) -> bool:
        return False

    def base_type(self) -> list[Any]:
        raise NotImplementedError

    # Higher Priority => checked first inside Union.
    def base_type_priority(self) -> int:
        return 0

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        raise NotImplementedError


class TypeCheckerFactory:

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        raise NotImplementedError


WrappedFunctionContextProvider = Callable[[str], ExecutionContext]


class WrappedFunction:
    def get_original(self):
        raise NotImplementedError

    def wrap_arguments(self, ctxprv: WrappedFunctionContextProvider, args, kwargs):
        raise NotImplementedError

    def wrap_return(self, ret, ctx: ExecutionContext):
        raise NotImplementedError

    def describe(self) -> str:
        raise NotImplementedError

    def checker_for(self, name: str) -> TypeChecker:
        raise NotImplementedError

    @staticmethod
    def find_original(fn):
        if isinstance(fn, WrappedFunction):
            return WrappedFunction.find_original(fn.get_original())
        elif hasattr(fn, '__wf'):
            return WrappedFunction.find_original(getattr(fn, '__wf').get_original())
        else:
            return fn

    @staticmethod
    def find_location(fn) -> Location:
        fn = WrappedFunction.find_original(fn)
        return Location(
            file=inspect.getfile(fn),
            line_no=inspect.getsourcelines(fn)[1],
            source_line="".join(inspect.getsourcelines(fn)[0]),
        )
