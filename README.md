# Tracing unified-kg-rag-on-aws, step by step

Notes, scripts and findings from learning the open-source repository [awslabs/unified-kg-rag-on-aws](https://github.com/awslabs/unified-kg-rag-on-aws) from zero. The method throughout: find the entry point, follow one function at a time, add checkpoints, run on small made-up data, and record what actually happened.

This is an independent study log. It is not affiliated with or endorsed by AWS or the maintainers of that repository. Everything here was checked against commit `37ef4a7df28bdd19a5f277d30aff026ddf8cbd50` of that repository; line numbers refer to that commit.

## Start here

| File | What it is |
|---|---|
| [`HANDOFF.md`](HANDOFF.md) | The full record: what has been read, what was run, the trace of stages 1 to 5, open questions, corrections. Self-contained: every script and sample document is in its appendices. |
| [`POTENTIAL_BUGS.md`](POTENTIAL_BUGS.md) | The bug tracker. Thirteen entries agreed during the session (1 to 4 and 7 to 15) and two candidates not yet decided (5 and 6). None has been reported to the maintainers. |
| [`SESSION_LOG.md`](SESSION_LOG.md) | The conversation that produced all this: every question asked, quoted exactly, with a short note of what was done and where the result lives. |
| [`chat/TRANSCRIPT.md`](chat/TRANSCRIPT.md) | The full chat, copied from its history: every message and every written reply word for word, with each tool call shortened to one line. |

## Progress

| Stage | Status |
|---|---|
| Entry point, constructor, `run()` | Traced and run |
| Run IDs, resume, the cache | Traced and run |
| 1. Document parsing | Traced and run |
| 2. Document loading | Traced and run |
| 3. Text chunking | Traced and run, with Claude answering the model's prompts by hand |
| 4. Translation | Traced and run, with hand-written Spanish translations |
| 5. Graph extraction | Steps 1 to 4b traced line by line and run: construction, inputs, batch processor (normal and failure paths), reading a reply, turning it into objects. Next: merging across chunks |
| 6 to 12 | Not started |

## How the evidence works

Every claim in `HANDOFF.md` is labelled **[RAN]** (seen in real output, which is included), **[READ]** (from code, which is quoted), **[INFERRED]** or **[NOT CHECKED]**. Code excerpts and program output were copied into the documents by script, not retyped. Sample documents describe a fictional company. No real customer data and no AWS account were used; the scripts block AWS access on purpose.

The model calls were not made to Amazon Bedrock. A stand-in model (`reproduce/scripts/fake_llm.py`) recorded each prompt, Claude wrote the answer by hand, and the answer was fed back. So the answers in this repository are Claude's, not the configured model's.

## Repository layout

| Path | Contents |
|---|---|
| `reproduce/run_all.sh` | Re-runs the stage 1 to 3 experiments against a local checkout of the awslabs repository (about 5 minutes). |
| `reproduce/run_stage5.sh` | Re-runs every stage 5 experiment (about 4 minutes). |
| `reproduce/scripts/` | Every tracing script, the stand-in model, the hand-written answers, and helpers. |
| `reproduce/docs_original/`, `reproduce/docs_added/` | The seven made-up sample documents. |
| `reproduce_output_fresh.txt` | Full output of `run_all.sh` from 11 October 2026. |
| `followup_out/` | Outputs of the scripts run outside `run_all.sh`: stage 3 follow-ups, stage 4, and stage 5 (`stage5_*`, from `run_stage5.sh` on 13 October 2026). |
| `evidence_9oct/` | Logs, captured prompts and the cache folder left by the first session on 9 October 2026. |
| `chat/` | The chat transcript. |
| `build/` | Templates and the script that assembles `HANDOFF.md` and `POTENTIAL_BUGS.md` from code and outputs, the self-extraction test, and `transcript_from_history.py`, which turned saved pages of the chat history into transcript text. |

## Re-running

```bash
git clone https://github.com/awslabs/unified-kg-rag-on-aws.git
cd unified-kg-rag-on-aws && git checkout 37ef4a7df28bdd19a5f277d30aff026ddf8cbd50 && uv sync && cd ..
bash <this repo>/reproduce/run_all.sh unified-kg-rag-on-aws > my_output.txt 2>&1
unified-kg-rag-on-aws/.venv/bin/python <this repo>/reproduce/scripts/check_expected.py my_output.txt
bash <this repo>/reproduce/run_stage5.sh unified-kg-rag-on-aws my_stage5_out
```

`HANDOFF.md` sections 0.5 and 0.6 have the details. It was tested on Linux with Python 3.11.

To rebuild the two documents after changing a template or an output: `python3 build/build.py . <path to the awslabs checkout>`.

## Credits and licence

`HANDOFF.md` and `POTENTIAL_BUGS.md` quote short excerpts of code from [awslabs/unified-kg-rag-on-aws](https://github.com/awslabs/unified-kg-rag-on-aws), Copyright Amazon.com, Inc. or its affiliates, licensed under the Apache License 2.0, with file names and line numbers. No other part of that repository is included here.

The same two files also quote short excerpts from two libraries installed in that repository's environment, with file names and line numbers: [langchain-aws](https://github.com/langchain-ai/langchain-aws) 1.8.0 and [langchain-classic](https://github.com/langchain-ai/langchain) 1.0.8, both Copyright LangChain, Inc., MIT License.

No licence has been chosen yet for the rest of this repository.

The tracing was done with Claude (Anthropic).
