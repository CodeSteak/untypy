import inspect
from typing import Protocol, Any, Optional, Callable, Union, TypeVar

from untypy.error import UntypyTypeError, UntypyAttributeError, Frame, Location, ResponsibilityType
from untypy.impl.any import SelfChecker
from untypy.interfaces import TypeCheckerFactory, CreationContext, TypeChecker, ExecutionContext, \
    WrappedFunctionContextProvider
from untypy.util import WrappedFunction, ArgumentExecutionContext, ReturnExecutionContext


class ProtocolFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        if isinstance(annotation, type) and Protocol in annotation.mro():
            return ProtocolChecker(annotation, ctx)
        else:
            return None


def _find_bound_typevars(clas: type) -> (type, dict[TypeVar, Any]):
    if not hasattr(clas, '__args__') or not hasattr(clas, '__origin__'):
        return (clas, dict())
    if not hasattr(clas.__origin__, '__parameters__'):
        return (clas, dict())

    keys = clas.__origin__.__parameters__
    values = clas.__args__

    if len(keys) != len(values):
        raise UntypyAttributeError(f"Some unbound Parameters in {clas.__name__}. "
                                   f"keys={keys} do not match values={values}.",
                                   Location(
                                       file=inspect.getfile(clas),
                                       line_no=inspect.getsourcelines(clas)[1],
                                       source_line="".join(inspect.getsourcelines(clas)[0])));
    return (clas.__origin__, dict(zip(keys, values)))


def get_proto_members(proto: type, ctx: CreationContext) -> (
        type, dict[str, (inspect.Signature, dict[str, TypeChecker])]):
    (nproto, typevars) = _find_bound_typevars(proto)
    ctx = ctx.with_typevars(typevars)
    proto = nproto

    blacklist = ['__subclasshook__', '__init__', '__class_getitem__']
    member_dict = {}
    for [name, member] in inspect.getmembers(proto):
        if inspect.isfunction(member) and name not in blacklist:
            signature = inspect.signature(member)
            checkers = {}
            for key in signature.parameters:
                if key == 'self':
                    checkers[key] = SelfChecker()
                else:
                    param = signature.parameters[key]
                    if param.annotation is inspect.Parameter.empty:
                        raise ctx.wrap(UntypyAttributeError(
                            f"\Missing Annotation for argument '{key}' of function {member.__name__} "
                            f"in Protocol {proto.__name__}\n"))

                    checker = ctx.find_checker(param.annotation)
                    if checker is None:
                        raise ctx.wrap(UntypyAttributeError(f"\n\tUnsupported Type Annotation: {param.annotation}\n"
                                                            f"for argument '{key}' of function {member.__name__} "
                                                            f"in Protocol {proto.__name__}.\n"))
                    checkers[key] = checker

            if signature.return_annotation is inspect.Parameter.empty:
                raise ctx.wrap(UntypyAttributeError(
                    f"\Missing Annotation for Return Value of function {member.__name__} "
                    f"in Protocol {proto.__name__}. Use 'None' if there is no return value.\n"))
            return_checker = ctx.find_checker(signature.return_annotation)
            if return_checker is None:
                raise ctx.wrap(UntypyAttributeError(f"\n\tUnsupported Type Annotation: {signature.return_annotation}\n"
                                                    f"for Return Value of function {member.__name__} "
                                                    f"in Protocol {proto.__name__}.\n"))
            checkers['return'] = return_checker
            member_dict[name] = (signature, checkers)
    return (nproto, member_dict)


