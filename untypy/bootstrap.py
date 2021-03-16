import inspect
from types import *
from typing import *

from .decorator import wrap_function

__all__ = ['enable']


def enable():
    mod = _find_calling_module()
    if mod is None:
        raise Exception("Cound't find loading Module. This is a Bug")
    _monkey_patch_module(mod)


def _find_calling_module() -> Optional[ModuleType]:
    for caller in inspect.stack():
        if caller.filename != __file__:
            mod = inspect.getmodule(caller.frame)
            if mod is not None:
                return mod
    return None


def _monkey_patch_module(mod: ModuleType):
    _monkey_patch_functions(mod)
    # _monkey_patch_classes(mod)


def _monkey_patch_functions(mod: ModuleType):
    for [name, member] in inspect.getmembers(mod):
        if not inspect.isfunction(member):
            continue
        setattr(mod, name, wrap_function(member))
        print(f"pathed {name}")


def _monkey_patch_classes(mod: ModuleType):
    raise Exception("Unimplemented")
