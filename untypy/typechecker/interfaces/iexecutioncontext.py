from __future__ import annotations

from typing import Callable, Optional

__all__ = ['IExecutionContext']

from untypy.error import UntypyError


class IExecutionContext:
    def blame(self, info: str, typ: Optional[type] = None):
        raise NotImplementedError

    def blame_with_previous(self, e: UntypyError, info: Optional[str] = None, typ: Optional[type] = None):
        raise NotImplementedError

    def rescope(self, fun: Callable, argument=None, in_return=None) -> IExecutionContext:
        raise NotImplementedError
