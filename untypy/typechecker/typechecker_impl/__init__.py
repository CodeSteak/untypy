from .lambda_checker import LambdaFactory
from .list_checker import ListFactory
from .simple_type_checker import TypeFactory

AllFactoriesInOrder = [
    LambdaFactory(),
    ListFactory(),
    TypeFactory()
]
