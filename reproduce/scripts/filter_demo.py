"""Run the real file-filter conditions of DocumentParsingStage._discover_files on a messy folder.
Usage: python filter_demo.py <empty work dir>"""
import logging, sys; logging.disable(logging.CRITICAL)
from pathlib import Path
from unified_kg_rag.application.ingestion.pipeline_stages import DocumentParsingStage as D
from unified_kg_rag.adapters.ingestion.parser import ParserFactory
base = Path(sys.argv[1]); src = base / "src"
for d in ("sub", "cache/run1", "__pycache__"): (src / d).mkdir(parents=True, exist_ok=True)
for f, t in (("a.txt","hi"),("sub/b.txt","hi"),(".secret.txt","hi"),("notes.docx","hi"),("__pycache__/x.pyc","hi"),
             ("__pycache__/y.txt","hi"),("cache/run1/documents.json","{}"),("real.json","{}")): (src / f).write_text(t + "\n")
ext = ParserFactory.get_supported_extensions(); owned = [(src / "cache").resolve()]
print("supported:", ext); print("owned_dirs: [<abs>/src/cache]")
print(f"{'path':<32}{'is_file':<9}{'ext ok':<8}{'excluded':<10}{'in owned':<10}KEPT")
for f in sorted(src.rglob("*")):
    a = f.is_file(); b = f.suffix.lower() in ext; c = D._should_exclude_file(f)
    d = any(f.resolve().is_relative_to(o) for o in owned)
    print(f"{str(f.relative_to(base)):<32}{str(a):<9}{str(b):<8}{str(c):<10}{str(d):<10}{a and b and not c and not d}")
print("\nis_relative_to demo:")
for x in ["/data/src/cache/run1/documents.json", "/data/src/real.json", "/data/src/cache2/x.json"]:
    print(f"  Path({x!r}).is_relative_to('/data/src/cache') ->", Path(x).is_relative_to("/data/src/cache"))
