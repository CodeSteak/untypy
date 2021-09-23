from typing import Any, Optional, Sequence

from untypy.error import UntypyTypeError, UntypyAttributeError
from untypy.interfaces import TypeChecker, TypeCheckerFactory, CreationContext, ExecutionContext
from untypy.util import CompoundTypeExecutionContext
from untypy.impl.simple import SimpleFactory
from untypy.impl.list import ListChecker
from untypy.impl.tuple import VariadicTupleChecker
from untypy.impl.union import UnionChecker

SequenceTypeA = type(Sequence[int])
SequenceTypeB = type(Sequence)

class SequenceFactory(TypeCheckerFactory):

    def create_from(self, annotation: Any, ctx: CreationContext) -> Optional[TypeChecker]:
        t = type(annotation)
        if t is SequenceTypeA or t is SequenceTypeB:
            try:
                args = annotation.__args__
            except AttributeError:
                args = []
            inner = []
            elemChecker = None
            if len(args) == 0:
                sf = SimpleFactory()
                inner = [sf.create_from(list, ctx),
                         sf.create_from(tuple, ctx),
                         sf.create_from(str, ctx)]
            elif len(args) == 1:
                elemChecker = ctx.find_checker(args[0])
                if elemChecker is None:
                    return None
                inner = [ListChecker(elemChecker, ctx.declared_location()),
                         VariadicTupleChecker(elemChecker)]
            return SequenceChecker(inner, ctx, elemChecker)
        else:
            return None

class SequenceChecker(UnionChecker):

    elemChecker: Optional[TypeChecker]

    def __init__(self, inner: list[TypeChecker], ctx: CreationContext, elemChecker: Optional[TypeChecker]):
        super().__init__(inner, ctx)
        self.elemChecker = elemChecker

    def describe(self) -> str:
        if self.elemChecker:
            desc = self.elemChecker.describe()
            return f"Sequence[{desc}]"
        else:
            return "Sequence"
