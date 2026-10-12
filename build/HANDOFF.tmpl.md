# Handoff: tracing `awslabs/unified-kg-rag-on-aws` step by step

Written 11 October 2026 and updated 12 October 2026, to continue on another machine a tracing session that ran from 9 to 12 October 2026.

This file is the complete record of that session: what was read, what was run, what was found, and what is still unknown. It is written to be read by an AI coding assistant (Claude Code) and by the person doing the tracing.

---

## 0. Read this first

### 0.1 What the person wants

They are learning this repository from zero and want to understand it "inside out". Their stated method, which the next session must keep:

- Work the way a person would without AI: find the entry point, follow one function at a time, put checkpoints in, run on small made-up data, and look at what actually happened.
- Take one small step per turn. No long essays. Stop after each step so they can ask questions.
- Zero invented facts. Every claim needs either a file and line number, or the output of something that was actually run.
- Plain language. They asked for explanations with less jargon.
- When a possible bug turns up, discuss it, and add it to the running bug log only when they say so.

### 0.2 Evidence labels used in this file

Every non-trivial claim carries one of these:

| Label | Meaning |
|---|---|
| **[RAN]** | Observed in the output of code that was executed. The output is in this file. |
| **[READ]** | Taken from source code that was read. The lines are quoted in this file. |
| **[INFERRED]** | A conclusion drawn from code that was read, but never executed. Treat as a hypothesis. |
| **[NOT CHECKED]** | Known gap. Nobody has looked. |

### 0.3 How this file was put together, and how far to trust it

- **Code excerpts** were copied out of the repository by a script, by file name and line range, at commit `37ef4a7df28bdd19a5f277d30aff026ddf8cbd50`. They were not retyped. Each excerpt's first line names its file and lines.
- **Program output** was copied in by a script from one complete re-run of every experiment, done on 11 October 2026 in a clean folder (`reproduce_output_fresh.txt` in this bundle). It was not retyped.
- **The narrative between them** was written by Claude from the session. It can contain mistakes. Where narrative and excerpt disagree, the excerpt wins.
- The 11 October re-run produced the same fingerprints, file names, prompt keys and chunk sizes as the 9 October session. A checker script compared 24 recorded values and found all 24 (Appendix F). Run IDs and clock times differ between the two days, because run IDs contain the time.
- Section 12 lists statements made during the 9 October session that turned out to be imprecise or incomplete. Read it.

### 0.4 What is in this bundle

| Path | What it is |
|---|---|
| `HANDOFF.md` | This file. |
| `POTENTIAL_BUGS.md` | The running bug log: the four entries agreed with the person, plus two candidates not yet approved. |
| `reproduce/run_all.sh` | Re-runs every experiment from scratch against a checkout of the repo. |
| `reproduce/scripts/` | The tracing scripts used in the session, plus small helpers. |
| `reproduce/docs_original/` | The five made-up source documents, as first written. |
| `reproduce/docs_added/` | Two longer made-up documents added for stage 3. |
| `reproduce_output_fresh.txt` | Full output of `run_all.sh` from 11 October 2026. |
| `evidence_9oct/` | Files left on disk by the 9 October session: logs, captured prompts, the cache folder. |

All sample documents are invented. They describe a fictional company. Nothing in the bundle comes from a real customer or a real AWS account.

### 0.5 Using this file on its own, without the rest of the bundle

This file contains every file needed to re-run the experiments. If only `HANDOFF.md` and `POTENTIAL_BUGS.md` were carried over, rebuild the `reproduce/` folder from the appendices:

- Appendix B holds `reproduce/run_all.sh`, the five `step*.py` scripts, `fake_llm.py` and `answers_handwritten.json`.
- Appendix E holds the seven sample documents.
- Appendix G holds the helper scripts.

Rules for rebuilding, so that the results match:

1. Each file is introduced by a line that starts with its path in backticks, followed by a fenced block. Save the block's contents to that path, relative to a new folder of your choice.
2. Every file must end with exactly one newline character after the last line shown. This matters for the sample documents: the folder fingerprint is computed from each file's size and bytes, so a missing or extra newline changes every fingerprint and saved file name recorded in this file. The original five documents are 110, 117, 124, 125 and 115 bytes; the two added ones are 2,414 and 2,804 bytes.
3. Use Unix line endings (LF), not Windows ones (CRLF), for the same reason.
4. Then follow section 0.6.

This rebuild was tested on 11 October 2026: a script extracted every file from this document by those rules and compared the result with the original folder, byte for byte (Appendix H).

Not contained in this file: the `evidence_9oct/` folder (logs and cache left by the first session) and `reproduce_output_fresh.txt`. Neither is needed to re-run anything, and the relevant parts of the fresh output are quoted throughout this file.

### 0.6 Setting up on the new machine

1. Clone the repository and check out the exact commit, so the line numbers in this file match:
   ```bash
   git clone https://github.com/awslabs/unified-kg-rag-on-aws.git
   cd unified-kg-rag-on-aws
   git checkout 37ef4a7df28bdd19a5f277d30aff026ddf8cbd50
   uv sync
   ```
   **[RAN]** `uv sync` built a virtual environment with Python 3.11.17 in the session. **[READ]** `pyproject.toml` line 11 requires Python `>=3.10, <3.13`.
2. Re-run everything and check it:
   ```bash
   bash /path/to/bundle/reproduce/run_all.sh /path/to/unified-kg-rag-on-aws > my_output.txt 2>&1
   /path/to/unified-kg-rag-on-aws/.venv/bin/python /path/to/bundle/reproduce/scripts/check_expected.py my_output.txt
   ```
   The whole run took about 5 minutes in the session.
3. `run_all.sh` is a bash script. On Windows it needs Git Bash or WSL. It looks for the interpreter at `.venv/bin/python` and falls back to `.venv/Scripts/python.exe`; the fallback has **[NOT CHECKED]** status, since the session ran on Linux only.

**AWS safety.** Nothing in the kit needs AWS. `run_all.sh` deliberately blanks the AWS environment variables and points the AWS config files at `/dev/null`, so that the one step that exercises Bedrock code (section 4.3, the constructor with all 12 stages) cannot reach a real account from a machine that has credentials. **[INFERRED]** On a machine with working AWS credentials and those blanking lines removed, that step would behave differently from what is recorded here.

---

## 1. Where things stand

