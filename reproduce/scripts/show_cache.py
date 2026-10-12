"""List a run's saved stage outputs: file, save time, start of document 1's text.
Usage: python show_cache.py <cache/run-id dir>"""
import json, glob, sys, os, time
for f in sorted(glob.glob(sys.argv[1] + "/document_*/*.json")):
    t = time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(f)))
    print(f"   {f} | saved at {t} | doc1 text starts: {json.load(open(f))[0]['page_content'][:28]}")
