import ast


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


def _is_untypy_patch_call(node):
    if isinstance(node, ast.Expr):
        node = node.value

    return (isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == 'untypy'
            and node.func.attr == 'enable')


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