| # | Step | Status |
|---|---|---|
| 1 | Map of the repo and the entry points | Done |
| 2 | How `DataIngestionPipeline` is constructed | Done, run with checkpoints |
| 3 | `pipeline.run()` on 5 documents, stages 1 and 2 | Done, run with checkpoints |
| 4 | The file filter in stage 1 | Done, run on a test folder |
| 5 | Run IDs, reruns and resume (scenarios A to D) | Done, run |
| 6 | The cache: file names, fingerprints, expiry, force rebuild | Done, run |
| 7 | Stage 3, text chunking, with Claude answering the model's prompt by hand | Done, run |
| 7b | Follow-up questions on stage 3: size checks, overlap, wrong or invented model replies | Done, run (section 8.6) |
| 8 | Stage 4, translation | Done, run with checkpoints and hand-written Spanish translations (section 9.1) |
| 9 | Stage 5, graph extraction | **In progress** (12 October). Steps 1 to 3 traced line by line: construction, inputs, batch processor normal and failure paths. Outputs in `followup_out/stage5_*.out`; not yet written up in this file. **Next:** step 4, reading each reply (XML reader, repair model, `_parse_extraction_result`). |
| 9b | Stages 6 to 12 | Not started. |
| 10 | The other four commands (`run-rag`, `run-eval`, `run-visualization`, `run-prompt-tuning`) | Not started. |

Open with the person: should the "merged pieces lose the gap between them" finding (candidate 5 in `POTENTIAL_BUGS.md`) be added to the bug log? They had not answered. Candidate 6 has not been shown to them. Bug 7 was approved and added on 11 October. Three stage 4 findings (bugs 8, 9 and 10) were shown to them on 12 October and approved and added the same day. Bug 11 (stage 5) was approved and added on 12 October.

---

## 2. Exactly what has been read

The person asked at the start for the whole repository to be read before any explanation. That did not happen, and they were told so. The approach taken was: build a mechanical map of every module, then read each file in full just before explaining it.

**Read in full [READ]:**

- `README.md`
- `CLAUDE.md` (the repo's own guide for AI assistants: layers, conventions, git rules)
- `unified_kg_rag/application/cli/run_ingestion_pipeline.py` (443 lines)
- `unified_kg_rag/application/ingestion/pipeline.py` (996 lines)
- `unified_kg_rag/adapters/providers.py` (163 lines)
- `unified_kg_rag/shared/config.py` (192 lines)
- `unified_kg_rag/shared/utils/cache_keys.py` (306 lines)
- `unified_kg_rag/adapters/ingestion/parser.py` (260 lines)
- `unified_kg_rag/shared/pipeline_manager.py` (702 lines)
- `unified_kg_rag/shared/cache_manager.py` (467 lines)
- `unified_kg_rag/adapters/ingestion/chunker.py` (992 lines)
- `unified_kg_rag/adapters/aws/chain_factory.py` (316 lines)
- `unified_kg_rag/ports/model_factory.py` (76 lines)
- `unified_kg_rag/shared/utils/langchain.py` (873 lines)
- `unified_kg_rag/domain/prompts/base.py` (138 lines)
- `docker/entrypoint.sh`

**Read in part [READ]:**

- `unified_kg_rag/application/ingestion/pipeline_stages.py`: lines 1 to 760 of 1,639. This covers the stage base class and the parsing, loading, chunking and translation stages. The eight later stage classes (from line 758) have **not** been read.
- `unified_kg_rag/domain/prompts/data_processing.py`: lines 1 to 130 (the chunking prompt).
- `unified_kg_rag/domain/models/config.py`: only the pieces found by searching (chunking, translation, fixing, cache TTL, stage list, a few processing fields). The file is 2,702 lines.
- `unified_kg_rag/domain/models/cache.py`: the `is_expired` property only.
- `unified_kg_rag/shared/utils/common.py`: `compute_hash` only.
- `pyproject.toml`: lines 1 to 140.

**Not read at all [NOT CHECKED]:** everything else. That is about 36,000 of the package's 43,812 lines, including every later-stage adapter (`graph_extractor.py`, `gleaner.py`, `community_detector.py`, the indexers), all of retrieval and search, evaluation, visualization, the infrastructure code under `iac/`, the tests, and the two design documents under `docs/`.

A map of every module (line count, class names, top-level function names, and which layer imports which) was produced by `reproduce/scripts/graph.py`, which reads the source with Python's `ast` module and runs nothing from the repo. Its output is in Appendix A. That map says what exists. It says nothing about what the code does.

---

## 3. The repository in brief

**Purpose [READ, `README.md`].** A framework that turns a folder of documents into a knowledge graph stored on AWS (Amazon Neptune and Amazon OpenSearch) and answers questions over it with Amazon Bedrock models. It reimplements two published methods, Microsoft GraphRAG and LightRAG, on one shared stack.

**Version and size [RAN].**

@@out 00@@

The package is 43,812 lines of Python. Lines per top-level folder, from the map in Appendix A:

| Folder | Lines | Role, as described in the repo's `CLAUDE.md` |
|---|---|---|
| `adapters/` | 19,698 | Code bound to a technology: AWS services, models, file loaders |
| `domain/` | 9,540 | Data models, prompts, and algorithms with no AWS or LangChain imports |
| `application/` | 7,226 | Orchestration and the command-line entry points |
| `shared/` | 3,941 | Config, logging, exceptions, cache and pipeline managers, utilities |
| `evaluation/` | 2,012 | Evaluators and their manager |
| `visualization/` | 803 | Rendering of an exported graph |
| `ports/` | 582 | Abstract interfaces that storage and model backends implement |

**Entry points [READ].** There are five commands, each with its own `main()`:

@@code pyproject.toml 92-97 toml@@

The session traced only the first one, `run-ingestion`.

---

## 4. Trace of `run-ingestion`

### 4.1 The front door

`main()` builds the argument parser, parses the flags, builds a runner, and calls `runner.run()`. It turns three kinds of failure into exit codes.

@@code unified_kg_rag/application/cli/run_ingestion_pipeline.py 425-439@@

The runner's constructor loads the config and checks the flags:

@@code unified_kg_rag/application/cli/run_ingestion_pipeline.py 148-196@@

The flag checks, in order **[READ]**: a source folder is required unless this is a metadata-only operation; the source folder must exist; `--s3-sync` needs `--s3-bucket-name`; `--resume-from-stage` needs `--pipeline-id`; metadata operations need `--pipeline-id`. The cache folder defaults to `cache` relative to the current directory and is created if missing.

`runner.run()` then builds the pipeline object, runs the two optional metadata operations, runs an integrity check, and finally calls `pipeline.run()`:

@@code unified_kg_rag/application/cli/run_ingestion_pipeline.py 370-422@@

Note the order of lines 377, 390 and 393. It matters for bug 1.

The runner translates flags into a `PipelineConfig`. Line 268 matters for bug 3:

@@code unified_kg_rag/application/cli/run_ingestion_pipeline.py 242-276@@

### 4.2 The 12 stages

**[READ]** The stage order is fixed by this dictionary:

@@code unified_kg_rag/application/ingestion/pipeline.py 64-109@@

**[RAN]** With no config file, these are the relevant defaults (printed by `step2b.py`, section 4.3): gleaning enabled, claim extraction disabled, community detection enabled, DynamoDB disabled.

**[INFERRED]** A default run with AWS access would therefore build 10 stages, since the two claim stages are switched off by lines 238 to 244 below. This was never run.

### 4.3 Constructing `DataIngestionPipeline`

@@code unified_kg_rag/application/ingestion/pipeline.py 124-165@@

What the constructor does **[READ]**:

1. Stores the config and the source folder.
2. Gets a `Providers` object. `Providers` holds the AWS session and the model factories, and builds each one only on first use (`adapters/providers.py`, lines 90 to 130).
3. `_initialize_managers` builds three helpers: a cache manager, a state manager, and a resume manager. It also builds an S3 cache manager if `--s3-sync` was given.
4. `_initialize_stages` loops over the 12 stage classes and builds each enabled one.

@@code unified_kg_rag/application/ingestion/pipeline.py 167-200@@

@@code unified_kg_rag/application/ingestion/pipeline.py 218-288@@

**[RAN]** With only parsing and loading enabled, the constructor finishes and touches no documents. The checkpoints were added by wrapping methods from an outside script (`reproduce/scripts/step2b.py`); the repo's code was not edited.

@@out 03@@

**[RAN]** With all 12 stages enabled and no AWS access, the constructor fails while building the third stage:

@@out 02@@

**[READ]** The reason is that the chunking stage builds its model clients in its own constructor:

@@code unified_kg_rag/application/ingestion/pipeline_stages.py 613-631@@

@@code unified_kg_rag/adapters/ingestion/chunker.py 584-617@@

So without AWS access, or a substitute model factory, the pipeline object cannot even be created with stage 3 or later enabled. Section 9 shows the substitute.

### 4.4 `pipeline.run()`

@@code unified_kg_rag/application/ingestion/pipeline.py 303-382@@

In order **[READ]**: check the source folder exists (line 319); settle the run ID (321); optionally download the cache from S3 (332); compute the folder fingerprint (337); decide between resume and new run (344 to 367); execute the stages (369).

The stage loop and the single-stage wrapper:

@@code unified_kg_rag/application/ingestion/pipeline.py 551-645@@

Every stage shares one base class. Its `execute` times the stage, calls the stage's own `_execute_core`, validates the counts, and converts any exception into a FAILED result:

@@code unified_kg_rag/application/ingestion/pipeline_stages.py 116-155@@

@@code unified_kg_rag/application/ingestion/pipeline_stages.py 175-207@@

After a failed stage the run stops unless `--continue-on-error` was given:

@@code unified_kg_rag/application/ingestion/pipeline.py 733-749@@

### 4.5 Stage 1, document parsing

@@code unified_kg_rag/application/ingestion/pipeline_stages.py 499-563@@

One file that fails to parse does not stop the stage. It goes into `failed_files` (lines 536 to 538).

The file filter:

@@code unified_kg_rag/application/ingestion/pipeline_stages.py 565-597@@

A path is kept only if all four conditions hold **[READ]**: it is a file; its extension is supported; `_should_exclude_file` does not match it; and it is not inside the cache folder or the export folder.

**[RAN]** The real conditions on a deliberately messy folder (`reproduce/scripts/filter_demo.py`):

@@out 04@@

Two things that output shows:

- `is_relative_to` compares whole folder names, so `cache2` is not inside `cache`.
- `src/__pycache__/y.txt` is kept. The `__pycache__` pattern matches only something named exactly `__pycache__`, not files inside such a folder.

Supported extensions and the empty-text check come from the parser:

@@code unified_kg_rag/adapters/ingestion/parser.py 174-193@@

@@code unified_kg_rag/adapters/ingestion/parser.py 127-161@@

**[RAN]** In the session's environment the optional `unstructured` package was not installed, so the supported list was `.csv`, `.json`, `.pdf`, `.txt`.

### 4.6 Stage 2, document loading

@@code unified_kg_rag/application/ingestion/pipeline_stages.py 291-350@@

**[READ]** When parsing already completed in this run, loading does not read the folder again. It reuses `context.documents`, and removes duplicates only if `self.loader.deduplicate` is on. That flag comes from `processing.deduplicate`, which defaults to `False`:

@@code unified_kg_rag/domain/models/config.py 998-1014@@

**[READ]** If the DynamoDB option is on, loading also filters the documents down to new or changed ones (lines 325 to 329, and `_apply_incremental_filter` at lines 360 to 419). **[NOT CHECKED]** That path was never run; DynamoDB is off by default.

### 4.7 The first real run

**[RAN]** `reproduce/scripts/step3.py`, five documents, stages 1 and 2:

@@out 05@@

Four files are written. `pipeline_metadata.json` is the run's logbook:

@@out 06@@

**[READ]** The documents themselves are not in that file. These fields are excluded on purpose, and live in the per-stage output files instead:

@@code unified_kg_rag/shared/pipeline_manager.py 50-68@@

---

## 5. Run IDs, reruns and resume

### 5.1 How a run ID is made

@@code unified_kg_rag/application/ingestion/pipeline.py 402-427@@

**[READ]** If no ID is passed, one is generated: the word `pipeline`, an 8-character hash of the source folder's subfolder names (or of the folder's own name if it has no subfolders), and the current date and time to the second.

