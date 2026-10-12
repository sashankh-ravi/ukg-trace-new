"""Recompute the folder fingerprint by hand: one line per file = path, size, sha256.
Usage: python manifest_demo.py <docs dir>"""
import hashlib, sys
from pathlib import Path
from unified_kg_rag.shared.utils.common import compute_hash
root = Path(sys.argv[1]).resolve(); entries = []
for p in sorted(root.rglob("*")):
    if p.is_file():
        e = f"{p.relative_to(root).as_posix()}\t{p.stat().st_size}\t{hashlib.sha256(p.read_bytes()).hexdigest()}"
        entries.append(e); print("  ", e[:60] + "...")
print("  fingerprint =", compute_hash("\n".join(entries), length=12))
