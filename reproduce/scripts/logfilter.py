"""Print a run-ingestion log in readable form: JSON log events as 'LOG: ...', other lines as-is."""
import json, sys
BOX = set("─│╭╮╰╯ █╗╔╝╚═║")
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    line = line.rstrip("\n")
    s = line.strip()
    if s.startswith("{"):
        try: e = json.loads(s)["event"]
        except Exception: continue
        if set(e) <= set("= "): continue
        print("LOG:", e[:240])
    elif s and "Warning" not in s and "warn(" not in s and not set(s) <= BOX and "█" not in s:
        print(s[:200])
