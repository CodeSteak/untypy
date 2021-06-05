import ast
import inspect
import sys
from types import ModuleType
from typing import Optional, Any

from .patching import patch_function, patch_class
from .patching.ast_transformer import UntypyAstTransformer, did_no_code_run_before_untypy_enable
from .patching.import_hook import install_import_hook


# def enable(recursive: bool = True, root: Optional[ModuleType] = None) -> None:
#     if root is None:
#         root = _find_calling_module()
#     if root is None:
#         raise Exception("Couldn't find loading Module. This is a Bug")
#
#     patch_module(root)
#
#     if recursive:
#         for module_name in sys.modules:
#             if module_name.startswith(root.__name__ + "."):
#                 patch_module(sys.modules[module_name])

def enable(recursive: bool = True, root: Optional[ModuleType] = None) -> None:
    caller = _find_calling_module()
    exit_after = False

    if root is None:
        root = caller
        exit_after = True
    if caller is None:
        raise Exception("Couldn't find loading Module. This is a Bug")

    def predicate(module_name):
        if recursive:
            # Patch if Submodule
            return module_name.startswith(root.__name__ + ".")
        else:
            raise AssertionError("You cannot run 'untypy.enable()' twice!")

    install_import_hook(predicate)
    _exec_module_patched(root, exit_after)


def _exec_module_patched(mod: ModuleType, exit_after: bool):
    source = inspect.getsource(mod)
    tree = compile(source, mod.__file__, 'exec', ast.PyCF_ONLY_AST,
                   dont_inherit=True, optimize=-1)

    if not did_no_code_run_before_untypy_enable(tree):
        raise AssertionError("Please put 'untypy.enable()' at the start of your module like so:\n"
                             "\timport untypy\n"
                             "\tuntypy.enable()")

    UntypyAstTransformer().visit(tree)
    ast.fix_missing_locations(tree)
    patched_mod = compile(tree, mod.__file__, 'exec', dont_inherit=True, optimize=-1)
    stack = list(map(lambda s: s.frame, inspect.stack()))
    try:
        exec(patched_mod, mod.__dict__)
    except Exception as e:
        while e.__traceback__.tb_frame in stack:
            e.__traceback__ = e.__traceback__.tb_next
        sys.excepthook(type(e), e, e.__traceback__)
        if exit_after: sys.exit(-1)
    if exit_after: sys.exit(0)


def _find_calling_module() -> Optional[ModuleType]:
    for caller in inspect.stack():
        if caller.filename != __file__:
            mod = inspect.getmodule(caller.frame)
            if mod is not None:
                return mod
    return None


def patch(a: Any) -> Any:
    if inspect.isfunction(a):
        return patch_function(a)
    elif inspect.isclass(a):
        return patch_class(a)
    else:
        return a
