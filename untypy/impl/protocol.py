import inspect
from typing import Protocol, Any, Optional, Callable, Union, TypeVar, Dict, Tuple

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


def _find_bound_typevars(clas: type) -> (type, Dict[TypeVar, Any]):
    if not hasattr(clas, '__args__') or not hasattr(clas, '__origin__'):
        return (clas, dict())
    if not hasattr(clas.__origin__, '__parameters__'):
        return (clas, dict())

    keys = clas.__origin__.__parameters__
    values = clas.__args__

    if len(keys) != len(values):
        raise UntypyAttributeError(f"Some unbound Parameters in {clas.__name__}. "
                                   f"keys={keys} do not match values={values}.",
                                   [Location(
                                       file=inspect.getfile(clas),
                                       line_no=inspect.getsourcelines(clas)[1],
                                       source_line="".join(inspect.getsourcelines(clas)[0]))])
    return (clas.__origin__, dict(zip(keys, values)))


def get_proto_members(proto: type, ctx: CreationContext) -> Dict[str, Tuple[inspect.Signature, dict[str, TypeChecker]]]:
    blacklist = ['__init__', '__class__', '__delattr__', '__dict__', '__dir__',
                 '__doc__', '__getattribute__', '__getattr__', '__init_subclass__',
                 '__new__', '__setattr__', '__subclasshook__', '__weakref__',
                 '__abstractmethods__', '__class_getitem__']

    member_dict = {}
    for [name, member] in inspect.getmembers(proto):
        if name in blacklist:
            continue

        if inspect.isfunction(member):
            member = WrappedFunction.find_original(member)
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
    return member_dict


class ProtocolChecker(TypeChecker):
    def __init__(self, annotation: type, ctx: CreationContext):
        (proto, typevars) = _find_bound_typevars(annotation)
        ctx = ctx.with_typevars(typevars)
        members = get_proto_members(proto, ctx)
        self.proto = proto
        self.members = members
        self.typevars = typevars
        self.wrapper_types = dict()

    def may_change_identity(self) -> bool:
        return True

    def check_and_wrap(self, arg: Any, ctx: ExecutionContext, *, signature_diff=False) -> Any:
        if type(arg) in self.wrapper_types:
            return self.wrapper_types[type(arg)](arg, ctx)
        else:
            wrapped_type = ProtocolWrapper(self, type(arg), self.members, ctx)
            self.wrapper_types[type(arg)] = wrapped_type
            return wrapped_type(arg, ctx)

    def base_type(self) -> list[Any]:
        # Protocols are distinguishable by method definitions
        # Note: set would be the better fit, but it is not hashable
        return ["; ".join(sorted(self.members.keys()))]

    def base_type_priority(self):
        return [len(self.members.keys())]

    def describe(self) -> str:
        desc = set([])
        for name in self.members:
            (sig, binds) = self.members[name]
            for argname in sig.parameters:
                if isinstance(sig.parameters[argname].annotation, TypeVar):
                    desc.add(binds[argname].describe())
        if len(desc) > 0:
            return f"{self.proto.__name__}[" + (', '.join(desc)) + "]"
        else:
            return f"{self.proto.__name__}({self.protocol_type()})"

    def protocol_type(self) -> str:
        return f"Protocol"

    def protoname(self):
        return self.describe()


def ProtocolWrapper(protocolchecker: ProtocolChecker, original: type,
                    members: Dict[str, Tuple[inspect.Signature, dict[str, TypeChecker]]], ctx: ExecutionContext):
    list_of_attr = dict()
    for fnname in members:
        if not hasattr(original, fnname):
            raise ctx.wrap(UntypyTypeError(
                expected=protocolchecker.describe(),
                given=original.__name__
            )).with_note(
                f"Type {original.__name__} does not meet the requirements of Protocol {protocolchecker.proto.__name__}. It is missing the function '{fnname}'")

        original_fn = getattr(original, fnname)
        original_fn_signature = inspect.signature(original_fn)

        if hasattr(original_fn, '__wf'):
            original_fn = getattr(original_fn, '__wf')
        (sig, argdict) = members[fnname]

        for param in sig.parameters:
            if param not in original_fn_signature.parameters:
                raise ctx.wrap(UntypyTypeError(
                    expected=protocolchecker.describe(),
                    given=original.__name__
                )).with_note(
                    f"Type {original.__name__} does not meet the requirements of Protocol {protocolchecker.proto.__name__}. The signature of '{fnname}' does not match. Missing required parameter {param}")

        list_of_attr[fnname] = ProtocolWrappedFunction(original_fn, sig, argdict, protocolchecker).build()

    def constructor(me, inner, ctx):
        me._ProtocolWrappedFunction__inner = inner
        me._ProtocolWrappedFunction__ctx = ctx

    list_of_attr['__init__'] = constructor
    name = f"{protocolchecker.proto.__name__}For{original.__name__}"
    return type(name, (), list_of_attr)