**[RAN]** For a folder named `docs` with no subfolders the middle part is always `46b42b42`. Only the timestamp differs between runs. A generated ID therefore never matches an earlier run.

### 5.2 The resume decision

@@code unified_kg_rag/application/ingestion/pipeline.py 340-367@@

All three parts of `can_resume` must be true: there is an ID (always true); `--force-rebuild` was not given; and a saved record exists for that ID.

@@code unified_kg_rag/shared/pipeline_manager.py 88-93@@

**[READ]** There is no separate resume command. Resume means running `run-ingestion` again with the old ID, through `--pipeline-id` or the environment variable `GRAPHRAG_PIPELINE_ID` (`run_ingestion_pipeline.py`, lines 97 to 103), with the same cache folder and without `--force-rebuild`.

### 5.3 Four rerun scenarios

**[RAN]** `reproduce/scripts/step4.py`. Scenario D first appends one sentence to `docs/01_acme.txt`.

@@out 07@@

| Scenario | Saved record found | Path | Stages that ran |
|---|---|---|---|
| A. No ID given | No, a new ID was generated | New run | Parsing, loading |
| B. Same ID, nothing changed | Yes | Resume from loading | Loading only |
| C. Same ID plus force rebuild | Yes | New run | Parsing, loading |
| D. Same ID, one file edited | Yes | Resume from parsing | Parsing, loading |

### 5.4 The code each scenario goes through

The resume path, once `can_resume` is true:

@@code unified_kg_rag/application/ingestion/pipeline.py 461-526@@

@@code unified_kg_rag/shared/pipeline_manager.py 385-434@@

Where the old run got to:

@@code unified_kg_rag/shared/pipeline_manager.py 469-486@@

Whether each completed stage's saved output is still there under the current inputs:

@@code unified_kg_rag/shared/pipeline_manager.py 488-559@@

