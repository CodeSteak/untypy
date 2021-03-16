from .lambdachecker import LambdaFactory
from .listchecker import ListFactory
from .typechecker import TypeFactory

AllFactoriesInOrder = [
    LambdaFactory(),
    ListFactory(),
    TypeFactory()
]
