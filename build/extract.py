"""Rebuild the reproduce/ folder from HANDOFF.md alone. Usage: python extract.py HANDOFF.md <out dir>"""
import re, sys, pathlib
t = pathlib.Path(sys.argv[1]).read_text(); out = pathlib.Path(sys.argv[2]); n = 0
for m in re.finditer(r"^`(reproduce/[^`\n]+)`[^\n]*\n\n(`{3,})\w*\n(.*?)\n\2\n", t, re.S | re.M):
    p = out / m.group(1); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(m.group(3) + "\n"); n += 1
print(n, "files written")
