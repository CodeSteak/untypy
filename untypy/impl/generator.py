import inspect

from untypy.error import UntypyTypeError, UntypyAttributeError, Location, Frame
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from typing import Any, Optional, Union, Generator

from untypy.util import CompoundTypeExecutionContext, NoResponsabilityWrapper

GeneratorType = type(Generator[None, None, None])


class GeneratorFactory(TypeCheckerFactory):
    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if type(annotation) == GeneratorType:
            return GeneratorChecker(annotation, ctx)
        else:
            return None


class GeneratorChecker(TypeChecker):
    yield_checker: TypeChecker
    send_checker: TypeChecker
    return_checker: TypeChecker

    def __init__(self, annotation: GeneratorType, ctx: CreationContext):
        if len(annotation.__args__) != 3:
            raise UntypyAttributeError(f"Expected 3 type arguments for Generator.")

        (yield_checker, send_checker, return_checker) = list(map(lambda a: ctx.find_checker(a), annotation.__args__))

        if yield_checker is None:
            raise UntypyAttributeError(f"The Yield Annotation of the Generator could not be resolved.")
        if send_checker is None:
            raise UntypyAttributeError(f"The Send Annotation of the Generator could not be resolved.")
        if return_checker is None:
            raise UntypyAttributeError(f"The Return Annotation of the Generator could not be resolved.")

        self.yield_checker = yield_checker
        self.send_checker = send_checker
        self.return_checker = return_checker

    def may_be_wrapped(self) -> bool:
        return True

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        if not inspect.isgenerator(arg):
            raise ctx.wrap(UntypyTypeError(arg, self.describe()))

        me = self
        yield_ctx = TypedGeneratorYieldReturnContext(arg, self, True, ctx)
        return_ctx = TypedGeneratorYieldReturnContext(arg, self, False, ctx)

        def wrapped():
            try:
                sent = None
                while True:
                    value_yield = arg.send(sent)
                    # check value_yield (arg is responsable)
                    value_yield = me.yield_checker.check_and_wrap(value_yield, yield_ctx)

                    sent = yield value_yield

                    # first is this fn
                    stack = inspect.stack()[1:]
                    # Use Callers of Callables
                    caller = next((e for e in stack if not e.function == '__call__'), None)

                    # check sent value (caller is responsable)
                    sent = me.send_checker.check_and_wrap(sent, TypedGeneratorSendContext(caller, me, ctx))

            except StopIteration as e:
                # check value_returned (arg is responsable)
                ret = me.return_checker.check_and_wrap(e.value, return_ctx)
                return ret

        return wrapped()

    def describe(self) -> str:
        return f"Generator[{self.yield_checker.describe()}, {self.send_checker.describe()}, {self.return_checker.describe()}]"

    def base_type(self) -> Any:
        return [GeneratorType]


class TypedGeneratorYieldReturnContext(CompoundTypeExecutionContext):
    generator: Generator[Any, Any, Any]

    def __init__(self, generator: Generator[Any, Any, Any], checker: GeneratorChecker, is_yield : bool, upper: ExecutionContext):
        self.generator = generator
        # index in checkers list
        if is_yield:
            idx = 0
        else:
            idx = 2
        super().__init__(upper, [checker.yield_checker, checker.send_checker, checker.return_checker], idx)

    def name(self) -> str:
        return "Generator"

    def responsable(self) -> Optional[Location]:
        try:
            if hasattr(self.generator, 'gi_frame'):
                return Location(
                    file=inspect.getfile(self.generator.gi_frame),
                    line_no=inspect.getsourcelines(self.generator.gi_frame)[1],
                    source_line="\n".join(inspect.getsourcelines(self.generator.gi_frame)[0]),
                )
        except OSError: # this call does not work all the time
            pass
        except TypeError:
            pass
        return None


class TypedGeneratorSendContext(CompoundTypeExecutionContext):
    def __init__(self, stack: inspect.FrameInfo, checker: GeneratorChecker, upper: ExecutionContext):
        self.stack = stack
        super().__init__(NoResponsabilityWrapper(upper), [checker.yield_checker, checker.send_checker, checker.return_checker], 1)

    def name(self) -> str:
        return "Generator"

    def responsable(self) -> Optional[Location]:
        return Location(
            file=self.stack.filename,
            line_no=self.stack.lineno,
            source_line=self.stack.code_context[0]
        )