Loading the saved outputs back into the context:

@@code unified_kg_rag/shared/pipeline_manager.py 589-670@@

Walking the scenarios through that code:

- **A [RAN].** Line 408 generates a fresh ID. `pipeline_exists` is false. `_prepare_new_run` (lines 528 to 542) creates an empty context and starts at the first stage.
- **B [RAN].** The record shows both stages completed. `_handle_auto_resume` finds no unfinished stage, so lines 481 to 484 pick the last one, loading. The cache check passes. `restore_pipeline_context` loads the saved documents. `_prepare_context_for_resume` keeps only results of stages before loading, so loading's own "completed" result is dropped and the loop runs it again. This is bug 2.
- **C [RAN].** `not force_rebuild` is false, so the new-run branch is taken and the old record is never opened. The cache strategy is also set to `FORCE_REFRESH` (lines 174 to 178 of `pipeline.py`), and, when started from the command line, saving is switched off (section 7).
- **D [RAN].** As B up to the cache check. The folder fingerprint is now different, so the expected file name for parsing's output is different, so it is "missing". Lines 523 to 534 move the start back to parsing and empty the completed list. Both stages run and save under the new names. The old files stay on disk.

**[READ]** A small inconsistency inside the repo: the docstring at `pipeline_manager.py` lines 544 to 545 says document parsing has no cache mapping, but `STAGE_OUTPUTS` (line 332) gives it one, and the runs above show its output being saved and checked.

---

## 6. The cache

### 6.1 File names carry a fingerprint

**[READ]** Each saved stage output is named `<attribute>-<12 hex characters>.json`. The 12 characters are a hash of two things: the settings that affect that stage and every stage before it, and the folder fingerprint.

@@code unified_kg_rag/shared/utils/cache_keys.py 238-306@@

Which settings count for which stage:

@@code unified_kg_rag/shared/utils/cache_keys.py 69-122@@

**[READ]** The module's own header notes a limit: built-in prompt templates are code, so editing one does not change the fingerprint (lines 38 to 40).

### 6.2 The folder fingerprint

@@code unified_kg_rag/shared/utils/cache_keys.py 195-235@@

**[READ]** One line per source file: relative path, size in bytes, SHA-256 of the contents. Modification times are deliberately not used.

**[RAN]** Recomputed by hand for the five documents after the edit (`reproduce/scripts/manifest_demo.py`). The result matches what the pipeline logged:

@@out 08@@

**[RAN]** The fingerprint was `70f976b347ba` for the five original documents and `11e583bd8e55` after one sentence was appended to `01_acme.txt`.

**[READ]** The pipeline does not compare old and new files and does not know which file changed. It only finds that the file names it expects no longer exist.

### 6.3 Saving

@@code unified_kg_rag/application/ingestion/pipeline.py 647-731@@

@@code unified_kg_rag/shared/cache_manager.py 313-356@@

### 6.4 "Is it there?" and expiry

@@code unified_kg_rag/shared/cache_manager.py 58-70@@

@@code unified_kg_rag/domain/models/cache.py 56-60@@

**[READ]** `cache.ttl_seconds` defaults to 86400, which is 24 hours (`config.py`, lines 2234 to 2235). **[RAN]** The run log confirms `TTL=86400s` (section 7.1).

**[READ]** A search of the cache manager, pipeline manager, ingestion pipeline, the command-line runner and the S3 cache adapter for delete operations (`rmtree`, `unlink`, `os.remove`, `shutil`) found exactly one: removal of a temporary file after a failed metadata save (`pipeline_manager.py`, line 187). Old cache files are never deleted by this code.

### 6.5 What a rerun does to files on disk

| Rerun | On disk | Status |
|---|---|---|
| New ID | A new run folder next to the old one | **[RAN]** |
| Same ID, nothing changed | Same file names, overwritten in place | **[RAN]** |
| Same ID, files or settings changed | New files next to the old ones, old ones stay | **[RAN]** for files changed; **[INFERRED]** for settings changed |
| Force rebuild from the command line | Nothing deleted, no stage outputs written | **[RAN]** |

`pipeline_metadata.json` is rewritten in every case.

### 6.6 Why the cache matters after a run has finished

The person asked this directly. If a run finished and is never touched again, the cache mostly does not matter: the finished graph is in the AWS stores. **[READ, `README.md`]** Questions are answered from those stores. **[NOT CHECKED]** The question-answering code has not been traced.

The cache matters when something runs again:

1. **A run crashes partway [INFERRED].** A resume loads the saved outputs of the finished stages and restarts at the failed one.
2. **A setting is changed and the run is repeated.** **[RAN]** Fingerprints computed before and after changing `processing.similarity_threshold` from 0.6 to 0.55 (`reproduce/scripts/threshold_demo.py`):

@@out 15@@

   Stages 1 to 6 keep their fingerprint. **[INFERRED]** A resume with the new value would reuse their saved outputs and redo stage 7 onward. A full 12-stage resume was never run.
3. **The run is split across machines [READ].** Comments in the code describe "phased execution", where separate tasks share one run ID through S3 (`pipeline.py` lines 497 to 502; `pipeline_manager.py` lines 145 to 151). **[NOT CHECKED]** The deployment code under `iac/` was not read.

---

## 7. The real command, run for real

### 7.1 Resume with nobody at the keyboard

**[RAN]** `run-ingestion --source-directory docs --pipeline-id <first run's ID> --enabled-stages DOCUMENT_PARSING,DOCUMENT_LOADING`, with standard input closed:

@@out 10@@

The command asks a question and, with nobody to answer, exits with code 1. This is bug 1.

### 7.2 Why the check fails

**[RAN]** The names the early check looks for, against the names really on disk (`reproduce/scripts/keys_demo.py`):

@@out 09@@

**[READ]** The check builds names without the folder fingerprint, because at that point the fingerprint slot is still empty:

@@code unified_kg_rag/shared/pipeline_manager.py 370-383@@

@@code unified_kg_rag/application/cli/run_ingestion_pipeline.py 349-368@@

@@code unified_kg_rag/shared/pipeline_manager.py 672-702@@

### 7.3 Resume, answering "y"

**[RAN]** The same command with `y` piped in. The integrity prompt appears, then the real resume logic runs with the right names, skips parsing, and re-runs loading:

@@out 11@@

### 7.4 Force rebuild

**[RAN]** On a brand-new run ID, then a plain resume of that ID:

@@out 12@@

The force rebuild wrote only `pipeline_metadata.json`. The resume that followed had nothing to load and redid both stages.

**[RAN]** On an ID that already has saved outputs. A marker string was written by hand into the first run's saved files, so that its output can be recognised later:

@@out 13@@

What that shows:

