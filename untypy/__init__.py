import ast
import inspect
import sys
from types import ModuleType
from typing import Optional, Any

from .patching import wrap_function, patch_class, wrap_class, DefaultConfig
from .patching.ast_transformer import UntypyAstTransformer, did_no_code_run_before_untypy_enable, \
    UntypyAstImportTransformer
from .patching.import_hook import install_import_hook

GlobalConfig = DefaultConfig


def enable(*, recursive: bool = True, root: Optional[ModuleType] = None) -> None:
    global GlobalConfig
    caller = _find_calling_module()
    exit_after = False

    if root is None:
        root = caller
        exit_after = True
    if caller is None:
        raise Exception("Couldn't find loading Module. This is a Bug")

    GlobalConfig = DefaultConfig._replace(checkedprefixes=[root.__name__])

    def predicate(module_name):
        if recursive:
            # Patch if Submodule
            return module_name.startswith(root.__name__ + ".")
        else:
            raise AssertionError("You cannot run 'untypy.enable()' twice!")

    transformer = lambda path: UntypyAstTransformer()
    install_import_hook(predicate, transformer)
    _exec_module_patched(root, exit_after, transformer(caller.__name__.split(".")))


def enable_on_imports(*prefixes):
    global GlobalConfig
    GlobalConfig = DefaultConfig._replace(checkedprefixes=[*prefixes])
    caller = _find_calling_module()

    def predicate(module_name: str):
        module_name = module_name.replace('__main__.', '')
        for p in prefixes:
            if module_name == p:
                return True
            elif module_name.startswith(p + "."):
                return True
            else:
                return False

    transformer = lambda path: UntypyAstImportTransformer(predicate, path)
    install_import_hook(predicate, transformer)
    _exec_module_patched(caller, True, transformer(caller.__name__.split(".")))


def _exec_module_patched(mod: ModuleType, exit_after: bool, transformer: ast.NodeTransformer):
    source = inspect.getsource(mod)
    tree = compile(source, mod.__file__, 'exec', ast.PyCF_ONLY_AST,
                   dont_inherit=True, optimize=-1)

    if not did_no_code_run_before_untypy_enable(tree):
        raise AssertionError("Please put 'untypy.enable()' at the start of your module like so:\n"
                             "\timport untypy\n"
                             "\tuntypy.enable()")

    transformer.visit(tree)
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
    global GlobalConfig
    if inspect.isfunction(a):
        return wrap_function(a, GlobalConfig)
    elif inspect.isclass(a):
        patch_class(a, GlobalConfig)
        return a
    else:
        return a


def wrap_import(a: Any) -> Any:
    global GlobalConfig
    if inspect.isfunction(a):
        return wrap_function(a, GlobalConfig)
    elif inspect.isclass(a) or inspect.ismodule(a):
        return wrap_class(a, GlobalConfig)
    else:
        return a
