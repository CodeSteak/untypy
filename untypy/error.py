from __future__ import annotations

import inspect
from typing import Optional, Any

__all__ = ['UntypyFrame', 'UntypyError']

class UntypyFrame:
    info: Optional[str]
    typ: Optional[type]
    callsite: Optional[Any]
    argument_name: str

    def __init__(self, info=None, typ=None, callsite=None, argument_name=None):
        self.info = info
        self.type = typ
        self.callsite = callsite
        self.argument_name = argument_name

    def __repr__(self) -> str:
        msg = ""
        if isinstance(self.callsite, inspect.FrameInfo):
            msg += f"{self.callsite.filename[-20:]}:{self.callsite.lineno} >> {self.callsite.code_context[0].strip()}\n\n"
        elif inspect.isfunction(self.callsite):
            msg += f">> {inspect.getsource(self.callsite)}\n\n"
        else:
            msg += f">> {self.callsite}\n\n"
        if self.argument_name == 'return':
            msg += "in return value\n"
        else:
            msg += f"in argument {self.argument_name}\n"

        if self.info is not None:
            msg += f"\t {self.info}"
        return msg

    def single_line_code_representation(self) -> str:
        responsable_line = None
        if isinstance(self.callsite, inspect.FrameInfo):
            responsable_line = self.callsite.code_context[0].strip()
        elif inspect.isfunction(self.callsite):
            responsable_line = inspect.getsource(self.callsite).split('\n')[0].strip()

        return responsable_line


class UntypyError(TypeError):
    frames: list[UntypyFrame]

    def __init__(self, frames: list[UntypyFrame]):
        super().__init__("TypeError: \n" + str(frames))
        self.frames = frames

    def with_frame(self, frame: UntypyFrame) -> UntypyError:
        return UntypyError(self.frames + [frame])

    def single_line_code_representation(self):
        return self.frames[0].single_line_code_representation()

    def was_in_return(self) -> bool:
        return self.frames[0].argument_name == 'return'