class ProtocolChecker(TypeChecker):
    def __init__(self, proto: type, ctx: CreationContext):
        (nproto, members) = get_proto_members(proto, ctx)
        self.proto = nproto
        self.members = members

    def may_change_identity(self) -> bool:
        return True

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext, *, signature_diff=False) -> Any:
        for name in self.members.keys():
            if not hasattr(arg, name):
                raise ctx.wrap(UntypyTypeError(arg, self.describe(),
                                               notes=[f"{type(arg).__name__} is missing method '{name}'."]))
            if not signature_diff:
                if hasattr(getattr(arg, name), '__signature__'):
                    arg_signature = getattr(arg, name).__signature__
                    (prot_signature, _protdict) = self.members[name]
                    if prot_signature != arg_signature:
                        signature_diff = True
                else:
                    signature_diff = True
        if not signature_diff:
            return arg
        else:
            return ProtocolWrapper(arg, self, ctx)

    def base_type(self) -> list[Any]:
        # Protocols are distinguishable by method definitions
        # Note: set would be the better fit, but it is not hashable
        return ["; ".join(sorted(self.members.keys()))]

    def base_type_priority(self):
        return [len(self.members.keys())]

    def describe(self) -> str:
        return f"{self.proto.__name__}({self.protocol_type()})"

    def protocol_type(self) -> str:
        return f"Protocol"


class ProtocolWrapper:

    def __init__(self, inner: Any, proto: ProtocolChecker, ctx: ExecutionContext):
        if type(inner) is ProtocolWrapper:
            inner = inner.__inner

        self.__ctx = ctx
        self.__proto = proto
        self.__inner = inner

    def __getattr__(self, item):
        sig_check = self.__proto.members.get(item)
        if sig_check is None:
            raise LookupError(f"Protocol {self.__proto.proto.__name__} does not define a method {item}.")

        (signature, checker) = sig_check

        innerfn = getattr(self.__inner, item)
        if hasattr(innerfn, '__wf'):
            innerfn = getattr(innerfn, '__wf')
        if hasattr(innerfn, '__func__'):
            innerfn = innerfn.__func__
        wf = ProtocolWrappedFunction(self.__inner, innerfn, signature, checker, self.__proto, self.__ctx).build()

        setattr(self, item, wf)
        return wf


class ProtocolWrappedFunction(WrappedFunction):

    def __init__(self, me, inner: Union[Callable, WrappedFunction], signature: inspect.Signature,
                 checker: dict[str, TypeChecker],
                 protocol: ProtocolChecker,
                 ctx: ExecutionContext):
        self.me = me
        self.inner = inner
        self.signature = signature
        self.checker = checker
        self.protocol = protocol
        self.ctx = ctx

    def build(self):
        fn = WrappedFunction.find_original(self.inner)
        fn_of_protocol = getattr(getattr(self.protocol.proto, fn.__name__), '__wf')

        def wrapper(*args, **kwargs):
            caller = inspect.stack()[1]
            (args, kwargs) = self.wrap_arguments(lambda n: ArgumentExecutionContext(fn_of_protocol, caller, n),
                                                 (self.me, *args), kwargs)
            if isinstance(self.inner, WrappedFunction):
                (args, kwargs) = self.inner.wrap_arguments(lambda n: ProtocolArgumentExecutionContext(self, n), args,
                                                           kwargs)
            ret = fn(*args, **kwargs)
            if isinstance(self.inner, WrappedFunction):
                ret = self.inner.wrap_return(ret, ProtocolReturnExecutionContext(self, ResponsibilityType.IN))
            return self.wrap_return(ret, ProtocolReturnExecutionContext(self, ResponsibilityType.OUT))

        async def async_wrapper(*args, **kwargs):
            raise AssertionError("Not correctly implemented see wrapper")
            # caller = inspect.stack()[1]
            # (args, kwargs) = self.wrap_arguments(lambda n: ArgumentExecutionContext(self, caller, n), args, kwargs)
            # if isinstance(self.inner, WrappedFunction):
            #     (args, kwargs) = self.inner.wrap_arguments(lambda n: ProtocolArgumentExecutionContext(self, n), args, kwargs)
            # ret = await fn(*args, **kwargs)
            # if isinstance(self.inner, WrappedFunction):
            #     ret = self.inner.wrap_return(ret, ReturnExecutionContext(self.inner))
            # print(self)
            # return self.wrap_return(ret, ProtocolArgumentExecutionContext(self, 'return'))

        if inspect.iscoroutine(self.inner):
            w = async_wrapper
        else:
            w = wrapper

        setattr(w, '__wrapped__', fn)
        setattr(w, '__name__', fn.__name__)
        setattr(w, '__signature__', self.signature)
        setattr(w, '__wf', self)
        return w

    def get_original(self):
        return self.inner

    def wrap_arguments(self, ctxprv: WrappedFunctionContextProvider, args, kwargs):
        bindings = self.signature.bind(*args, **kwargs)
        bindings.apply_defaults()
        for name in bindings.arguments:
            check = self.checker[name]
            ctx = ctxprv(name)
            bindings.arguments[name] = check.check_and_wrap(bindings.arguments[name], ctx)
        return (bindings.args, bindings.kwargs)

    def wrap_return(self, ret, ctx: ExecutionContext):
        check = self.checker['return']
        return check.check_and_wrap(ret, ctx)

    def describe(self) -> str:
        fn = WrappedFunction.find_original(self.inner)
        return f"{fn.__name__}" + str(self.signature)

    def checker_for(self, name: str) -> TypeChecker:
        return self.checker[name]

    def declared(self) -> Location:
        fn = WrappedFunction.find_original(self.inner)
        return WrappedFunction.find_location(getattr(self.protocol.proto, fn.__name__))