- Step 3a: a force rebuild of an existing run ID hits the same integrity prompt, and exits with code 1 when nobody can answer. This was first seen on 11 October (section 12, item 5).
- Step 3b: answered with `y`, the force rebuild runs both stages and saves nothing. The files on disk keep their old save time and the marker.
- Step 4: a later resume skips parsing, loads the old marked files, and the loading output it writes carries the marker. The forced run's fresh results were never saved.

This is bug 3.

### 7.5 Expiry

**[RAN]** The expiry was simulated by editing the dates in `cache_index.json`. Nobody waited 24 hours.

@@out 14@@

This is bug 4, logged as a "gotcha" because the behaviour looks intended.

---

## 8. Stage 3, text chunking

### 8.1 What the stage does

**[READ]** For each document it calls the chunker and collects the pieces into `context.text_units` (`pipeline_stages.py` lines 633 to 662, in Appendix C). The work is in `adapters/ingestion/chunker.py`.

Default settings **[READ]**:

@@code unified_kg_rag/domain/models/config.py 664-731@@

### 8.2 The decisions per document

**Step 1, rough cut.** The default `content_type` is `markdown`, so the document is first split at its headings. Small sections are glued together until each piece reaches `min_chunk_size`.

@@code unified_kg_rag/adapters/ingestion/chunker.py 850-910@@

**Step 2, is the model needed?** Only for a piece of at least twice `min_chunk_size` (2,000 characters by default) or longer than `max_chunk_size`.

@@code unified_kg_rag/adapters/ingestion/chunker.py 664-706@@

**Step 3, ask the model.** Each line of the piece is numbered. The model is asked for the line numbers where new chunks should start.

@@code unified_kg_rag/adapters/ingestion/chunker.py 924-948@@

**Step 4, apply the answer and tidy up.**

@@code unified_kg_rag/adapters/ingestion/chunker.py 779-848@@

@@code unified_kg_rag/adapters/ingestion/chunker.py 325-355@@

**Step 5, build a text unit for each chunk.**

@@code unified_kg_rag/adapters/ingestion/chunker.py 475-519@@

### 8.3 How the model was replaced

**[READ]** `Providers` accepts a substitute model factory (`adapters/providers.py`, lines 60 to 78), and `DataIngestionPipeline` accepts a `providers` argument (`pipeline.py`, line 133).

The session used a stand-in model (`reproduce/scripts/fake_llm.py`, full text in Appendix B). It records every prompt to `prompts.jsonl`. It replies from `answers.json`, a file of answers that Claude wrote by hand after reading the prompt. If no answer is on file it replies "keep as one chunk" and marks the call `PLACEHOLDER`.

Limits of this method:

- The replies are Claude's, written in the conversation. They are not what the configured Bedrock model would say.
- It covers chat models only. **[NOT CHECKED]** Embeddings (lists of numbers for similarity search) cannot be written by hand; a later stage that needs them will need fake vectors.

### 8.4 The run

Two longer documents were added, because the five short ones (about 120 characters each) never reach the model.

**[RAN]** Capture pass, no answers on file yet:

@@out 16@@

Read from that output:

- The stage asked the factory for two models when it was built: `anthropic.claude-sonnet-5-5` (the one used to repair malformed replies, `fixing.fixing_model_id`) and `anthropic.claude-haiku-5-5` (`chunking.chunking_model_id`).
- `06_profile.txt` (2,414 characters, with headings) was cut at its headings into pieces of 1,532 and 884 characters. Both are under 2,000, so the model was not asked.
- `07_review.txt` (2,804 characters, no headings) stayed as one piece of 2,803 characters and was sent to the model. One model call in total.

The prompt's fixed text is in Appendix D.

**The hand-written answer.** The document covers three topics: operations at the Chennai site (lines 1 to 8), the next robot model (lines 9 to 16), and hiring and expansion (lines 17 to 24). Claude's reply was that new chunks start at lines 9 and 17.

**[RAN]** Default settings, with that answer:

@@out 17@@

The result is one chunk of 2,801 characters, not three. The three pieces were 945, 952 and 904 characters, all under the 1,000 minimum, so step 4 merged them back together.

**[RAN]** The same answer with `min_chunk_size` lowered to 900:

@@out 18@@

Three chunks, split at lines 9 and 17. So the model only proposes cut points; the size rules decide.

**[RAN]** The merge function called directly (`reproduce/scripts/merge_demo.py`):

@@out 19@@

The merged text is 2,801 characters where the original was 2,803. The two line breaks at the joins are gone, and the sentences run together with no space: `renewed.The engineering team`. **[READ]** Line 832 of `chunker.py` strips each piece, and line 337 joins pieces with `+=` and no separator. This is candidate 5 in `POTENTIAL_BUGS.md`.

### 8.5 The reply parser

**[RAN]** In the 9 October session the hand-written XML was passed through the repo's parser and came back as `{'chunk_boundaries': {'line_number': ['9', '17']}}`. **[READ]** The parser is `RobustXMLOutputParser` in `shared/utils/langchain.py`, lines 597 to 868. It tries four methods in turn before giving up.

### 8.6 Follow-up questions on stage 3 (11 October)

These three scripts are not part of `run_all.sh`. Run them by hand from the work folder that `run_all.sh` leaves behind (they need its `docs/` folder and `fake_llm.py`); they are in Appendix G.

**Is size checked twice, and are tokens counted?** **[READ]** Size is in characters throughout. It is used at four points in `chunker.py`: deciding whether to ask the model (lines 679 to 684); in the prompt, where the model is told the target range (lines 937 to 942); after the reply, where pieces under the minimum are merged and pieces over the maximum are split (lines 842 to 844); and in a quality check that only logs a warning (lines 645 to 651). The code never checks whether the model obeyed the range. Tokens are estimated once per finished chunk and stored as `n_tokens`; the estimate is not used for any decision in this stage:

@@code unified_kg_rag/adapters/aws/token_counter.py 119-126@@

**Why a model and not only a size count?** **[READ]** The model's job is to choose cut points; it does not count. The setting `processing.chunking.chunker_type` has two values, `intelligent` (default, the path traced here) and `simple`, which cuts by size alone with no model (section 8.1 shows the settings and their descriptions). **[NOT CHECKED]** The design document was not read, so the authors' reasons for the default are unknown.

**Is there overlap between chunks?** **[READ]** `chunk_overlap` (default 500) is given only to the size-only splitter (`chunker.py`, lines 365 to 367). That splitter is used by the simple chunker, by the fallback when a model reply is rejected, and when a chunk is over the maximum. Cuts chosen by the model and cuts at headings are plain slices with no overlap. **[RAN]** `reproduce/scripts/overlap_demo.py`:

@@txt followup_out/overlap_demo.out@@

**Can the model put invented text into a chunk?** **[READ]** No. The model returns line numbers only; chunk text is always sliced from the original (`chunker.py`, lines 830 to 835, in section 8.2). **[RAN]** Seven different replies, including wrong and invented ones, fed into the real chunker with checkpoints (`reproduce/scripts/trace_ai_answers.py`, minimum chunk size set to 900 so that splits are visible):