# class ProtocolWrapper:
#
#     def __init__(self, inner: Any, proto: ProtocolChecker, ctx: ExecutionContext):
#         if type(inner) is ProtocolWrapper:
#             inner = inner.__inner
#
#         self.__ctx = ctx
#         self.__proto = proto
#         self.__inner = inner
#
#     def __getattr__(self, item):
#         sig_check = self.__proto.members.get(item)
#         if sig_check is None:
#             raise LookupError(f"Protocol {self.__proto.proto.__name__} does not define a method {item}.")
#
#         (signature, checker) = sig_check
#
#         innerfn = getattr(self.__inner, item)
#         if hasattr(innerfn, '__wf'):
#             innerfn = getattr(innerfn, '__wf')
#         if hasattr(innerfn, '__func__'):
#             innerfn = innerfn.__func__
#         wf = ProtocolWrappedFunction(self.__inner, innerfn, signature, checker, self.__proto, self.__ctx).build()
#
#         setattr(self, item, wf)
#         return wf
#

class ProtocolWrappedFunction(WrappedFunction):

    def __init__(self, inner: Union[Callable, WrappedFunction], signature: inspect.Signature,
                 checker: Dict[str, TypeChecker],
                 protocol: ProtocolChecker):
        self.inner = inner
        self.signature = signature
        self.checker = checker
        self.protocol = protocol

    def build(self):
        fn = WrappedFunction.find_original(self.inner)

        fn_of_protocol = getattr(self.protocol.proto, fn.__name__)
        if hasattr(fn_of_protocol, '__wf'):
            fn_of_protocol = getattr(fn_of_protocol, '__wf')

        def wrapper(me, *args, **kwargs):
            inner_object = me.__inner
            inner_ctx = me.__ctx

            caller = inspect.stack()[1]
            (args, kwargs) = self.wrap_arguments(lambda n: ArgumentExecutionContext(fn_of_protocol, caller, n),
                                                 (inner_object, *args), kwargs)
            if isinstance(self.inner, WrappedFunction):
                (args, kwargs) = self.inner.wrap_arguments(lambda n:
                                                           ProtocolArgumentExecutionContext(self, n, inner_object,
                                                                                            inner_ctx),
                                                           args, kwargs)
            ret = fn(*args, **kwargs)
            if isinstance(self.inner, WrappedFunction):
                ret = self.inner.wrap_return(ret, ProtocolReturnExecutionContext(self,
                                                                                 ResponsibilityType.IN, inner_object,
                                                                                 inner_ctx))
            return self.wrap_return(ret, ProtocolReturnExecutionContext(self,
                                                                        ResponsibilityType.OUT, inner_object,
                                                                        inner_ctx))

        async def async_wrapper(*args, **kwargs):
            raise AssertionError("Not correctly implemented see wrapper")

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
        return bindings.args, bindings.kwargs

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
    def __init__(self, wf: ProtocolWrappedFunction, invert: ResponsibilityType, me: Any, ctx: ExecutionContext):
        self.wf = wf
        self.invert = invert
        self.me = me
        self.ctx = ctx

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
            self.me,
            f"{self.wf.protocol.protoname()}"
        ).with_note(
            f"Type '{type(self.me).__name__}' does not implement {self.wf.protocol.protocol_type()} '{self.wf.protocol.protoname()}' correctly.")

        previous_chain = self.ctx.wrap(previous_chain)
        return err.with_previous_chain(previous_chain)


class ProtocolArgumentExecutionContext(ExecutionContext):
    def __init__(self, wf: ProtocolWrappedFunction, arg_name: str, me: Any, ctx: ExecutionContext):
        self.wf = wf
        self.arg_name = arg_name
        self.me = me
        self.ctx = ctx

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
            self.me,
            f"{self.wf.protocol.protoname()}"
        ).with_note(
            f"Type '{type(self.me).__name__}' does not implement {self.wf.protocol.protocol_type()} '{self.wf.protocol.protoname()}' correctly.")

        previous_chain = self.ctx.wrap(previous_chain)
        # err = err.with_inverted_responsibility_type()

        return err.with_previous_chain(previous_chain)
