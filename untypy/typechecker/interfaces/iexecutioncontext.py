from __future__ import annotations

from typing import Callable

__all__ = ['IExecutionContext']


class IExecutionContext:
    def blame(self, param):
        raise NotImplementedError
    
    def rescope(self, fun: Callable, argument=None) -> IExecutionContext:
        raise NotImplementedError