@@txt followup_out/trace_ai_answers.out@@

Read from that output:

- Numbers of 1 or below, and anything that is not a whole number, are dropped (lines 171 to 174).
- A line number past the end counts as a miss. If more than 10% miss (`max_marker_miss_rate`), the whole reply is rejected and the size-only splitter is used; the chunk is labelled `fallback` (case 2).
- Invented text in the reply is never used (cases 5 and 6).
- A reply with no usable numbers gives one chunk, still labelled `llm`, with nothing counted as a failure (cases 4 and 5). This is bug 7.
- Case 7 went to the second, "repair" model. The stand-in for that model always answers "keep as one chunk", so what a real repair model would return is **[NOT CHECKED]**.
- **[INFERRED]** A valid line number in a poor place (the middle of a topic) would be accepted. The model cannot change the text, but it can choose bad cut points.

**Does the model add context between chunks?** **[READ]** No. A chunk is the sliced text with nothing added. Its place is recorded beside the text, in the attributes built at lines 487 to 494 (section 8.2, step 5). **[NOT CHECKED]** Whether a later stage shows the model neighbouring chunks.

**What if the reply is unusable and the piece is large?** **[RAN]** `reproduce/scripts/trace_oversized.py`, default settings, a 24,160-character text with no headings:

@@txt followup_out/trace_oversized.out@@

With a "keep as one chunk" reply, or a reply with no usable numbers, the result is a single chunk of 24,159 characters, three times `max_chunk_size`. This is bug 7.

**The prompt exactly as sent** for `07_review.txt` under default settings. System message:

@@txt followup_out/prompt_system.txt@@

Human message:

@@txt followup_out/prompt_human.txt@@

---

## 9. Stage 4, and what is known about later stages

### 9.1 Stage 4, translation (traced 12 October)

**What it does [READ].** It asks the model to translate each chunk into a target language and stores the result beside the original. Stage class: `TranslationStage` in `pipeline_stages.py`. Work: `adapters/ingestion/translator.py` (216 lines, read in full). Prompt: `TextTranslationPrompt` in `domain/prompts/data_processing.py`, lines 187 to 272 (read).

The settings, and the languages on offer:

@@code unified_kg_rag/domain/models/config.py 743-775@@

@@code unified_kg_rag/domain/models/config.py 63-73@@

The stage:

@@code unified_kg_rag/application/ingestion/pipeline_stages.py 665-757@@

The translator:

@@code unified_kg_rag/adapters/ingestion/translator.py 57-196@@

**How the runs were made.** `reproduce/scripts/stage4.py`, with the stand-in model from section 8.3. It runs stages 1 to 4 on a folder `docs5` holding the five short documents, with `01_acme.txt` in its edited form (one sentence appended, as left by scenario D). To recreate after `run_all.sh`, from its work folder: `mkdir docs5 && cp docs/0[1-5]_*.txt docs5/`, then copy in `stage4.py`. Modes: `default`; `es` (target language Spanish); `es-broken` (target Spanish, and a model that raises an error on every call). Hand-written answers are in `reproduce/scripts/answers_es.json`; copy it to `answers.json` before the answered run.

**Run A, default settings [RAN].**

@@txt followup_out/stage4_A_default.out@@

The skip check fires, the translator is never built, no model is called, and an empty `translated_units` list is still saved to the cache.

**Run B1, Spanish, capture pass [RAN].** No answers on file, so the stand-in replied with its placeholder, which is leftover chunking XML:

@@txt followup_out/stage4_B1_capture.out@@

The five prompts, keyed by hash, and the chunk each one carries:

@@txt followup_out/stage4_prompt_keys.out@@

The prompt as sent for the first chunk. System message:

@@txt followup_out/stage4_prompt_system.txt@@

Human message:

@@txt followup_out/stage4_prompt_human.txt@@

**Run B, Spanish, with Claude's hand-written translations [RAN].**

`reproduce/scripts/answers_es.json`

@@file reproduce/scripts/answers_es.json json@@

@@txt followup_out/stage4_B_answered.out@@

**Run C, Spanish, every model call fails [RAN].**

@@txt followup_out/stage4_C_broken.out@@

**How the language name reaches the prompt [RAN].** `reproduce/scripts/lang_format_demo.sh`. The 3.10 and 3.12 lines use a tiny stand-alone enum of the same kind, not the repo:

@@txt followup_out/stage4_lang_format.out@@

**What the runs show.**

- **[RAN]** The original text is kept. The translation is added to the chunk's `translated_texts` dictionary, keyed by language code (`translator.py`, lines 183 to 186). `n_tokens` still describes the original.
- **[RAN]** `context.translated_units` holds the same objects as `context.text_units`; the translator changes the chunks in place and returns the list it was given (line 121).
- **[RAN]** The prompt names the target as `LanguageCode.ES` on Python 3.11, because the enum object itself is passed in (line 168). On Python 3.10 the same formatting gives `es`. The repo supports 3.10 to 3.12. Bug 8.
- **[RAN]** Any non-empty reply is stored as the translation (lines 177 to 186). The placeholder XML in run B1 was stored as the "Spanish translation" of all five chunks and counted as five successes. Bug 9.
- **[RAN]** When every model call fails, the stage still ends `completed`, with `units_translated: 0` and five failures counted only inside `translation_stats`. Errors are caught in the translator (lines 118 to 119), and the stage reports as many outputs as inputs (line 755). Bug 10.
- **Claude's own mistake, 12 October.** On the first answered replay Claude matched two hand-written answers to the wrong prompts, because it assumed the prompts were captured in document order; they were not. The Meera Shah chunk received the Orbit Logistics translation. The pipeline accepted it. The mapping was corrected by matching each answer to the source text quoted in its prompt (the key table above), and the run was repeated. The answers file in this repository is the corrected one.

**[NOT CHECKED] What later stages read.** A search (not a full read) shows later stages use `context.translated_units or context.text_units` (`pipeline_stages.py` lines 777, 827, 985, 1296, 1311; line 1188 has the opposite order), and that helpers such as `domain/ingestion/base_processor.py` lines 46 to 48 read `translated_texts.get(target_language, text)`. If that holds, the translation, not the original, is what the graph is built from when translation is on. To be confirmed in stage 5.

### 9.2 Files behind the remaining stages

**[READ]** Found by searching each stage class's own lines in `pipeline_stages.py` for the helper classes it constructs. File locations are from the map in Appendix A.

