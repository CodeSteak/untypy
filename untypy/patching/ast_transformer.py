import ast
from typing import Callable, List, Optional


class UntypyAstTransformer(ast.NodeTransformer):
    def visit_Module(self, node: ast.Module):
        for i, child in enumerate(node.body):
            if isinstance(child, ast.ImportFrom) and child.module == '__future__':
                continue  # from __future__ import ...
            elif isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant):
                continue  # module docstring
            elif _is_untypy_import(node):
                break
            else:
                node.body.insert(i, ast.Import(names=[ast.alias('untypy', None)]))
                break

        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef):
        node.decorator_list.insert(0, ast.Attribute(ast.Name("untypy", ast.Load()), "patch", ast.Load()))
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.FunctionDef):
        node.decorator_list.insert(0, ast.Attribute(ast.Name("untypy", ast.Load()), "patch", ast.Load()))
        self.generic_visit(node)
        return node

    def visit_Expr(self, node: ast.Expr):
        val = node.value
        if _is_untypy_patch_call(val):
            return ast.Expr(ast.Constant("# untypy.enable()"))
        else:
            self.generic_visit(node)
            return node


class UntypyAstImportTransformer(ast.NodeTransformer):
    def __init__(self, predicate: Callable[[str], bool], module_path: List[str]):
        self.predicate = predicate
        self.module_path = module_path

    def resolve_relative_name(self, name: str, levels: Optional[int]) -> str:
        if levels is None:
            return name
        elif levels == 1:
            return '.'.join(self.module_path + list(name.split('.')))
        else:
            prefix = self.module_path[:-(levels - 1)]
            return '.'.join(prefix + list(name.split('.')))

    def visit_Module(self, node: ast.Module):
        inserts = []
        need_insert_utypy_imp = True
        need_insert_utypy_idx = 0
        for i, child in enumerate(node.body):
            if _is_untypy_import(node):
                need_insert_utypy_imp = False
            elif isinstance(child, ast.ImportFrom) and child.module == '__future__':
                need_insert_utypy_idx += 1
            elif isinstance(child, ast.ImportFrom) and self.predicate(
                    self.resolve_relative_name(child.module, child.level)):
                for alias in child.names:
                    if alias.asname is None:
                        destname = alias.name
                    else:
                        destname = alias.asname
                    # $destname = untypy.wrap_import($destname)
                    call = ast.Call(ast.Attribute(ast.Name("untypy", ast.Load()), "wrap_import", ast.Load()),
                                    [ast.Name(destname, ast.Load())], [])
                    expr = ast.Assign([ast.Name(destname, ast.Store())], call)
                    node.body.insert(i + 1, expr)

            elif isinstance(child, ast.Import):
                for alias in child.names:
                    if self.predicate(alias.name):
                        if alias.asname is None:
                            destname = alias.name
                        else:
                            destname = alias.asname

                        # $destname = untypy.wrap_import($destname)
                        # python ast weirdness
                        def create_attribute(levels: List[str], op=ast.Store()):
                            if len(levels) == 1:
                                return ast.Name(levels[0], ctx=op)
                            else:
                                return ast.Attribute(create_attribute(levels[:-1], ast.Load()), levels[-1], ctx=op)

                        destpath = destname.split(".")
                        call = ast.Call(ast.Attribute(ast.Name("untypy", ast.Load()), "wrap_import", ast.Load()),
                                        [create_attribute(destpath, ast.Load())], [])
                        expr = ast.Assign([create_attribute(destpath)], call)
                        # inserts.append((i + 1, expr)) # insert after
                        node.body.insert(i + 1, expr)

        # TODO BUG: Multiple imports index mix up
        # TODO BUG:
        for (idx, expr) in inserts:
            node.body.insert(idx, expr)

        if need_insert_utypy_imp:
            node.body.insert(need_insert_utypy_idx, ast.Import(names=[ast.alias('untypy', None)]))

        self.generic_visit(node)
        return node

    def visit_Expr(self, node: ast.Expr):
        val = node.value
        if _is_untypy_patch_call(val):
            return ast.Expr(ast.Constant("# untypy.enable()"))
        else:
            self.generic_visit(node)
            return node

def _is_untypy_patch_call(node):
    if isinstance(node, ast.Expr):
        node = node.value

    return (isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == 'untypy'
            and (node.func.attr == 'enable' or node.func.attr == 'enable_on_imports'))


def _is_untypy_import(node):
    return (isinstance(node, ast.Import)
            and len(node.names) == 1
            and isinstance(node.names[0], ast.alias)
            and node.names[0].name == 'untypy')


def did_no_code_run_before_untypy_enable(node: ast.Module) -> bool:
    for child in node.body:
        if isinstance(child, ast.ImportFrom) and child.module == '__future__':
            continue  # from __future__ import ...
        elif _is_untypy_import(child):
            continue
        elif isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant):
            continue  # module docstring
        elif _is_untypy_patch_call(child):
            return True
        else:
            break

    # untypy.enable() was not first. It is still okay if this call does not exist.
    class DidNoCodeRunVisitor(ast.NodeVisitor):
        def __init__(self):
            self.has_untypycall = False

        def visit_Call(self, node):
            if _is_untypy_patch_call(node):
                self.has_untypycall = True
            self.generic_visit(node)
            return node

    visitor = DidNoCodeRunVisitor()
    visitor.visit(node)
    if visitor.has_untypycall:
        return False
    else:
        return True
