"""Usage: python ttl_tools.py show|expire <cache/run-id dir>"""
import json, sys
p = sys.argv[2] + "/cache_index.json"; i = json.load(open(p))
if sys.argv[1] == "show":
    for k, e in i["entries"].items(): print("   entry", k, "| created", e["created_at"][:19], "| expires", e["expires_at"][:19])
else:
    for e in i["entries"].values(): e["expires_at"] = "2000-01-01T00:00:00"
    json.dump(i, open(p, "w"), indent=2); print("   expiry of every entry set to 2000-01-01")
