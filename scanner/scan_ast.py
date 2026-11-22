import ast
import copy

from scanner.finding import Finding

# fields that hold nested statements; everything else on a compound
# statement (the condition, the iterable, the decorators...) is its header
BODY_FIELDS = ("body", "orelse", "finalbody", "handlers", "cases")

# calls that only print or log text; string arguments there are messages,
# not crypto being used
OUTPUT_METHODS = {"debug", "info", "warning", "warn", "error",
                  "critical", "exception", "log"}


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


def imported_names(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                names.add(item.asname or item.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for item in node.names:
                names.add(item.asname or item.name)
    return names


def bound_names(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    return names


def instance_map(tree, aliases):
    """Variables assigned from a directly imported class, like
    `ph = PasswordHasher()`, mapped to the class's full name. A later
    call such as `ph.hash(...)` can then be matched as
    `argon2.PasswordHasher.hash(...)` even though the algorithm name is
    not on that line."""
    instances = {}
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id in aliases):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    instances[target.id] = aliases[node.value.func.id]
    return instances


def is_output_call(call):
    func = call.func
    if isinstance(func, ast.Name):
        return func.id == "print"
    if isinstance(func, ast.Attribute):
        return func.attr in OUTPUT_METHODS
    return False


class AliasResolver(ast.NodeTransformer):
    def __init__(self, aliases, local_names, instances=None):
        self.aliases = aliases
        self.local_names = local_names
        self.instances = instances or {}

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id in self.instances:
            node.value = ast.parse(self.instances[node.value.id], mode="eval").body
            return node
        return self.generic_visit(node)

    def visit_Name(self, node):
        if node.id in self.aliases:
            return ast.parse(self.aliases[node.id], mode="eval").body
        if node.id in self.local_names:
            # a name the file defines itself and never imports (like
            # `hashlib = Tester()`) is not the library, so break the match
            return ast.copy_location(ast.Name(id=node.id + "_", ctx=node.ctx), node)
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        if is_output_call(node):
            node.args = [
                ast.Constant(value="")
                if isinstance(arg, ast.JoinedStr)
                or (isinstance(arg, ast.Constant) and isinstance(arg.value, str))
                else arg
                for arg in node.args
            ]
        return node


def statement_parts(node):
    """A simple statement is scanned whole. A compound statement (if, for,
    with, def, class, except...) contributes only its header, because the
    statements inside it are visited on their own."""
    if not any(hasattr(node, field) for field in BODY_FIELDS):
        return [node]
    parts = []
    for name, value in ast.iter_fields(node):
        if name in BODY_FIELDS:
            continue
        for item in (value if isinstance(value, list) else [value]):
            if isinstance(item, ast.AST):
                parts.append(item)
    return parts


def scan_file_ast(path, rules):
    """Returns a list of findings, or None if the file is not valid Python."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    local_names = bound_names(tree) - imported_names(tree)
    aliases = build_alias_map(tree)
    resolver = AliasResolver(aliases, local_names, instance_map(tree, aliases))
    findings = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.stmt, ast.excepthandler)):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue  # an import is not a use; the call site is reported
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            continue  # skip docstrings

        for part in statement_parts(node):
            text = ast.unparse(resolver.visit(copy.deepcopy(part)))
            line = getattr(part, "lineno", node.lineno)
            for rule in rules:
                match = rule.regex.search(text)
                if match:
                    findings.append(Finding(
                        file=str(path),
                        line=line,
                        matched_text=match.group(0),
                        algorithm=rule.algorithm,
                        category=rule.category,
                        status=rule.status,
                        replacement=rule.replacement,
                    ))
    return findings