| Stage | Class (lines in `pipeline_stages.py`) | Helper classes it constructs | Helper's file |
|---|---|---|---|
| 5 Graph extraction | `GraphExtractionStage` (758-809) | `GraphExtractor` | `adapters/ingestion/graph_extractor.py` |
| 6 Gleaning | `GleaningStage` (810-888) | `GraphGleaner` | `adapters/ingestion/gleaner.py` |
| 7 Graph resolution | `GraphResolutionStage` (889-965) | `GraphResolver`, `DescriptionSummarizer` | `domain/ingestion/graph_resolver.py`, `adapters/ingestion/description_summarizer.py` |
| 8 Claim extraction | `ClaimExtractionStage` (966-1011) | `ClaimExtractor` | `adapters/ingestion/claim_extractor.py` |
| 9 Claim resolution | `ClaimResolutionStage` (1012-1062) | `ClaimResolver` | `domain/ingestion/claim_resolver.py` |
| 10 Graph analysis | `GraphAnalysisStage` (1063-1127) | `GraphAnalyzer`, `GraphBuilder` | `domain/ingestion/graph_analyzer.py`, `domain/ingestion/graph_builder.py` |
| 11 Community detection | `CommunityDetectionStage` (1128-1244) | `GraphAnalyzer`, `CommunityDetector` | `domain/ingestion/graph_analyzer.py`, `adapters/ingestion/community_detector.py` |
| 12 Indexing | `IndexingStage` (1245-1639) | `IndexingManager`, `IncrementalIndexer` | `application/storage/indexing_manager.py`, `application/ingestion/incremental.py` |

**[NOT CHECKED]** This table says only which helper each stage constructs. None of these classes or files has been read, so what they do is unknown.

### 9.3 Suggested order of work

