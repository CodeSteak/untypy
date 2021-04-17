from __future__ import annotations

from typing import Optional, Any, Union

from untypy.error import Frame, UntypyTypeError


class CreationContext:
    def find_checker(self, annotation: Any) -> Optional[TypeChecker]:
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

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        raise NotImplementedError


class TypeCheckerFactory:

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        raise NotImplementedError
