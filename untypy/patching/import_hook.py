import ast
import importlib
from collections import Callable
from importlib.abc import MetaPathFinder
from importlib.machinery import SourceFileLoader
from importlib.util import decode_source

from untypy.patching.ast_transformer import UntypyAstTransformer


def install_import_hook(should_patch_predicate: Callable[[str], bool]):
    import sys

    already_patched = next((f for f in sys.meta_path if isinstance(f, UntypyFinder)), None)
    if already_patched is not None:
        return

    original_finder = next(f for f in sys.meta_path if f.__name__ == 'PathFinder' and hasattr(f, 'find_spec'))
    sys.meta_path.insert(0, UntypyFinder(original_finder, should_patch_predicate))


class UntypyFinder(MetaPathFinder):

    def __init__(self, inner_finder: MetaPathFinder, should_patch_predicate: Callable[[str], bool]):
        self.inner_finder = inner_finder
        self.should_patch_predicate = should_patch_predicate

    def find_spec(self, fullname, path=None, target=None):
        if not self.should_instrument(fullname):
            return None

        inner_spec = self.inner_finder.find_spec(fullname, path, target)
        if inner_spec is not None and isinstance(inner_spec.loader, SourceFileLoader):
            inner_spec.loader = UntypyLoader(inner_spec.loader.name, inner_spec.loader.path)
        return inner_spec

    def should_instrument(self, module_name: str) -> bool:
        return self.should_patch_predicate(module_name)


class UntypyLoader(SourceFileLoader):

    def source_to_code(self, data, path, *, _optimize=-1):
        source = decode_source(data)
        tree = compile(source, path, 'exec', ast.PyCF_ONLY_AST,
                       dont_inherit=True, optimize=_optimize)
        UntypyAstTransformer().visit(tree)
        ast.fix_missing_locations(tree)
        return compile(tree, path, 'exec', dont_inherit=True, optimize=_optimize)

    def exec_module(self, module) -> None:
        # cache_from_source has to be patched to prevent load from cache
        # this enables patching of AST
        # See https://github.com/agronholm/typeguard/blob/89c1478bd33bcf9a7cccc2c962ebeaa034e51908/src/typeguard/importhook.py#L12
        original = getattr(importlib._bootstrap_external, 'cache_from_source')
        try:
            setattr(importlib._bootstrap_external, 'cache_from_source', lambda *args: None)
            return super().exec_module(module)
        finally:
            setattr(importlib._bootstrap_external, 'cache_from_source', original)
