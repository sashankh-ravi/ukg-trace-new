#!/usr/bin/env bash
# Re-runs every experiment from the tracing session against a checkout of
# awslabs/unified-kg-rag-on-aws at commit 37ef4a7df28bdd19a5f277d30aff026ddf8cbd50.
#
#   usage:  bash run_all.sh /path/to/unified-kg-rag-on-aws [workdir]
#
# The repo must have its virtualenv built (`uv sync` in the repo root).
# Nothing here needs AWS. The AWS variables below are blanked ON PURPOSE so the
# one step that touches Bedrock code (section 02) cannot reach a real account.
set -u
REPO="$(cd "$1" && pwd)"; HERE="$(cd "$(dirname "$0")" && pwd)"; WORK="${2:-$HERE/work}"
PY="$REPO/.venv/bin/python"; RI="$REPO/.venv/bin/run-ingestion"
[ -x "$PY" ] || { PY="$REPO/.venv/Scripts/python.exe"; RI="$REPO/.venv/Scripts/run-ingestion.exe"; }
unset AWS_PROFILE AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_REGION
export AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null AWS_EC2_METADATA_DISABLED=true AWS_DEFAULT_REGION=us-east-1
export PYTHONWARNINGS=ignore
SC="$HERE/scripts"; STAGES="DOCUMENT_PARSING,DOCUMENT_LOADING"
sec() { echo; echo "=====SECTION $1====="; }
quiet() { grep -v "Warning\|warn(\|it/s\]\|doc/s\]\|Chunking Documents\|Processing:" ; }
cli() { # cli <logname> <stdin: y|none> <args...>
  local log="logs/$1.log" inp="$2"; shift 2
  if [ "$inp" = y ]; then echo y | "$RI" --source-directory docs --enabled-stages $STAGES "$@" > "$log" 2>&1
  else "$RI" --source-directory docs --enabled-stages $STAGES "$@" > "$log" 2>&1 < /dev/null; fi
  echo "exit code: $?"; "$PY" "$SC/logfilter.py" "$log"; }
key() { grep -E "Rewinding|Resume strategy|Executing [0-9]|Cached single|Cache disabled|Force rebuild|Starting new|Using [0-9]|exit code|integrity|Missing cache|Continue despite|unexpected error" ; }

