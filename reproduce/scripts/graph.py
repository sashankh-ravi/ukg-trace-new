import ast, pathlib, sys, collections
root = pathlib.Path(sys.argv[1])
pkg = root / "unified_kg_rag"
mods = {}
for p in sorted(pkg.rglob("*.py")):
    name = ".".join(p.relative_to(root).with_suffix("").parts)
    if name.endswith(".__init__"): name = name[:-9]
    mods[name] = p
edges = collections.defaultdict(set)
stats = {}
for name, p in mods.items():
    tree = ast.parse(p.read_text())
    classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
    funcs = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    stats[name] = (len(p.read_text().splitlines()), classes, funcs)
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.level == 0 and n.module.startswith("unified_kg_rag"):
            edges[name].add(n.module)
        elif isinstance(n, ast.ImportFrom) and n.level > 0:
            base = name.split(".")
            if not p.name == "__init__.py": base = base[:-1]
            base = base[: len(base) - (n.level - 1)]
            edges[name].add(".".join(base + ([n.module] if n.module else [])))
layer = lambda m: m.split(".")[1] if "." in m else "root"
lc = collections.Counter()
for a, bs in edges.items():
    for b in bs:
        if layer(a) != layer(b): lc[(layer(a), layer(b))] += 1
print("LAYER EDGES (importer -> imported: count)")
for (a, b), c in sorted(lc.items()): print(f"  {a:14s} -> {b:14s} {c}")
print("\nLINES PER LAYER")
ll = collections.Counter()
for m, (n, _, _) in stats.items(): ll[layer(m)] += n
for k, v in ll.most_common(): print(f"  {k:14s} {v}")
print("\nMODULES (lines | classes | top-level funcs)")
for m, (n, c, f) in stats.items():
    if n > 5: print(f"{m.replace('unified_kg_rag.','')} | {n} | {','.join(c)} | {','.join(f)}")
