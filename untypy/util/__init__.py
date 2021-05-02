from typing import Optional

from untypy.error import UntypyTypeError, Frame, Location
from untypy.interfaces import ExecutionContext, TypeChecker


class CompoundTypeExecutionContext(ExecutionContext):
    upper: ExecutionContext
    checkers: list[TypeChecker]
    idx: int

    def __init__(self, upper: ExecutionContext, checkers: list[TypeChecker], idx: int):
        self.upper = upper
        self.checkers = checkers
        self.idx = idx

    def declared(self) -> Optional[Location]:
        return None

    def responsable(self) -> Optional[Location]:
        return None

    def name(self) -> str:
        raise NotImplementedError

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        type_declared = self.name()+"["
        indicator = " " * len(type_declared)

        for i, checker in enumerate(self.checkers):
            if i == self.idx:
                next_type, next_indicator = err.next_type_and_indicator()
                type_declared += next_type
                indicator += next_indicator
            else:
                type_declared += checker.describe()
                indicator += " " * len(checker.describe())

            if i != len(self.checkers) - 1:  # not last element
                type_declared += ", "
                indicator += "  "

        type_declared += "]"

        err = err.with_frame(Frame(
            type_declared,
            indicator,
            declared=self.declared(),
            responsable=self.responsable(),
        ))

        return self.upper.wrap(err)


class NoResponsabilityWrapper(ExecutionContext):
    upper: ExecutionContext

    def __init__(self, upper: ExecutionContext):
        self.upper = upper

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        full = self.upper.wrap(err)

        # now remove responsability in frames:
        frames_to_add = []
        for frame in full.frames:
            if frame not in err.frames:
                frame.responsable = None
                frames_to_add.append(frame)

        for frame in frames_to_add:
            err = err.with_frame(frame)

        return err