import re, sys, subprocess, pathlib
H = pathlib.Path(sys.argv[1]); R = pathlib.Path(sys.argv[2])
fresh = (H / "reproduce_output_fresh.txt").read_text()
secs = {}
for m in re.finditer(r"=====SECTION (\d\d)[^\n]*=====\n(.*?)(?=\n=====SECTION|\Z)", fresh, re.S):
    secs[m.group(1)] = m.group(2).rstrip("\n")
check = subprocess.run([str(R / ".venv/bin/python"), str(H / "reproduce/scripts/check_expected.py"), str(H / "reproduce_output_fresh.txt")], capture_output=True, text=True).stdout.rstrip()
def fence(body, lang=""):
    f = "```"
    while f in body: f += "`"
    return f"{f}{lang}\n{body}\n{f}"
def sub(line):
    m = re.fullmatch(r"@@code (\S+) (\d+)-(\d+)(?: (\w+))?@@", line)
    if m:
        rel, a, b, lang = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4) or "python"
        src = (R / rel).read_text().splitlines()
        assert 1 <= a <= b <= len(src), (rel, a, b, len(src))
        rng = f"line {a}" if a == b else f"lines {a}-{b}"
        return fence(f"# {rel}, {rng}\n" + "\n".join(src[a-1:b]), lang)
    m = re.fullmatch(r"@@out (\d\d)@@", line)
    if m: return fence(secs[m.group(1)], "text")
    m = re.fullmatch(r"@@file (\S+) (\w+)@@", line)
    if m: return fence((H / m.group(1)).read_text().rstrip("\n"), m.group(2))
    m = re.fullmatch(r"@@txt (\S+)@@", line)
    if m: return fence((H / m.group(1)).read_text().rstrip("\n"), "text")
    if line == "@@check@@": return fence(check, "text")
    if line == "@@selftest@@": return fence((H / "build" / "selftest.txt").read_text().rstrip("\n") if (H / "build" / "selftest.txt").exists() else "(pending)", "text")
    assert "@@" not in line, line
    return line
for name in ("HANDOFF", "POTENTIAL_BUGS"):
    out = [sub(l) for l in (H / "build" / f"{name}.tmpl.md").read_text().split("\n")]
    (H / f"{name}.md").write_text("\n".join(out))
    print(name, len("\n".join(out).splitlines()), "lines")
