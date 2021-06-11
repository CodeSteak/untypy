import inspect
import types
from typing import Optional, Union, List

from untypy.display import IndicatorStr
from untypy.error import UntypyTypeError, Frame, Location
from untypy.interfaces import ExecutionContext, TypeChecker, WrappedFunction


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
        type_declared = self.name() + "["
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

        for note in full.notes:
            err = err.with_note(note)

        if full.previous_chain is not None:
            err = err.with_previous_chain(full.previous_chain)

        return err


class ReturnExecutionContext(ExecutionContext):
    fn: WrappedFunction

    def __init__(self, fn: WrappedFunction):
        self.fn = fn

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        (next_ty, indicator) = err.next_type_and_indicator()
        return_id = IndicatorStr(next_ty, indicator)

        original = WrappedFunction.find_original(self.fn)
        signature = inspect.signature(original)

        front_sig = []
        for name in signature.parameters:
            front_sig.append(f"{name}: {self.fn.checker_for(name).describe()}")
        front_sig = f"{original.__name__}(" + (", ".join(front_sig)) + ") -> "

        return_id = IndicatorStr(front_sig) + return_id

        declared = WrappedFunction.find_location(self.fn)
        return err.with_frame(Frame(
            return_id.ty,
            return_id.indicator,
            declared=declared,
            responsable=declared,
        ))


class ArgumentExecutionContext(ExecutionContext):
    n: WrappedFunction
    stack: inspect.FrameInfo
    argument_name: str

    def __init__(self, fn: Union[WrappedFunction, types.FunctionType], stack: Optional[inspect.FrameInfo],
                 argument_name: str):
        self.fn = fn
        self.stack = stack
        self.argument_name = argument_name

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        (next_ty, indicator) = err.next_type_and_indicator()
        error_id = IndicatorStr(next_ty, indicator)

        original = WrappedFunction.find_original(self.fn)
        signature = inspect.signature(original)

        wf = None
        if (hasattr(self.fn, '__wf')):
            wf = getattr(self.fn, '__wf')
        elif isinstance(self.fn, WrappedFunction):
            wf = self.fn

        arglist = []
        for name in signature.parameters:
            if name is self.argument_name:
                arglist.append(IndicatorStr(f"{name}: ") + error_id)
            else:
                if wf is not None:
                    arglist.append(IndicatorStr(f"{name}: {wf.checker_for(name).describe()}"))
                else:
                    arglist.append(IndicatorStr(f"{name}"))

        id = IndicatorStr(f"{original.__name__}(") + IndicatorStr(", ").join(arglist)

        if wf is not None:
            id += IndicatorStr(f") -> {wf.checker_for('return').describe()}")
        else:
            id += IndicatorStr(f")")

        declared = WrappedFunction.find_location(self.fn)
        if self.stack is not None:
            responsable = Location(
                file=self.stack.filename,
                line_no=self.stack.lineno,
                source_line=self.stack.code_context[0]
            )
        else:
            responsable = None

        frame = Frame(
            id.ty,
            id.indicator,
            declared=declared,
            responsable=responsable
        )
        return err.with_frame(frame)


class GenericExecutionContext(ExecutionContext):
    def __init__(self, *, declared: Union[None, Location, List[Location]] = None,
                 responsable: Union[None, Location, List[Location]] = None,
                 upper_ctx: Optional[ExecutionContext] = None):
        self.declared = declared
        self.responsable = responsable
        self.upper_ctx = upper_ctx

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        declared = []
        if isinstance(self.declared, Location):
            declared.append(self.declared)
        if isinstance(self.declared, list):
            declared.extend(self.declared)

        responsable = []
        if isinstance(self.responsable, Location):
            responsable.append(self.responsable)
        if isinstance(self.responsable, list):
            responsable.extend(self.responsable)

        while len(declared) < len(responsable): declared.append(None)
        while len(declared) > len(responsable): responsable.append(None)

        for (d, r) in zip(declared, responsable):
            (t, i) = err.next_type_and_indicator()
            err = err.with_frame(Frame(t, i, d, r))

        if self.upper_ctx is not None:
            return self.upper_ctx.wrap(err)
        else:
            return err
