import inspect
import sys
from .patching import patch_module

from types import ModuleType
from typing import Optional


def enable(recursive: bool = True, root : Optional[ModuleType] = None) -> None:
    if root is None:
        root = _find_calling_module()
    if root is None:
        raise Exception("Couldn't find loading Module. This is a Bug")

    patch_module(root)

    if recursive:
        for module_name in sys.modules:
            if module_name.startswith(root.__name__ + "."):
                patch_module(sys.modules[module_name])


def _find_calling_module() -> Optional[ModuleType]:
    for caller in inspect.stack():
        if caller.filename != __file__:
            mod = inspect.getmodule(caller.frame)
            if mod is not None:
                return mod
    return None
