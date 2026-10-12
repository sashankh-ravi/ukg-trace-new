"""Compare a run_all.sh output file with the values recorded in the original session.
Usage: python check_expected.py <output file>     (exit code 0 = every value found)"""
import sys
t = open(sys.argv[1], encoding="utf-8", errors="replace").read()
EXPECTED = [
 ("commit", "37ef4a7df28bdd19a5f277d30aff026ddf8cbd50"),
 ("run id prefix for a folder named docs", "pipeline-46b42b42-"),
 ("folder fingerprint, 5 original docs", "returned: '70f976b347ba'"),
 ("folder fingerprint, after editing 01_acme.txt", "corpus fingerprint    : 11e583bd8e55"),
 ("parsing output name, original docs", "document_parsing/documents-2e1fc5080839.json"),
 ("loading output name, original docs", "document_loading/documents-76101e2dcda9.json"),
 ("parsing output name, edited docs", "document_parsing/documents-54cf4641e850.json"),
 ("loading output name, edited docs", "document_loading/documents-0842cedc0821.json"),
 ("name the early check looks for, parsing", "key: 'documents-1035b7a62512'"),
 ("name the early check looks for, loading", "key: 'documents-ac616352a4e7'"),
 ("scenario B resumes at loading", "path taken      : RESUME  -> start stage = document_loading"),
 ("scenario D rewinds to parsing", "path taken      : RESUME  -> start stage = document_parsing"),
 ("all-stage constructor stops at chunking", "CHECKPOINT  7: entering TextChunkingStage.__init__"),
 ("force rebuild skips saving", "Cache disabled, skipping output save for stage: 'document_parsing'"),
 ("expiry rewind", "Rewinding resume point from 'document_loading' to 'document_parsing'"),
 ("chunking prompt key, default settings", "prompt 266920b75e"),
 ("chunking prompt key, min 900", "prompt 0b6352c8bf"),
 ("06_profile pre-chunks", "pre-chunks: 2  sizes=[1532, 884]"),
 ("07_review single chunk under defaults", "chunk 1/1  method=llm      chars=2801"),
 ("07_review three chunks with min 900", "chunk 3/3  method=llm      chars=904"),
 ("merge joins with no separator", "renewed.The engineering team"),
 ("threshold change keeps gleaning", "gleaning              6d3b14e6d688   6d3b14e6d688   yes"),
 ("threshold change redoes graph_resolution", "graph_resolution      7d5bce1ee591   cc32ecbec5bb   NO - redo"),
]
bad = 0
# After the resume in section 13, the loading output must still carry run 1's marker.
tail = t.split("saved files after the resume:")[-1].split("=====SECTION")[0]
ok = "document_loading/documents-0842cedc0821.json" in tail and tail.count("MARKER-FROM-FIRST-RUN") == 2
bad += not ok
print(("PASS  " if ok else "FAIL  ") + "resume after force rebuild reuses run 1's marked output (section 13, step 4)")
for label, needle in EXPECTED:
    ok = needle in t; bad += not ok
    print(("PASS  " if ok else "FAIL  ") + label + "  ->  " + needle)
print(f"\n{len(EXPECTED) + 1 - bad}/{len(EXPECTED) + 1} expected values found")
sys.exit(1 if bad else 0)
