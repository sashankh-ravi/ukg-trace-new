"""Stamp MARKER-FROM-FIRST-RUN into the first document of every saved stage output of a run.
Usage: python mark_cache.py <cache/run-id dir>"""
import json, glob, sys
for f in sorted(glob.glob(sys.argv[1] + "/document_*/*.json")):
    d = json.load(open(f)); d[0]["page_content"] = "MARKER-FROM-FIRST-RUN " + d[0]["page_content"]
    json.dump(d, open(f, "w"), indent=2)
