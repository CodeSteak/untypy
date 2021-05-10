import inspect
from typing import Protocol, Any, Optional, Callable

from untypy.error import UntypyTypeError, UntypyAttributeError, Frame, Location
from untypy.impl.any import AnyChecker
from untypy.interfaces import TypeCheckerFactory, CreationContext, TypeChecker, ExecutionContext
from untypy.util import WrappedFunction, ArgumentExecutionContext, ReturnExecutionContext


class ProtocolFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if isinstance(annotation, type) and Protocol in annotation.mro():
            return ProtocolChecker(annotation, ctx)
        else:
            return None


def get_proto_members(proto: type, ctx: CreationContext) -> dict[str, (inspect.FullArgSpec, dict[str, TypeChecker])]:
    blacklist = ['__subclasshook__', '__init__']
    member_dict = {}
    for [name, member] in inspect.getmembers(proto):
        if inspect.isfunction(member) and name not in blacklist:
            spec = inspect.getfullargspec(member)
            checked_keys = spec.args + ['return']
            checkers = {}
            for key in checked_keys:
                if key == 'self':
                    checkers[key] = AnyChecker()
                else:
                    if key not in spec.annotations:
                        raise UntypyAttributeError(
                            f"\Missing Annotation for argument '{key}' of function {member.__name__} "
                            f"in Protocol {proto.__name__}\n"
                            f"{inspect.getfile(proto)}:{inspect.getsourcelines(proto)[1]}\n")

                    checker = ctx.find_checker(spec.annotations[key])
                    if checker is None:
                        raise UntypyAttributeError(f"\n\tUnsupported Type Annotation: {spec.annotations[key]}\n"
                                                   f"for argument '{key}' of function {member.__name__} "
                                                   f"in Protocol {proto.__name__}.\n"
                                                   f"{inspect.getfile(proto)}:{inspect.getsourcelines(proto)[1]}\n")
                    checkers[key] = checker
            member_dict[name] = (spec, checkers)
    return member_dict


class ProtocolChecker(TypeChecker):
    def __init__(self, proto: type, ctx: CreationContext):
        members = get_proto_members(proto, ctx)
        self.proto = proto
        self.members = members

    def may_change_identity(self) -> bool:
        return True

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext) -> Any:
        for name in self.members.keys():
            if not hasattr(arg, name):
                raise ctx.wrap(UntypyTypeError(arg, self.describe()))  # TODO notes=[f"Missing method '{name}'"]))

        return ProtocolWrapper(arg, self.proto, self.members, ctx)

    def base_type(self) -> list[Any]:
        return [list]

    def describe(self) -> str:
        return f"{self.proto}(Protocol)"


class ProtocolWrapper(WrappedFunction):

    def __init__(self, inner: Any, proto: type, members: dict[str, (inspect.FullArgSpec, dict[str, TypeChecker])],
                 ctx: ExecutionContext):
        self.proto = proto
        self.members = members
        self.ctx = ctx
        self.inner = inner

    def __getattr__(self, item):
        # TODO: Async

        (spec, checkers) = self.members[item]

        # TODO: if members[item] does not exist

        def wrapper_fn(*args, **kwargs):
            # first is this fn
            caller = inspect.stack()[1]

            # TODO: KWARGS?
            f_wrapped = getattr(self.inner, item)  # Should not fail, checked at creation of wrapper
            if hasattr(f_wrapped, '__checkers'):
                inner_checkers = getattr(f_wrapped, '__checkers')
                wf = getattr(f_wrapped, '__wf')
                f = f_wrapped.__wrapped__
            else:
                raise NotImplementedError

            new_args = []
            for (arg, name) in zip(args, spec.args[1:]):
                check = checkers[name]
                # TODO BUG: what if different names
                ctx = ArgumentExecutionContext(getattr(getattr(self.proto, item), '__wf'), caller, name)
                res = check.check_and_wrap(arg, ctx)
                inner_check = inner_checkers.get(name)
                if inner_check is not None:
                    ctx = ProtocolArgumentExecutionContext(self.inner, self.proto, checkers, f, name, self.ctx)
                    res = inner_check.check_and_wrap(res, ctx)
                new_args.append(res)

            ret = f(self.inner, *new_args, **kwargs)
            inner_check = inner_checkers.get('return')
            if inner_check is not None:
                ret = inner_check.check_and_wrap(ret, ReturnExecutionContext(wf))
            ret = checkers['return'].check_and_wrap(ret, ProtocolArgumentExecutionContext(self.inner, self.proto, checkers, f, 'return', self.ctx))
            return ret

        return wrapper_fn


class ProtocolArgumentExecutionContext(ExecutionContext, WrappedFunction):

    def __init__(self, self_inst, proto: type, checkers: dict[str, TypeChecker], function: Callable, arg_name: str, upper: ExecutionContext):
        self.checkers = checkers
        if hasattr(function, '__wrapped__'):
            self.function = function.__wrapped__
        else:
            self.function = function
        self.arg_name = arg_name
        self.self_inst = self_inst
        self.proto = proto
        self.upper = upper

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        if self.arg_name == 'return':
            arg = ReturnExecutionContext(self)
        else:
            arg = ArgumentExecutionContext(self, None,  self.arg_name)
        err = arg.wrap(err)
        # TODO err = err.with_frame(Frame(
        #     f"{front_str}{next_ty}]",
        #     (" " * len(front_str)) + indicator,
        #     declared=None,
        #     responsable=responsable
        # ))

        responsable = Location(
            file=inspect.getfile(self.function),
            line_no=inspect.getsourcelines(self.function)[1],
            source_line="".join(inspect.getsourcelines(self.function)[0]),
        )

        (decl, ind) = err.next_type_and_indicator()
        err = err.with_frame(Frame(
            decl,
            ind,
            declared=None,
            responsable=responsable
        ))

        err = UntypyTypeError(
            self.self_inst,
            f"{self.proto.__name__}<Protocol>",
            previous_chain=err
        )

        return self.upper.wrap(err)

    def wrapped_original(self) -> Callable:
        f = getattr(self.proto, self.function.__name__)
        if hasattr(f, '__wrapped__'):
            return f.__wrapped__
        return f

    def wrapped_fullspec(self) -> inspect.FullArgSpec:
        return inspect.getfullargspec(self.wrapped_original())

    def wrapped_checker(self) -> dict[str, TypeChecker]:
        return self.checkers
