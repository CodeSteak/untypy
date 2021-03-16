from .default_type_manager import *
from .typechecker_impl import AllFactoriesInOrder

__all__ = ['GlobalTypeManager']

GlobalTypeManager = DefaultTypeManager(AllFactoriesInOrder)