rm -rf "$WORK"; mkdir -p "$WORK/docs" "$WORK/logs"; cd "$WORK"
cp "$HERE"/docs_original/*.txt docs/; cp "$SC"/step*.py "$SC"/fake_llm.py .

sec "00 environment"
git -C "$REPO" rev-parse HEAD; "$PY" --version; grep -n '^__version__' "$REPO/unified_kg_rag/__init__.py"; wc -c docs/*.txt

sec "01 repo map (scripts/graph.py: imports, classes and functions read with Python's ast module)"
python3 -I "$SC/graph.py" "$REPO" 2>/dev/null || "$PY" -I "$SC/graph.py" "$REPO"

sec "02 constructor, all 12 stages enabled, no AWS (step2.py)"
"$PY" step2.py > logs/step2.log 2>&1; echo "exit code: $?"; grep -E "^(---|CHECKPOINT)" logs/step2.log; tail -1 logs/step2.log | cut -c1-400

sec "03 constructor, only parsing + loading enabled (step2b.py)"
"$PY" step2b.py 2>&1 | quiet

sec "04 file filter demo (scripts/filter_demo.py)"
"$PY" "$SC/filter_demo.py" "$WORK/filterdemo" 2>&1 | quiet

sec "05 first run with checkpoints (step3.py)"
rm -rf cache; "$PY" step3.py 2>&1 | quiet
RUN1="$(ls cache | sort | head -1)"; echo "RUN1=$RUN1"

sec "06 pipeline_metadata.json of the first run"
cat "cache/$RUN1/pipeline_metadata.json"

sec "07 rerun scenarios A-D (step4.py; D appends a sentence to docs/01_acme.txt)"
sleep 1; "$PY" step4.py 2>&1 | quiet; echo "run folders now:"; ls cache

sec "08 folder fingerprint recomputed by hand, after the edit (scripts/manifest_demo.py)"
"$PY" "$SC/manifest_demo.py" docs 2>&1 | quiet

sec "09 cache key names with and without the folder fingerprint (scripts/keys_demo.py)"
"$PY" "$SC/keys_demo.py" 11e583bd8e55 2>&1 | quiet; echo "files on disk for RUN1:"; find "cache/$RUN1" -type f | sort

sec "10 real CLI resume of RUN1, nobody at the keyboard (bug 1)"
cli resume_noinput none --pipeline-id "$RUN1"

sec "11 real CLI resume of RUN1, answering y (bug 1 and bug 2)"
cli resume_yes y --pipeline-id "$RUN1"

sec "12 force rebuild on a brand-new run id, then resume it (bug 3)"
cli force_new none --pipeline-id force-test --force-rebuild | key; echo "files:"; find cache/force-test -type f | sort
cli force_new_resume y --pipeline-id force-test | key; echo "files:"; find cache/force-test -type f | sort

sec "13 normal run -> marker -> force rebuild -> resume, same run id (bug 3)"
echo "[1] normal run, id demo-force"; cli df1 none --pipeline-id demo-force | key
"$PY" "$SC/mark_cache.py" cache/demo-force; echo "[2] marker stamped into run 1's saved outputs:"; "$PY" "$SC/show_cache.py" cache/demo-force
sleep 3; echo "[3a] force rebuild, same id, nobody at the keyboard"; cli df2a none --pipeline-id demo-force --force-rebuild | key
echo "[3b] force rebuild, same id, answering y"; cli df2b y --pipeline-id demo-force --force-rebuild | key
echo "    saved files after the force rebuild:"; "$PY" "$SC/show_cache.py" cache/demo-force
sleep 3; echo "[4] resume, same id, no force"; cli df3 y --pipeline-id demo-force | key
echo "    saved files after the resume:"; "$PY" "$SC/show_cache.py" cache/demo-force

sec "14 24-hour expiry (bug 4)"
echo "[1] normal run, id demo-ttl"; cli ttl1 none --pipeline-id demo-ttl | key; "$PY" "$SC/ttl_tools.py" show cache/demo-ttl
echo "[2] resume right away"; cli ttl2 y --pipeline-id demo-ttl | key
echo "[3] expiry dates edited to the past, then resume"; "$PY" "$SC/ttl_tools.py" expire cache/demo-ttl; cli ttl3 y --pipeline-id demo-ttl | key

sec "15 which stage fingerprints change when one late setting changes (scripts/threshold_demo.py)"
"$PY" "$SC/threshold_demo.py" 11e583bd8e55 2>&1 | quiet

sec "16 stage 3, capture pass: 7 documents, stand-in model with no answers yet (step5.py)"
cp "$HERE"/docs_added/*.txt docs/; wc -c docs/*.txt; rm -f answers.json prompts.jsonl
"$PY" step5.py stage3-pass1 2>&1 | quiet; "$PY" "$SC/show_prompts.py" full

sec "17 stage 3, default settings, hand-written answer (new chunks at lines 9 and 17)"
cp "$SC/answers_handwritten.json" answers.json; cat answers.json; echo
"$PY" step5.py stage3-pass2 2>&1 | quiet; "$PY" "$SC/show_prompts.py"

sec "18 stage 3, min_chunk_size lowered to 900, same hand-written answer"
"$PY" step5.py stage3-min900 900 2>&1 | quiet; "$PY" "$SC/show_prompts.py"
echo "one finished text unit (chunk 2 of 07_review.txt):"
"$PY" -c "
import json
u = json.load(open('text_units.json'))[-2]
for k, v in u.items():
    s = repr(v); print(f'  {k:<18} = {s if len(s) < 95 else s[:92] + \"...\"}')"

sec "19 merge function called directly (scripts/merge_demo.py)"
"$PY" "$SC/merge_demo.py" docs/07_review.txt 2>&1 | quiet

sec "20 end"
echo done