1. Stage 4 is done (section 9.1).
2. Read `GraphExtractionStage` and `adapters/ingestion/graph_extractor.py` in full, and the extraction prompt in `domain/prompts/graph_extraction.py`.
3. Run stage 5 with the stand-in model: capture the prompts, answer them by hand, feed the answers back. The stand-in's placeholder reply is chunking XML, so it must be changed or made per-prompt first.
4. Continue stage by stage. Stage 12 writes to Neptune and OpenSearch; decide with the person whether to use the in-memory fakes under `tests/fixtures/fakes/` (mentioned in the repo's `CLAUDE.md`, not yet looked at) or real services.

---

## 10. Possible bugs

Full text is in `POTENTIAL_BUGS.md`. Summary:

| # | Title | Status in the person's log | Evidence |
|---|---|---|---|
| 1 | The resume check runs before the folder fingerprint is known | Logged | **[RAN]** sections 7.1 to 7.3 |
| 2 | Resuming a fully finished run re-runs the last stage | Logged, with an open question on whether it is a bug | **[RAN]** two-stage case; **[INFERRED]** for indexing |
| 3 | A force rebuild does not save its results, so a later rerun uses older ones | Logged | **[RAN]** section 7.4, two non-model stages; **[INFERRED]** for model stages |
| 4 | Saved work expires after 24 hours (gotcha) | Logged | **[RAN]** with edited dates, section 7.5 |
| 5 | Merged chunk pieces lose the space or line break between them | **Candidate.** Proposed to the person, no answer yet | **[RAN]** section 8.4 |
| 6 | A force rebuild of an existing run ID also stops at the integrity prompt | **Candidate.** Found 11 October while building this file; the person has not seen it | **[RAN]** section 7.4, step 3a |
| 7 | An unusable model reply in chunking is accepted silently and can leave a chunk far over the size limit | Logged 11 October | **[RAN]** section 8.6, stand-in model |
| 8 | The translation prompt names the language as `LanguageCode.ES` on Python 3.11 and 3.12 | Logged 12 October | **[RAN]** section 9.1 |
| 9 | Any non-empty model reply is stored as the translation | Logged 12 October | **[RAN]** section 9.1 |
| 10 | Stage 4 reports `completed` when every translation call failed | Logged 12 October | **[RAN]** section 9.1 |
| 11 | The `ignore_errors` setting has no effect on chunks that fail in graph extraction | Logged 12 October | **[RAN]** `followup_out/step3b_ignore_off.out`, `step3b_ignore_on.out` |

None of these has been reported to the maintainers, and none has been checked against the repo's issue tracker or its unit tests.

---

## 11. Open questions and gaps

Collected from the sections above. All **[NOT CHECKED]** unless marked.

1. Does bug 1 appear with all 12 stages and with a custom config file? It was reproduced only with two stages and default settings.
2. Is re-running the last stage on resume (bug 2) intended? No comment in the code says.
3. In a full run, would a resume of a finished run really execute indexing again, and what would that do to the stores?
4. Bug 3 for model stages: after a force rebuild, do the stores and the cache really end up with different graph versions? What does indexing do on the next run: replace, merge, or leave?
5. What does `indexing.reset` do? It is referenced at `pipeline_stages.py` line 381.
6. The incremental path (DynamoDB registry) was never run.
7. S3 sync and phased execution were never run and the `iac/` code was not read.
8. How do the repo's own tests exercise `validate_pipeline_integrity`? Hits were seen in `tests/unit/test_pipeline_manager_logic.py` and `tests/unit/test_stage_cache_invalidation.py` but the tests were not read.
9. Does the lost separator (candidate 5) matter downstream? It depends on how extraction reads chunk text.
10. Behaviour on Windows and on Python 3.10 or 3.12.
11. Everything about the four other commands.
12. **[INFERRED]** Is the batch processor's fixed 300-second call limit (`shared/utils/langchain.py` line 127, not settable from the config) long enough for a graph extraction reply? The prompt allows up to 32,768 output tokens. A call that legitimately takes longer would time out, be retried up to 5 times, and each abandoned call would keep running and be billed (lines 154 to 159). Real reply times have not been measured.

---

## 12. Corrections to things said in the 9 October session

These are places where what was told to the person was imprecise, incomplete, or has since been superseded. The next session should set them straight if they come up.

1. **"Translation is switched off by default."** Said at the end of the stage 3 explanation. Imprecise. **[READ]** `TranslationConfig.enabled` defaults to `True`. The stage is a no-op by default because source and target language are both English (section 9.1).
2. **"A default run with AWS would build 10 stages."** This is **[INFERRED]** and was flagged as unrun at the time. It remains unrun.
3. **"Stage 2 ... only removing duplicates."** Wrong for default settings. **[READ]** Duplicates are removed only when `processing.deduplicate` is on, and it defaults to `False` (section 4.6). In the session's runs stage 2 therefore removed nothing and passed the documents from stage 1 straight through. With DynamoDB enabled the stage would also filter to new and changed documents.
4. **Bug 3's first test.** In the 9 October session every command in that test had `y` piped into it. That is why the force rebuild on an existing ID went through without comment. The 11 October re-run separates the two cases (section 7.4, steps 3a and 3b).
5. **New on 11 October: force rebuild on an existing ID stops at the integrity prompt.** Not seen on 9 October for the reason in item 4. **[READ]** There are two reasons it would fail the check: the missing fingerprint of bug 1, and the fact that under the `FORCE_REFRESH` strategy `cache_exists` always returns false (`cache_manager.py`, lines 59 to 60). **[INFERRED]** So fixing bug 1 alone would not remove this prompt.
6. **The bug log's "About this log" section** says the test setup was five small files and two stages. That is true for entries 1 to 4. Candidate 5 used seven files and three stages.
7. **The person was told at the start that not everything had been read.** That is still the case; section 2 has the exact list.
8. **`01_acme.txt` was edited during the session.** One sentence, "Acme has 120 employees.", was appended for scenario D and left in place. `reproduce/docs_original/` holds the file as first written; `run_all.sh` re-applies the edit at the same point.

---

## 13. How the person likes to work: notes for the next session

- They ask short follow-up questions and expect the answer to start with the answer.
- They want code shown, with file names and line numbers, and then a plain-language reading of it.
- When they say they are confused, go slower and smaller, and use a concrete story with the sample data.
- They decide what goes in the bug log. Ask, then add.
- The bug log was kept as a document in their personal Claude account. On the work machine, `POTENTIAL_BUGS.md` in this bundle is the copy to continue from.

---

## 14. Appendices

### Appendix A. Map of the repository

**[RAN]** Output of `reproduce/scripts/graph.py`. "Layer edges" counts how many modules in one top-level folder import from another.

@@out 01@@

### Appendix B. The tracing scripts

`reproduce/scripts/step2.py`: constructor with checkpoints, all 12 stages enabled.

@@file reproduce/scripts/step2.py python@@

`reproduce/scripts/step2b.py`: the same with only parsing and loading enabled.

@@file reproduce/scripts/step2b.py python@@

`reproduce/scripts/step3.py`: first run with checkpoints.

@@file reproduce/scripts/step3.py python@@

`reproduce/scripts/step4.py`: scenarios A to D.

@@file reproduce/scripts/step4.py python@@

`reproduce/scripts/fake_llm.py`: the stand-in model.

@@file reproduce/scripts/fake_llm.py python@@

`reproduce/scripts/step5.py`: stages 1 to 3 with the stand-in model.

@@file reproduce/scripts/step5.py python@@

`reproduce/scripts/answers_handwritten.json`: Claude's replies, keyed by a hash of the prompt.

@@file reproduce/scripts/answers_handwritten.json json@@

`reproduce/run_all.sh`: the driver.

@@file reproduce/run_all.sh bash@@

### Appendix C. The chunking stage class

@@code unified_kg_rag/application/ingestion/pipeline_stages.py 613-662@@

### Appendix D. The chunking prompt

@@code unified_kg_rag/domain/prompts/data_processing.py 8-124@@

### Appendix E. The sample documents

Each of these files ends with one newline after the text shown (see section 0.5).

`reproduce/docs_original/01_acme.txt`

@@file reproduce/docs_original/01_acme.txt text@@

`reproduce/docs_original/02_meera.txt`

@@file reproduce/docs_original/02_meera.txt text@@

`reproduce/docs_original/03_orbit.txt`

@@file reproduce/docs_original/03_orbit.txt text@@

`reproduce/docs_original/04_product.txt`

@@file reproduce/docs_original/04_product.txt text@@

`reproduce/docs_original/05_investor.txt`

@@file reproduce/docs_original/05_investor.txt text@@

`reproduce/docs_added/06_profile.txt`

@@file reproduce/docs_added/06_profile.txt text@@

`reproduce/docs_added/07_review.txt`

@@file reproduce/docs_added/07_review.txt text@@

### Appendix F. Results of the checker

**[RAN]** `reproduce/scripts/check_expected.py` on the 11 October output:

@@check@@

### Appendix G. The helper scripts

Small scripts called by `run_all.sh`, followed by scripts run by hand: three stage 3 follow-ups (`overlap_demo.py`, `trace_ai_answers.py`, `trace_oversized.py`, section 8.6) and the stage 4 scripts (`stage4.py`, `lang_format_demo.sh`, section 9.1; `answers_es.json` is shown in section 9.1). Each one's first lines say what it does.

`reproduce/scripts/graph.py`

@@file reproduce/scripts/graph.py python@@

`reproduce/scripts/keys_demo.py`

@@file reproduce/scripts/keys_demo.py python@@

`reproduce/scripts/manifest_demo.py`

@@file reproduce/scripts/manifest_demo.py python@@

`reproduce/scripts/threshold_demo.py`

@@file reproduce/scripts/threshold_demo.py python@@

`reproduce/scripts/merge_demo.py`

@@file reproduce/scripts/merge_demo.py python@@

`reproduce/scripts/filter_demo.py`

@@file reproduce/scripts/filter_demo.py python@@

`reproduce/scripts/logfilter.py`

@@file reproduce/scripts/logfilter.py python@@

`reproduce/scripts/mark_cache.py`

@@file reproduce/scripts/mark_cache.py python@@

`reproduce/scripts/show_cache.py`

@@file reproduce/scripts/show_cache.py python@@

`reproduce/scripts/ttl_tools.py`

@@file reproduce/scripts/ttl_tools.py python@@

`reproduce/scripts/show_prompts.py`

@@file reproduce/scripts/show_prompts.py python@@

`reproduce/scripts/check_expected.py`

@@file reproduce/scripts/check_expected.py python@@

`reproduce/scripts/overlap_demo.py`

@@file reproduce/scripts/overlap_demo.py python@@

`reproduce/scripts/trace_ai_answers.py`

@@file reproduce/scripts/trace_ai_answers.py python@@

`reproduce/scripts/trace_oversized.py`

@@file reproduce/scripts/trace_oversized.py python@@

`reproduce/scripts/stage4.py`

@@file reproduce/scripts/stage4.py python@@

`reproduce/scripts/lang_format_demo.sh`

@@file reproduce/scripts/lang_format_demo.sh bash@@

`reproduce/scripts/linetrace.py`

@@file reproduce/scripts/linetrace.py python@@

`reproduce/scripts/stage5.py`

@@file reproduce/scripts/stage5.py python@@

`reproduce/scripts/make_answers5.py`

@@file reproduce/scripts/make_answers5.py python@@

`reproduce/scripts/answers_stage5.json`

@@file reproduce/scripts/answers_stage5.json json@@

`reproduce/scripts/stage5_step1_build.py`

@@file reproduce/scripts/stage5_step1_build.py python@@

`reproduce/scripts/stage5_step1b_inside_setup.py`

@@file reproduce/scripts/stage5_step1b_inside_setup.py python@@

`reproduce/scripts/stage5_step2_inputs.py`

@@file reproduce/scripts/stage5_step2_inputs.py python@@

`reproduce/scripts/stage5_step3a_batch.py`

@@file reproduce/scripts/stage5_step3a_batch.py python@@

`reproduce/scripts/stage5_step3b_failures.py`

@@file reproduce/scripts/stage5_step3b_failures.py python@@

### Appendix H. Self-extraction test

**[RAN]** Every file was extracted from this document by the rules in section 0.5 and compared with the original.

@@selftest@@
