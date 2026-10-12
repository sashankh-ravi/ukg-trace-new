"""Usage: python show_prompts.py [full]  -- list prompts captured by the stand-in model."""
import json, sys, os
if not os.path.exists("prompts.jsonl"): print("   (no prompts captured)"); sys.exit()
for l in open("prompts.jsonl"):
    d = json.loads(l); h = d["messages"][-1]["text"]
    print("   prompt", d["key"], "| model:", d["model_id"], "| reply used:", d["reply_used"], "|", [x for x in h.splitlines() if x.startswith("- Target")][0])
    if len(sys.argv) > 1:
        for m in d["messages"]: print(f"--- {m['role']} message: {len(m['text'])} chars ---")
        print(h[h.index("DOCUMENT TO ANALYZE"):])
