import inspect
from collections import namedtuple
from types import ModuleType, FunctionType
from typing import Callable, Dict, Tuple
from untypy.impl import DefaultCreationContext

from untypy.error import UntypyAttributeError, UntypyTypeError, Frame
from untypy.interfaces import CreationContext, TypeChecker, ExecutionContext

Config = namedtuple('PatchConfig', 'verbose')

DefaultConfig = Config(verbose=True)


def patch_module(mod: ModuleType, cfg: Config = DefaultConfig) -> None:
    if cfg.verbose:
        print(f"Patching Module: {mod}")

    if hasattr(mod, "__patched") is True:
        # Skip, already patched
        return

    setattr(mod, "__patched", True)

    for [name, member] in inspect.getmembers(mod):
        if inspect.isfunction(member):
            setattr(mod, name, patch_function(member, cfg))
        if inspect.isclass(member):
            patch_class(member, cfg)
        # else skip


def patch_function(fn: FunctionType, cfg: Config = DefaultConfig) -> Callable:
    if len(inspect.getfullargspec(fn).annotations) > 0:
        if cfg.verbose:
            print(f"Patching Function: {fn.__name__}")

        return TypedFunction(fn, DefaultCreationContext())
    else:
        return fn


def patch_class(clas, cfg: Config = DefaultConfig) -> None:
    print(f"WARN: Skipping Class {clas} NIY")
    pass


class TypedFunction(Callable):
    inner: Callable
    spec: inspect.FullArgSpec
    checkers: Dict[str, TypeChecker]
    __patched: bool

    def __init__(self, inner: Callable, ctx: CreationContext):
        self.inner = inner
        self.spec = inspect.getfullargspec(inner)
        checkers = {}
        for key in (self.spec.args + ['return']):
            if key not in self.spec.annotations:
                raise UntypyAttributeError(f"\Missing Annotation for argument '{key}' of function {inner.__name__}\n"
                                           f"{inspect.getfile(inner)}:{inspect.getsourcelines(inner)[1]}\n"
                                           "Partial Annotation are not supported."
                                           )
            checker = ctx.find_checker(self.spec.annotations[key])
            if checker is None:
                # TODO: Maybe Nicer Error
                raise UntypyAttributeError(f"\n\tUnsupported Type Annotation: {self.spec.annotations[key]}\n"
                                           f"\tin argument '{key}' of function {inner.__name__}\n"
                                           f"\n"
                                           f"\tdef {inner.__name__}{inspect.signature(inner)}\t\n"
                                           f"\n"
                                           f"\t{inspect.getfile(inner)}:{inspect.getsourcelines(inner)[1]}"
                                           )
            else:
                checkers[key] = checker
        self.checkers = checkers
        self.__patched = True

    def __call__(self, *args, **kwargs):
        # TODO: KWARGS?
        # first is this fn
        stack = inspect.stack()[1:]
        # Use Callers of Callables
        caller = next((e for e in stack if not e.function == '__call__'), None)

        new_args = []
        for (arg, name) in zip(args, self.spec.args):
            check = self.checkers[name]
            ctx = ArgumentExecutionContext(self, caller, name)
            res = check.check_and_wrap(arg, ctx)
            new_args.append(res)

        ret = self.inner(*new_args, **kwargs)
        check = self.checkers['return']
        ret = check.check_and_wrap(ret, ReturnExecutionContext(self))
        return ret


class ReturnExecutionContext(ExecutionContext):
    fn: TypedFunction

    def __init__(self, fn: TypedFunction):
        self.fn = fn

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        (next_ty, indicator) = err.next_type_and_indicator()

        arg_types = []
        for i, name in enumerate(self.fn.spec.args):
            arg_types.append(self.fn.checkers[name].describe())

        front_str = f"def {self.fn.inner.__name__}({', '.join(arg_types)}) -> "

        return err.with_frame(Frame(
            front_str + next_ty,
            (" "*len(front_str)) + indicator,

            file=inspect.getfile(self.fn.inner),
            line_no=inspect.getsourcelines(self.fn.inner)[1],
            source_line="".join(inspect.getsourcelines(self.fn.inner)[0]),
        ))


class ArgumentExecutionContext(ExecutionContext):
    fn: TypedFunction
    stack: inspect.FrameInfo
    argument_name: str

    def __init__(self, fn: TypedFunction, stack: inspect.FrameInfo, argument_name: str):
        self.fn = fn
        self.stack = stack
        self.argument_name = argument_name

    def declared_and_indicator(self, err: UntypyTypeError) -> Tuple[str, str]:
        (next_ty, indicator) = err.next_type_and_indicator()

        front_types = []
        back_types = []
        highlighted = None
        for i, name in enumerate(self.fn.spec.args):
            if name == self.argument_name:
                highlighted = next_ty
            elif highlighted is None:
                front_types.append(self.fn.checkers[name].describe())
            else:
                back_types.append(self.fn.checkers[name].describe())

        l = len(f"def {self.fn.inner.__name__}({', '.join(front_types)}")
        if len(front_types) > 0:
            l += len(', ')

        return f"def {self.fn.inner.__name__}({', '.join(front_types + [highlighted] + back_types)}) ->" \
               f"  {self.fn.checkers['return'].describe()}", (
                    " " * l) + indicator

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        (type_declared, indicator_line) = self.declared_and_indicator(err)

        frame = Frame(
            type_declared,
            indicator_line,

            file=self.stack.filename,
            line_no=self.stack.lineno,
            source_line=self.stack.code_context[0]
        )
        return err.with_frame(frame)
