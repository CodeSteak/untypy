import inspect

from collections import namedtuple
from types import ModuleType, FunctionType
from typing import Callable, Dict, Tuple
from untypy.impl import DefaultCreationContext

from untypy.error import UntypyAttributeError, UntypyTypeError, Frame, Location
from untypy.impl.any import AnyChecker
from untypy.interfaces import CreationContext, TypeChecker, ExecutionContext

Config = namedtuple('PatchConfig', 'verbose')

DefaultConfig = Config(verbose=True)


not_patching = ['__class__']


def patch_module(mod : ModuleType, cfg: Config = DefaultConfig) -> None:
    _patch_module_or_class(mod, cfg)


def patch_class(clas : type, cfg: Config = DefaultConfig) -> None:
    _patch_module_or_class(clas, cfg)


def _patch_module_or_class(unit, cfg) -> None:
    if cfg.verbose:
        if inspect.ismodule(unit):
            print(f"Patching Module: {unit}")
        elif inspect.isclass(unit):
            print(f"Patching Class: {unit}")
        else:
            print(f"Skipping: {unit}")

    if hasattr(unit, "__patched") is True:
        # Skip, already patched
        return

    setattr(unit, "__patched", True)

    for [name, member] in inspect.getmembers(unit):
        if name in not_patching:
            pass
        elif inspect.isfunction(member):
            setattr(unit, name, patch_function(member, cfg))
        elif inspect.isclass(member):
            patch_class(member, cfg)
        # else skip


def patch_function(fn: FunctionType, cfg: Config = DefaultConfig) -> Callable:
    if len(inspect.getfullargspec(fn).annotations) > 0:
        if cfg.verbose:
            print(f"Patching Function: {fn.__name__}")

        return TypedFunctionBuilder(fn, DefaultCreationContext(Location(
            file=inspect.getfile(fn),
            line_no=inspect.getsourcelines(fn)[1],
            source_line="".join(inspect.getsourcelines(fn)[0]),
        ))).build()
    else:
        return fn


class TypedFunctionBuilder:
    inner: Callable
    spec: inspect.FullArgSpec
    checkers: Dict[str, TypeChecker]

    special_args = ['self', 'cls']
    method_name_ignore_return = ['__init__']

    def __init__(self, inner: Callable, ctx: CreationContext):
        self.inner = inner
        self.spec = inspect.getfullargspec(inner)
        checkers = {}

        checked_keys = self.spec.args
        if inner.__name__ in self.method_name_ignore_return:
            checkers['return'] = AnyChecker()
        else:
            checked_keys += ['return']

        # Remove self and cls from checking
        if checked_keys[0] in self.special_args:
            checkers[checked_keys[0]] = AnyChecker()
            checked_keys = checked_keys[1:]

        for key in checked_keys:
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

    def build(self):
        if len(self.spec.args) > 0 and self.spec.args[0] in self.special_args:
            return self.build_class_method()
        else:
            return self.build_non_class_method()

    def build_non_class_method(self):
        me = self

        def wrapper(*args, **kwargs):
            # first is this fn
            caller = inspect.stack()[1]

            new_args = []
            for (arg, name) in zip(args, me.spec.args):
                check = me.checkers[name]
                ctx = ArgumentExecutionContext(me, caller, name)
                res = check.check_and_wrap(arg, ctx)
                new_args.append(res)

            ret = me.inner(*new_args, **kwargs)
            check = me.checkers['return']
            ret = check.check_and_wrap(ret, ReturnExecutionContext(me))
            return ret

        return wrapper

    def build_class_method(self):
        me = self
        spec_args = me.spec.args[1:] # we need to skip self

        def wrapper(self, *args, **kwargs):
            # first is this fn
            caller = inspect.stack()[1]

            new_args = []
            for (arg, name) in zip(args, spec_args):
                check = me.checkers[name]
                ctx = ArgumentExecutionContext(me, caller, name)
                res = check.check_and_wrap(arg, ctx)
                new_args.append(res)

            ret = me.inner(self, *new_args, **kwargs)
            check = me.checkers['return']
            ret = check.check_and_wrap(ret, ReturnExecutionContext(me))
            return ret

        return wrapper


class ReturnExecutionContext(ExecutionContext):
    fn: TypedFunctionBuilder

    def __init__(self, fn: TypedFunctionBuilder):
        self.fn = fn

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        (next_ty, indicator) = err.next_type_and_indicator()

        arg_types = []
        for i, name in enumerate(self.fn.spec.args):
            arg_types.append(self.fn.checkers[name].describe())

        front_str = f"def {self.fn.inner.__name__}({', '.join(arg_types)}) -> "

        declared = Location(
            file=inspect.getfile(self.fn.inner),
            line_no=inspect.getsourcelines(self.fn.inner)[1],
            source_line="".join(inspect.getsourcelines(self.fn.inner)[0]),
        )

        return err.with_frame(Frame(
            front_str + next_ty,
            (" "*len(front_str)) + indicator,
            declared=declared,
            responsable=declared,
        ))


class ArgumentExecutionContext(ExecutionContext):
    fn: TypedFunctionBuilder
    stack: inspect.FrameInfo
    argument_name: str

    def __init__(self, fn: TypedFunctionBuilder, stack: inspect.FrameInfo, argument_name: str):
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

        declared = Location(
            file=inspect.getfile(self.fn.inner),
            line_no=inspect.getsourcelines(self.fn.inner)[1],
            source_line="".join(inspect.getsourcelines(self.fn.inner)[0]),
        )

        responsable = Location(
            file=self.stack.filename,
            line_no=self.stack.lineno,
            source_line=self.stack.code_context[0]
        )

        frame = Frame(
            type_declared,
            indicator_line,
            declared=declared,
            responsable=responsable
        )
        return err.with_frame(frame)
