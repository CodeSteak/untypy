import inspect
from typing import Optional, Callable, Tuple

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


class WrappedFunction:

    def wrapped_original(self) -> Callable:
        raise NotImplementedError

    def wrapped_fullspec(self) -> inspect.FullArgSpec:
        raise NotImplementedError

    def wrapped_checker(self) -> dict[str, TypeChecker]:
        raise NotImplementedError


class ReturnExecutionContext(ExecutionContext):
    fn: WrappedFunction

    def __init__(self, fn: WrappedFunction):
        self.fn = fn

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        (next_ty, indicator) = err.next_type_and_indicator()

        arg_types = []
        for i, name in enumerate(self.fn.wrapped_fullspec().args):
            if name != 'return':
                arg_types.append(self.fn.wrapped_checker()[name].describe())

        front_str = f"def {self.fn.wrapped_original().__name__}({', '.join(arg_types)}) -> "

        declared = Location(
            file=inspect.getfile(self.fn.wrapped_original()),
            line_no=inspect.getsourcelines(self.fn.wrapped_original())[1],
            source_line="".join(inspect.getsourcelines(self.fn.wrapped_original())[0]),
        )

        return err.with_frame(Frame(
            front_str + next_ty,
            (" "*len(front_str)) + indicator,
            declared=declared,
            responsable=declared,
            ))


class ArgumentExecutionContext(ExecutionContext):
    fn: WrappedFunction
    stack: inspect.FrameInfo
    argument_name: str

    def __init__(self, fn: WrappedFunction, stack: Optional[inspect.FrameInfo], argument_name: str):
        self.fn = fn
        self.stack = stack
        self.argument_name = argument_name

    def declared_and_indicator(self, err: UntypyTypeError) -> Tuple[str, str]:
        (next_ty, indicator) = err.next_type_and_indicator()

        front_types = []
        back_types = []
        highlighted = None
        for i, name in enumerate(self.fn.wrapped_fullspec().args):
            if name != 'return':
                if name == self.argument_name:
                    highlighted = next_ty
                elif highlighted is None:
                    front_types.append(self.fn.wrapped_checker()[name].describe())
                else:
                    back_types.append(self.fn.wrapped_checker()[name].describe())

        l = len(f"def {self.fn.wrapped_original().__name__}({', '.join(front_types)}")
        if len(front_types) > 0:
            l += len(', ')

        return f"def {self.fn.wrapped_original().__name__}({', '.join(front_types + [highlighted] + back_types)}) -> " \
               f"  {self.fn.wrapped_checker()['return'].describe()}", (
                       " " * l) + indicator

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        (type_declared, indicator_line) = self.declared_and_indicator(err)

        declared = Location(
            file=inspect.getfile(self.fn.wrapped_original()),
            line_no=inspect.getsourcelines(self.fn.wrapped_original())[1],
            source_line="".join(inspect.getsourcelines(self.fn.wrapped_original())[0]),
        )

        if self.stack is not None:
            responsable = Location(
                file=self.stack.filename,
                line_no=self.stack.lineno,
                source_line=self.stack.code_context[0]
            )
        else:
            responsable = None

        frame = Frame(
            type_declared,
            indicator_line,
            declared=declared,
            responsable=responsable
        )
        return err.with_frame(frame)
