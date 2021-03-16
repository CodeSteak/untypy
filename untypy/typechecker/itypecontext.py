from collections.abc import Callable


class ITypeContext:
    def fail(self, info):
        raise Exception("This is an interface")

    def type_manager(self):
        raise Exception("This is an interface")

    def wrap_function(self, fun: Callable) -> Callable:
        raise Exception("This is an interface")

    def rescope(self, fun=None, arg=None, extra=None):
        raise Exception("This is an interface")
