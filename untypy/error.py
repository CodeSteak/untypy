from __future__ import annotations

import inspect
from enum import Enum
from typing import Any, Optional, Tuple


class Location:
    file: str
    line_no: int
    source_line: str

    def __init__(self, file: str, line_no: int, source_line: str):
        self.file = file
        self.line_no = line_no
        self.source_line = source_line

    def __str__(self):
        buf = f"{self.file}:{self.line_no}"
        if self.source_line:
            for i, line in enumerate(self.source_line.splitlines()):
                if i < 5:
                    buf += f"\n{'{:3}'.format(self.line_no + i)} | {line}"
            if i >= 5:
                buf += "    | ..."
        return buf

    def __repr__(self):
        return f"Location(file={self.file.__repr__()}, line_no={self.line_no.__repr__()}, source_line={repr(self.source_line)})"

    def __eq__(self, other):
        if not isinstance(other, Location):
            return False
        return self.file == other.file and self.line_no == other.line_no

    @staticmethod
    def from_code(obj) -> Location:
        try:
            return Location(
                file=inspect.getfile(obj),
                line_no=inspect.getsourcelines(obj)[1],
                source_line="".join(inspect.getsourcelines(obj)[0]),
            )
        except Exception:
            return Location(
                file=inspect.getfile(obj),
                line_no=1,
                source_line=repr(obj)
            )

    @staticmethod
    def from_stack(stack) -> Location:
        if isinstance(stack, inspect.FrameInfo):
            try:
                return Location(
                    file=stack.filename,
                    line_no=stack.lineno,
                    source_line=stack.code_context[0]
                )
            except Exception:
                return Location(
                    file=stack.filename,
                    line_no=stack.lineno,
                    source_line=None
                )
        else:  # assume sys._getframe(...)
            try:
                source_line = inspect.findsource(stack.f_code)[0][stack.f_lineno - 1]
                return Location(
                    file=stack.f_code.co_filename,
                    line_no=stack.f_lineno,
                    source_line=source_line
                )
            except Exception:
                return Location(
                    file=stack.f_code.co_filename,
                    line_no=stack.f_lineno,
                    source_line=None
                )


class Frame:
    type_declared: str
    indicator_line: str

    declared: Optional[Location]
    responsable: Optional[Location]

    responsibility_type: Optional[ResponsibilityType]

    def __init__(self, type_declared: str, indicator_line: Optional[str],
                 declared: Optional[Location], responsable: Optional[Location]):

        self.type_declared = type_declared
        if indicator_line is None:
            indicator_line = '^' * len(type_declared)
        self.indicator_line = indicator_line
        self.declared = declared
        self.responsable = responsable

    def __str__(self):
        buf = f"in: {self.type_declared}\n" \
              f"    {self.indicator_line}\n"

        if self.responsable is not None:
            buf += f"{self.responsable.file}:{self.responsable.line_no}:\n" \
                   f"{self.responsable.source_line}\n" \
                   f"\n"
        return buf


class ResponsibilityType(Enum):
    IN = 0
    OUT = 1

    def invert(self):
        if self is ResponsibilityType.IN:
            return ResponsibilityType.OUT
        else:
            return ResponsibilityType.IN

def join_lines(l: list[str]) -> str:
    return '\n'.join([x.rstrip() for x in l])

class UntypyTypeError(TypeError):
    given: Any
    expected: str
    frames: list[Frame]
    notes: list[str]
    previous_chain: Optional[UntypyTypeError]
    responsibility_type: ResponsibilityType

    def __init__(self, given: Any, expected: str, frames: list[Frame] = [],
                 notes: list[str] = [],
                 previous_chain: Optional[UntypyTypeError] = None,
                 responsibility_type: ResponsibilityType = ResponsibilityType.IN):
        self.responsibility_type = responsibility_type
        self.given = given
        self.expected = expected
        self.frames = frames.copy()
        for frame in self.frames:
            if frame.responsibility_type is None:
                frame.responsibility_type = responsibility_type
        self.notes = notes.copy()
        self.previous_chain = previous_chain
        super().__init__('\n' + self.__str__())

    def next_type_and_indicator(self) -> Tuple[str, str]:
        if len(self.frames) >= 1:
            frame = self.frames[-1]
            return frame.type_declared, frame.indicator_line
        else:
            return self.expected, "^" * len(self.expected)

    def with_frame(self, frame: Frame) -> UntypyTypeError:
        frame.responsibility_type = self.responsibility_type
        return UntypyTypeError(self.given, self.expected, self.frames + [frame],
                               self.notes, self.previous_chain, self.responsibility_type)

    def with_previous_chain(self, previous_chain: UntypyTypeError):
        return UntypyTypeError(self.given, self.expected, self.frames,
                               self.notes, previous_chain, self.responsibility_type)

    def with_note(self, note: str):
        return UntypyTypeError(self.given, self.expected, self.frames,
                               self.notes + [note], self.previous_chain, self.responsibility_type)

    def with_inverted_responsibility_type(self):
        return UntypyTypeError(self.given, self.expected, self.frames,
                               self.notes, self.previous_chain, self.responsibility_type.invert())

    def last_responsable(self):
        for f in reversed(self.frames):
            if f.responsable is not None and f.responsibility_type is ResponsibilityType.IN:
                return f.responsable
        return None

    def last_declared(self):
        for f in reversed(self.frames):
            if f.declared is not None:
                return f.declared
        return None

    def __str__(self):
        declared_locs = []
        responsable_locs = []

        for f in self.frames:
            if f.responsable is not None and f.responsibility_type is ResponsibilityType.IN and str(
                    f.responsable) not in responsable_locs:
                responsable_locs.append(str(f.responsable))
            if f.declared is not None and str(f.declared) not in declared_locs:
                declared_locs.append(str(f.declared))

        cause = join_lines(responsable_locs)
        declared = join_lines(declared_locs)

        (ty, ind) = self.next_type_and_indicator()

        notes = join_lines(self.notes)
        if notes:
            notes = notes + "\n\n"

        if self.previous_chain is None:
            previous_chain = ""
        else:
            previous_chain = self.previous_chain.__str__()
        if previous_chain:
            previous_chain = previous_chain + "\n\n"

        inside = ""
        if self.expected != ty:
            inside = f"by function {ty.rstrip()}\n" \
                     f"            {ind.rstrip()}"

        given = repr(self.given)
        expected = self.expected.strip()
        if expected != 'None':
            expected = f'value of type {expected}'
        return (f"""{previous_chain}{notes}given:    {given.rstrip()}
expected: {expected}

{inside}
declared at: {declared}

caused by: {cause}""")


class UntypyAttributeError(AttributeError):

    def __init__(self, message: str, locations: list[Location] = []):
        self.message = message
        self.locations = locations.copy()

        super().__init__(self.__str__())

    def with_location(self, loc: Location) -> UntypyAttributeError:
        return UntypyAttributeError(self.message, self.locations + [loc])

    def __str__(self):
        locations = '\n'.join(map(str, self.locations))
        return f"{self.message}\n{locations}"
