import ast
import copy

from scanner.finding import Finding

LEAF_STATEMENTS = (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Expr, ast.Return)


def build_alias_map(tree):
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                if item.asname:
                    aliases[item.asname] = item.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for item in node.names:
                local = item.asname or item.name
                aliases[local] = f"{node.module}.{item.name}"
    return aliases


class AliasResolver(ast.NodeTransformer):
    def __init__(self, aliases):
        self.aliases = aliases

    def visit_Name(self, node):
        if node.id in self.aliases:
            return ast.parse(self.aliases[node.id], mode="eval").body
        return node


def scan_file_ast(path, rules):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    resolver = AliasResolver(build_alias_map(tree))
    findings = []

    for node in ast.walk(tree):
        if not isinstance(node, LEAF_STATEMENTS):
            continue
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            continue  # skip docstrings

        text = ast.unparse(resolver.visit(copy.deepcopy(node)))

        for rule in rules:
            match = rule.regex.search(text)
            if match:
                findings.append(Finding(
                    file=str(path),
                    line=node.lineno,
                    matched_text=match.group(0),
                    algorithm=rule.algorithm,
                    category=rule.category,
                    status=rule.status,
                    replacement=rule.replacement,
                ))
    return findings