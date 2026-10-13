#!/usr/bin/env bash
# Re-runs every stage 5 (graph extraction) experiment from the tracing session, in order, against a
# checkout of awslabs/unified-kg-rag-on-aws at commit 37ef4a7df28bdd19a5f277d30aff026ddf8cbd50.
#
#   usage:  bash run_stage5.sh /path/to/unified-kg-rag-on-aws OUTPUT_DIR [workdir]
#
# Every program output is written to OUTPUT_DIR as stage5_*.out (plus a few small extracts).
# Nothing here needs AWS; the AWS variables are blanked on purpose, as in run_all.sh. The model is the
# stand-in in scripts/fake_llm.py: it records each prompt and replies from answers.json.
# Takes about 4 minutes.
set -u
REPO="$(cd "$1" && pwd)"; HERE="$(cd "$(dirname "$0")" && pwd)"; mkdir -p "$2"; OUT="$(cd "$2" && pwd)"
WORK="${3:-$HERE/work_stage5}"
PY="$REPO/.venv/bin/python"; [ -x "$PY" ] || PY="$REPO/.venv/Scripts/python.exe"
unset AWS_PROFILE AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_REGION
export AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null AWS_EC2_METADATA_DISABLED=true AWS_DEFAULT_REGION=us-east-1
export PYTHONWARNINGS=ignore
SC="$HERE/scripts"
quiet() { grep -v "Warning\|warn(\|it/s\]\|doc/s\]\|Chunking Documents\|Processing:\|Sequential Processing\|Graph Extraction" ; }
run() { local name="$1"; shift; "$PY" "$@" 2>&1 | quiet > "$OUT/$name.out"; echo "$name: $(wc -l < "$OUT/$name.out") lines"; }

# The five documents used from stage 4 on: the original five, with the sentence that scenario D of
# step4.py appends to 01_acme.txt.
rm -rf "$WORK"; mkdir -p "$WORK/docs5"; cd "$WORK"
cp "$HERE"/docs_original/0[1-5]_*.txt docs5/
printf 'Acme has 120 employees.\n' >> docs5/01_acme.txt
cp "$SC"/fake_llm.py "$SC"/linetrace.py "$SC"/stage5*.py "$SC"/make_answers5.py .

echo "== environment"; git -C "$REPO" rev-parse HEAD; "$PY" --version

echo "== Claude's hand-written answers to the five extraction prompts"
python3 -I make_answers5.py
cmp answers_stage5.json "$SC/answers_stage5.json" && echo "answers_stage5.json identical to the copy in scripts/"

echo "== run A: no answers on file (the stand-in replies with its placeholder)"
rm -f answers.json prompts.jsonl; run stage5_A_capture stage5.py capture
cp prompts.jsonl "$OUT/stage5_A_prompts.jsonl"
"$PY" -I -c "
import json
d = json.loads(open('prompts.jsonl').readline())
open('$OUT/stage5_prompt_system.txt', 'w').write(d['messages'][0]['text'])
open('$OUT/stage5_prompt_human.txt', 'w').write(d['messages'][1]['text'])"

echo "== run B: Claude's answers"
cp answers_stage5.json answers.json; rm -f prompts.jsonl; run stage5_B_answered stage5.py answered

echo "== step 1: construction"
run stage5_step1_build stage5_step1_build.py
run stage5_step1b_inside_setup stage5_step1b_inside_setup.py
echo "== step 2: stage start to hand-over"
run stage5_step2_inputs stage5_step2_inputs.py
echo "== step 3a: batch processor, normal path"
run stage5_step3a_batch stage5_step3a_batch.py
echo "== step 3b: batch processor, failure paths"
for m in throttle-once denied-always throttle-always hang-once; do run "stage5_step3b_$m" stage5_step3b_failures.py "$m"; done
IGNORE_ERRORS=off run stage5_step3b_ignore_off stage5_step3b_failures.py denied-always
IGNORE_ERRORS=on  run stage5_step3b_ignore_on  stage5_step3b_failures.py denied-always
echo "== step 4a: reading a reply"
for part in real cut prose; do run "stage5_step4a_$part" stage5_step4a_reader.py "$part"; done
cp answers_stage5.json answers.json     # the prose run rewrote answers.json
echo "== step 4b: from reply to objects"
for part in main entity relationship edge; do run "stage5_step4b_$part" stage5_step4b_parse.py "$part"; done

echo "== small extracts used as evidence in POTENTIAL_BUGS.md (cut from the outputs above, not retyped)"
for v in off on; do
  { grep "ignore_errors =" "$OUT/stage5_step3b_ignore_$v.out"; sed -n '/SUMMARY/,$p' "$OUT/stage5_step3b_ignore_$v.out"; } \
    > "$OUT/stage5_bug11_ignore_${v}_summary.txt"
done
{ sed -n '1,/^$/p' "$OUT/stage5_step4a_cut.out"; sed -n '/^RESULT/,$p' "$OUT/stage5_step4a_cut.out"; } > "$OUT/stage5_bug12_cut_summary.txt"
{ sed -n '1p' "$OUT/stage5_step4a_prose.out"; sed -n '/^model calls recorded/,/^  call 6/p' "$OUT/stage5_step4a_prose.out"
  grep "^does it contain\|^stage 5:" "$OUT/stage5_step4a_prose.out"; } > "$OUT/stage5_bug13_repair_summary.txt"
sed -n '/=== the repair prompt, in full/,/=== end ===/p' "$OUT/stage5_step4a_prose.out" > "$OUT/stage5_bug13_repair_prompt.txt"
ls "$OUT"/stage5_bug*
echo "== done"
