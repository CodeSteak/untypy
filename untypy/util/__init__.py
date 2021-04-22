from untypy.error import UntypyTypeError, Frame
from untypy.interfaces import ExecutionContext, TypeChecker


class CompoundTypeExecutionContext(ExecutionContext):
    upper: ExecutionContext
    checkers: list[TypeChecker]
    idx: int

    def __init__(self, upper: ExecutionContext, checkers: list[TypeChecker], idx: int):
        self.upper = upper
        self.checkers = checkers
        self.idx = idx

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

        return err.with_frame(Frame(
            type_declared,
            indicator,
            None,
            None,
            None
        ))


class DummyExecutionContext(ExecutionContext):
    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        return err
