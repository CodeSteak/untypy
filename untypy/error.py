from __future__ import annotations

import inspect
from typing import Any, Optional, Tuple


class Frame:
    type_declared: str
    indicator_line: str

    file: Optional[str]
    line_no: Optional[int]
    source_line: Optional[str]

    def __init__(self, type_declared: str, indicator_line: str, file: Optional[str], line_no: Optional[int],
                 source_line: Optional[str]):
        self.type_declared = type_declared
        self.indicator_line = indicator_line
        self.file = file
        self.line_no = line_no
        self.source_line = source_line

    def __str__(self):
        buf = f"in: {self.type_declared}\n" \
              f"    {self.indicator_line}\n"

        if self.file is not None and self.line_no is not None and self.source_line is not None:
            buf += f"{self.file}:{self.line_no}:\n" \
                   f"{self.source_line}\n" \
                   f"\n"
        return buf


class UntypyTypeError(TypeError):
    given: Any
    expected: str
    expected_indicator: str
    frames: list[Frame]

    def __init__(self, given: Any, expected: str, expected_indicator: Optional[str] = None, frames: list[Frame] = []):
        super().__init__(f"given: {given}\n"
                         f"expected: {expected}\n\n" +
                         ('\n'.join(map(str, frames))))
        self.given = given
        self.expected = expected
        if expected_indicator is None:
            expected_indicator = "^" * len(expected)

        self.expected_indicator = expected_indicator
        self.frames = frames.copy()

    def next_type_and_indicator(self) -> Tuple[str, str]:
        if len(self.frames) >= 1:
            frame = self.frames[-1]
            return frame.type_declared, frame.indicator_line
        else:
            return self.expected, "^" * len(self.expected)

    def with_frame(self, frame: Frame) -> UntypyTypeError:
        return UntypyTypeError(self.given, self.expected, self.expected_indicator, self.frames + [frame])

    def __str__(self):
        return f"given: {self.given}\n" \
               f"expected: {self.expected}\n\n" + \
               ('\n'.join(map(str, self.frames)))


class UntypyAttributeError(AttributeError):
    pass

# given: 43
# but expected: str
# in the contract of foo (file.py, line 2)
#
# def foo(i: int, fun: Callable[[int], str]) -> List[str]:
#                                      ^^^
#
# The contract violation was triggered by the code calling foo (file.py, line 6)
# print(’Not OK: ’ + str(foo(42, inc)))
#                                ^^^
#
#
# /////////////////////////////////////////////////
# given: 42
# but expected: str
#
# in the contract of foo (file.py, line 2)
#
# def bar(xx : int) -> Callable[[int], str]
#                                      ^^^
# caused by (file.py, line 2)
#
# return lambda x: x
#        ^^^^^^^^^^^
#
# The contract violation was triggered by the code calling foo (file.py, line 6)
#     <Stacktrace>