class ProtocolReturnExecutionContext(ExecutionContext):
    def __init__(self, wf: ProtocolWrappedFunction, invert: ResponsibilityType):
        self.wf = wf
        self.invert = invert

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        err = ReturnExecutionContext(self.wf).wrap(err)

        if err.responsibility_type is self.invert:
            return err

        responsable = WrappedFunction.find_location(self.wf)
        (decl, ind) = err.next_type_and_indicator()
        err = err.with_inverted_responsibility_type()
        err = err.with_frame(Frame(
            decl,
            ind,
            declared=self.wf.declared(),
            responsable=responsable
        ))

        inner = self.wf.inner
        if isinstance(inner, WrappedFunction):
            err = err.with_note(
                f"The return value of method '{WrappedFunction.find_original(self.wf).__name__}' does violate the {self.wf.protocol.protocol_type()} '{self.wf.protocol.proto.__name__}'.")
            err = err.with_note(
                f"The annotation '{inner.checker_for('return').describe()}' is incompatible with the {self.wf.protocol.protocol_type()}'s annotation '{self.wf.checker_for('return').describe()}'\nwhen checking against the following value:")

        previous_chain = UntypyTypeError(
            self.wf.me,
            f"{self.wf.protocol.proto.__name__}"
        ).with_note(
            f"Type '{type(self.wf.me).__name__}' does not implement {self.wf.protocol.protocol_type()} '{self.wf.protocol.proto.__name__}' correctly.")

        previous_chain = self.wf.ctx.wrap(previous_chain)
        return err.with_previous_chain(previous_chain)


class ProtocolArgumentExecutionContext(ExecutionContext):
    def __init__(self, wf: ProtocolWrappedFunction, arg_name: str):
        self.wf = wf
        self.arg_name = arg_name

    def wrap(self, err: UntypyTypeError) -> UntypyTypeError:
        (original_expected, _ind) = err.next_type_and_indicator()
        err = ArgumentExecutionContext(self.wf, None, self.arg_name).wrap(err)

        responsable = WrappedFunction.find_location(self.wf)

        (decl, ind) = err.next_type_and_indicator()
        err = err.with_frame(Frame(
            decl,
            ind,
            declared=self.wf.declared(),
            responsable=responsable
        ))

        err = err.with_note(
            f"The argument '{self.arg_name}' of method '{WrappedFunction.find_original(self.wf).__name__}' violates the {self.wf.protocol.protocol_type()} '{self.wf.protocol.proto.__name__}'.")
        err = err.with_note(
            f"The annotation '{original_expected}' is incompatible with the {self.wf.protocol.protocol_type()}'s annotation '{self.wf.checker_for(self.arg_name).describe()}'\nwhen checking against the following value:")

        previous_chain = UntypyTypeError(
            self.wf.me,
            f"{self.wf.protocol.proto.__name__}"
        ).with_note(
            f"Type '{type(self.wf.me).__name__}' does not implement {self.wf.protocol.protocol_type()} '{self.wf.protocol.proto.__name__}' correctly.")

        previous_chain = self.wf.ctx.wrap(previous_chain)
        # err = err.with_inverted_responsibility_type()

        return err.with_previous_chain(previous_chain)
