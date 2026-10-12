# Potential bugs found: unified-kg-rag-on-aws

A running log of possible bugs found while tracing [awslabs/unified-kg-rag-on-aws](https://github.com/awslabs/unified-kg-rag-on-aws) step by step.

Entries 1 to 4 were agreed with the person during the 9 October 2026 session and carry the same content as the log document kept in their personal Claude account (last changed 9 October 2026). Entries 5 and 6 are **candidates**: 5 was proposed to the person and not yet answered, and 6 was found on 11 October 2026 and the person has not seen it. Entry 7 was approved by the person on 11 October 2026 and is also in their log document. Entries 8, 9 and 10 (stage 4, translation) are candidates shown to the person on 12 October 2026; they have not yet said which to log.

## About this log

- Code version: commit `37ef4a7df28bdd19a5f277d30aff026ddf8cbd50` (cloned 9 October 2026). Line numbers refer to that commit.
- Test setup for entries 1 to 4 and 6: 5 small text files, default settings, no AWS account, only the first two stages switched on (document parsing and document loading). Entries 5 and 7 used the chunking stage with a stand-in model whose replies were written by hand.
- Each entry says what was actually run and what is only read from the code.
- Clock times and run IDs quoted in the evidence tables of entries 1 to 4 are from the 9 October session. `HANDOFF.md` holds the output of an 11 October re-run of the same experiments, which gave the same file names and fingerprints with different clock times.
- Code excerpts in this file were copied from the repository by script.
- These are potential bugs. None has been reported to or confirmed by the maintainers.

---

## Bug 1: The resume check runs before the folder fingerprint is known

On every resume, the command reports the old run's saved files as missing, although they are there.

**Background.** Every saved stage output has a name like `documents-54cf4641e850`. The code part is a fingerprint built from two ingredients: your settings and the contents of your source folder. When a run saves a file it uses both ingredients. To find that file again later, the code must rebuild the name with the same two.

**Order of events.** The command-line runner (`run_ingestion_pipeline.py`) does things in this order:

| Step | Line | What happens | Folder fingerprint known? |
| --- | --- | --- | --- |
| 1 | 377 | Builds the pipeline object. The fingerprint slot starts empty (`pipeline_manager.py`, line 383: `self.corpus_fingerprint = None`). | No |
| 2 | 390 | Runs the "are the old run's saved files all there?" check. | No |
| 3 | 393 | Calls `pipeline.run()`, which calculates the fingerprint at `pipeline.py` lines 337–338. | Yes, from here on |

```python
# unified_kg_rag/application/cli/run_ingestion_pipeline.py, lines 375-393
        boto_session = boto3.Session(profile_name=self.config.aws.profile_name)
        pipeline_config = self._create_pipeline_config()
        self.pipeline = DataIngestionPipeline(
            config=self.config,
            pipeline_config=pipeline_config,
            source_directory=self.args.source_directory,
            target_directory=self.args.target_directory,
            boto_session=boto_session,
            metrics_sink=self._build_metrics_sink(),
        )

        try:
            if self._handle_metadata_operations():
                return

            if not self._validate_pipeline_integrity():
                return

            context = self._execute_pipeline()
```

```python
# unified_kg_rag/application/ingestion/pipeline.py, lines 335-338
            # Part of every stage cache key, so it must be set before the
            # resume decision reads the cache.
            self.corpus_fingerprint = self._compute_corpus_fingerprint(source_path)
            self.resume_manager.corpus_fingerprint = self.corpus_fingerprint
```

Step 2 runs one step too early. The name-builder only adds the folder ingredient when it has one (`cache_keys.py`, lines 272–273):

```python
# unified_kg_rag/shared/utils/cache_keys.py, lines 272-273
    if corpus_fingerprint is not None:
        projection.append(("corpus_manifest", corpus_fingerprint))
```

So at step 2 it builds names from settings alone. No run ever saves files under those names, so the check reports them missing.

**Effect.**

- With a person at the keyboard, you get a "Continue despite integrity issues?" prompt on every resume. Answering `y` works, because the real resume logic in step 3 uses the right names.
- With nobody to answer, the command exits with an error. Exit code 1 was seen when it ran without input.

**Evidence from the test run.**

| Stage | Name the early check looked for | Name actually on disk |
| --- | --- | --- |
| Document parsing | `documents-1035b7a62512` | `documents-54cf4641e850` |
| Document loading | `documents-ac616352a4e7` | `documents-0842cedc0821` |

Command used: `run-ingestion --source-directory docs --pipeline-id pipeline-46b42b42-20261009_132047 --enabled-stages DOCUMENT_PARSING,DOCUMENT_LOADING`

**Not yet checked.**

- Only reproduced in the two-stage setup with default settings. From the code, it should affect any resume of an existing run through this command.
- The repo's unit tests for this check have not been read in full.

**Possible fix.** Calculate the folder fingerprint before step 2, or move the check inside `run()` after line 338.

---

## Bug 2: Resuming a fully finished run re-runs the last stage

When every stage of the old run is already completed and nothing has changed, a resume still runs the last recorded stage again. It has no "nothing to do" outcome.

**Cause, part 1.** The restart point is chosen in `pipeline_manager.py`, lines 474–484. The code walks the saved record looking for the first stage that is not completed. When all are completed there is none, so it falls back to the last stage in the record:

```python
# unified_kg_rag/shared/pipeline_manager.py, lines 470-486
    def _handle_auto_resume(stage_results: list[dict]) -> tuple[str, list[str]]:
        completed_stages = []
        resume_stage = None

        for result in stage_results:
            if result["status"] == "completed":
                completed_stages.append(result["stage_name"])
            else:
                resume_stage = result["stage_name"]
                break

        if resume_stage is None:
            resume_stage = (
                stage_results[-1]["stage_name"] if stage_results else "document_loading"
            )

        return resume_stage, completed_stages
```

**Cause, part 2.** `pipeline.py`, lines 515–521, then keeps only the results of stages that come before the restart point. The last stage's own "completed" result is dropped, so the run loop (lines 586–591) treats it as not done and runs it.

```python
# unified_kg_rag/application/ingestion/pipeline.py, lines 515-521
        valid_results = [
            res
            for res in context.stage_results
            if res.stage_name in canonical_order
            and canonical_order.index(res.stage_name) < start_index
        ]
        context.stage_results = valid_results
```

```python
# unified_kg_rag/application/ingestion/pipeline.py, lines 586-591
        for stage in stages_to_execute:
            if stage.name in completed_stage_names:
                logger.info("Skipping previously completed stage: '%s'", stage.name)
            else:
                logger.info("Executing stage: '%s'", stage.name)
                result = self._execute_stage(stage, context)
```

**Effect.**

- In the test run the cost was nothing: document loading re-ran in under a millisecond and reused the 5 saved documents.
- In a full 12-stage run the last stage is indexing, which writes to the AWS stores. By the same logic it would run again on a resume of a finished run.

**Evidence from the test run.** Same run ID, no file changed:

```
Resume strategy determined - Start from: 'document_loading', Load 2 completed stages
Found 1 previously completed stages: 'document_parsing'
Executing 1 stages: 'document_loading'
```

**Not yet checked.**

- The full 12-stage case has not been run, so the indexing re-run is read from the code only.
- It is not clear from the code whether this is intended (a deliberate "redo the last step") or an oversight. No comment in the code explains it.

**Open question left for the person** (posted as a comment on this entry in their log document, unanswered): should this stay listed as a bug, or as a design question until the full 12 stages have been run?

---

## Bug 3: A force rebuild does not save its results, so a later rerun uses older ones

A run with `--force-rebuild` does all its work but writes no stage outputs to the cache. If the same run ID already has saved outputs from an earlier normal run, those stay, and a later resume loads them as if they were current.

**Cause.**

- The command-line runner turns saving off whenever force rebuild is on: `cache_enabled=not self.args.force_rebuild` (`run_ingestion_pipeline.py`, line 268).

```python
# unified_kg_rag/application/cli/run_ingestion_pipeline.py, lines 265-276
        return PipelineConfig(
            stages_enabled=stages,
            continue_on_error=self.args.continue_on_error,
            cache_enabled=not self.args.force_rebuild,
            local_directory=self.args.cache_directory,
            s3_sync_enabled=self.args.s3_sync,
            s3_bucket_name=self.args.s3_bucket_name,
            s3_prefix=self.args.s3_prefix,
            force_rebuild=self.args.force_rebuild,
            pipeline_id=self.args.pipeline_id,
            resume_from_stage=self.args.resume_from_stage,
        )
```

- The save step then returns early (`pipeline.py`, lines 650–654):

```python
# unified_kg_rag/application/ingestion/pipeline.py, lines 650-654
        if not self.pipeline_config.cache_enabled:
            logger.info(
                "Cache disabled, skipping output save for stage: '%s'", stage_name
            )
            return
```

- Nothing deletes or replaces the older saved files. The only delete in the cache, pipeline and command-line code removes a temporary file after a failed save (`pipeline_manager.py`, line 187).

**Why it matters.** The cache and the AWS stores can end up holding different versions, and the code trusts the cache.

1. Monday, normal run. The AI stages produce result A. A is saved to the cache and written to the AWS stores.
2. Tuesday, force rebuild. The AI stages run again and produce result B, which can differ from A. B is written to the AWS stores but not to the cache, which still holds A.
3. Wednesday, you change one late setting and rerun with the same run ID. The early stages are reused from the cache, so they load A. Everything after is built from A, with no warning.

Tuesday's AI calls are effectively wasted, and Wednesday's result is built on the older version.

**Evidence from the test run.** Run ID `demo-force`, two stages:

| Step | What was done | Result |
| --- | --- | --- |
| 1 | Normal run | Two output files saved at 14:10:16 |
| 2 | Marker text `MARKER-FROM-FIRST-RUN` added by hand to both saved files | Lets run 1's output be recognised later |
| 3 | Force rebuild, same ID | Log: "Cache disabled, skipping output save" for both stages. Files unchanged, still saved at 14:10:16, marker still present |
| 4 | Resume, same ID, no force | Parsing skipped. The output written by loading began with `MARKER-FROM-FIRST-RUN` |

A second test, force rebuild on a brand-new ID (`force-test`), wrote only `pipeline_metadata.json`. A resume of it then redid every stage.

Note added 11 October: in the 9 October test, `y` was piped into every command, including step 3. See candidate 6 for what happens at step 3 without it.

**Not yet checked.**

- Shown only with the two non-AI stages. The Monday-to-Wednesday story for AI stages is read from the code.
- The last stage (indexing) has not been traced, so it is unknown whether Wednesday's run would remove result B from the AWS stores or leave it.

---

## Bug 4 (gotcha): Saved work expires after 24 hours, so a late resume starts over

A resume more than 24 hours after a stage was saved treats that stage's output as missing and runs it again. The results stay correct; the cost is time and AI calls spent twice. This looks intended, so it is listed as a gotcha.

**Cause.**

- Each saved output is stamped with an expiry time when written: now plus `ttl_seconds` (`cache_manager.py`, lines 343–347). The run log shows the default: `TTL=86400s`, which is 24 hours.

```python
# unified_kg_rag/shared/cache_manager.py, lines 343-347
            expires_at=(
                datetime.now() + timedelta(seconds=self.ttl_seconds)
                if self.ttl_seconds is not None and self.ttl_seconds > 0
                else None
            ),
```

- The "is it there?" check returns false for an expired entry (`cache_manager.py`, line 70):

```python
# unified_kg_rag/shared/cache_manager.py, line 70
        return entry.exists_locally and not entry.is_expired
```

- The resume logic then moves the start point back to the first stage whose output it cannot find (`pipeline_manager.py`, lines 504–534).

**Why it matters.** A run does an hour of AI calls in stages 1 to 7 and crashes at stage 8 on Monday at 3pm. You resume on Tuesday at 4pm. The saved work is 25 hours old, so the run starts again from stage 1.

**Evidence from the test run.** Run ID `demo-ttl`, two stages:

| Step | What was done | Result |
| --- | --- | --- |
| 1 | Normal run | Index file recorded: created 9 Oct 14:11, expires 10 Oct 14:11 |
| 2 | Resume straight away | Saved outputs accepted, parsing skipped |
| 3 | Expiry dates edited by hand to the previous day, then resume | Log: "Rewinding resume point from 'document_loading' to 'document_parsing'". Both stages ran again |

**Not yet checked.** The expiry was simulated by editing the dates, not by waiting 24 hours.

**Workaround.** The 24 hours is the setting `cache.ttl_seconds`, which can be raised. The expired files are not deleted from disk.

---

## Candidate 5 (not yet approved): Merged chunk pieces lose the space or line break between them

When the chunking stage merges pieces that are under the minimum size, it joins them with nothing in between. Sentences from two different lines run together.

**Cause.** Each piece is stripped of surrounding whitespace when it is cut out (`chunker.py`, line 832), and pieces are then joined with `+=` (line 337 and line 352):

```python
# unified_kg_rag/adapters/ingestion/chunker.py, lines 830-835
            for end_pos in sorted(set(indices)):
                if end_pos > start_pos:
                    chunk = text[start_pos:end_pos].strip()
                    if chunk:
                        chunks.append(chunk)
                start_pos = end_pos
```

```python
# unified_kg_rag/adapters/ingestion/chunker.py, lines 332-355
            while i < len(chunks):
                current_chunk = chunks[i]
                j = i + 1
                while j < len(chunks) and len(current_chunk) < self.min_chunk_size:
                    if len(current_chunk) + len(chunks[j]) <= self.max_chunk_size:
                        current_chunk += chunks[j]
                        j += 1
                    else:
                        break
                merged_chunks.append(current_chunk)
                i = j
            return self._merge_final_small_chunk_if_needed(merged_chunks)
        except Exception as e:
            logger.debug("Failed to merge small chunks: %s", e)
            return chunks

    def _merge_final_small_chunk_if_needed(self, chunks: list[str]) -> list[str]:
        if len(chunks) > 1 and len(chunks[-1]) < self.min_chunk_size:
            last_chunk = chunks.pop()
            if len(chunks[-1]) + len(last_chunk) <= self.max_chunk_size:
                chunks[-1] += last_chunk
            else:
                chunks.append(last_chunk)
        return chunks
```

**Evidence from the test run.** Document `07_review.txt` is 24 lines and 2,803 characters without its final line break. The stand-in model answered that new chunks start at lines 9 and 17, giving pieces of 945, 952 and 904 characters. With the default minimum of 1,000 the three were merged back into one chunk of 2,801 characters, two fewer than the original. Calling `ChunkProcessor(1000, 8000).merge_small_chunks` directly on the three pieces gave the same result, and the text at the first join read:

```
'ore the contract is renewed.The engineering team spe'
```

**Not yet checked.**

- Whether this matters for later stages, which read the chunk text.
- The same `+=` is used by the simple chunker and the fallback path (`chunker.py`, lines 564 and 919). There the pieces come from LangChain's splitter, and whether those pieces keep their own separators was not looked at.

---

## Candidate 6 (not yet seen by the person): A force rebuild of an existing run ID also stops at the integrity prompt

Running `--force-rebuild` with the ID of a run that already exists triggers the same "Continue despite integrity issues?" prompt as bug 1, and exits with code 1 when nobody can answer.

**Cause.**

- The command-line integrity check runs for any existing run ID, whether or not force rebuild was asked for:

```python
# unified_kg_rag/application/cli/run_ingestion_pipeline.py, lines 349-368
    def _validate_pipeline_integrity(self) -> bool:
        if not self.pipeline:
            raise ValueError("Pipeline not initialized")

        if self.args.pipeline_id and self.pipeline.state_manager.pipeline_exists(
            self.args.pipeline_id
        ):
            is_valid, errors = self.pipeline.resume_manager.validate_pipeline_integrity(
                self.args.pipeline_id
            )
            if not is_valid:
                console.print(
                    f"\n[red]Pipeline integrity check failed for '{self.args.pipeline_id}':[/red]"
                )
                for error in errors:
                    console.print(f"  • {error}")
                if not Confirm.ask("Continue despite integrity issues?"):
                    console.print("[yellow]Pipeline execution cancelled.[/yellow]")
                    return False
        return True
```

- It fails for the reason given in bug 1. Read from the code, there is also a second reason: with force rebuild the cache uses the `FORCE_REFRESH` strategy, under which the "is it there?" check always answers no:

```python
# unified_kg_rag/application/ingestion/pipeline.py, lines 172-178
        # force_rebuild ignores existing cached stage outputs: FORCE_REFRESH makes
        # the cache treat every entry as a miss so stages actually re-execute.
        cache_strategy = (
            CacheStrategy.FORCE_REFRESH
            if self.pipeline_config.force_rebuild
            else CacheStrategy.CONTENT_HASH
        )
```

```python
# unified_kg_rag/shared/cache_manager.py, lines 58-60
    def cache_exists(self, cache_key: str, pipeline_id: str) -> bool:
        if self.strategy == CacheStrategy.FORCE_REFRESH:
            return False
```

**Evidence.** 11 October re-run, run ID `demo-force`, after a normal run had completed. `run-ingestion --source-directory docs --enabled-stages DOCUMENT_PARSING,DOCUMENT_LOADING --pipeline-id demo-force --force-rebuild` with standard input closed exited with code 1 after printing the integrity prompt. The same command with `y` piped in went on to run both stages. The output is in `HANDOFF.md`, section 7.4, steps 3a and 3b.

**Not yet checked.**

- That the second reason alone would keep the prompt after bug 1 is fixed. This is read from the code and was not tested.
- Whether a prompt on force rebuild is intended.

---

## Bug 7: An unusable AI reply in chunking is accepted silently, and can leave a chunk far over the size limit

When the chunking model's reply contains no usable line numbers, the code keeps the whole piece of text as one chunk, labels it `llm`, counts no failure, and does not apply the maximum-size split. Added 11 October 2026.

**Cause.** All in `adapters/ingestion/chunker.py`.

- If the reply has no usable line numbers, the function returns the whole text as a single piece (lines 783–793):

```python
# unified_kg_rag/adapters/ingestion/chunker.py, lines 779-793
    def _chunk_with_llm_boundaries(
        self, text: str, response: dict[str, Any]
    ) -> list[str] | None:
        try:
            chunk_boundaries = response.get("chunk_boundaries")
            if chunk_boundaries is None:
                return [text]

            lines = text.split("\n")

            line_numbers = self.line_boundary_processor.extract_line_numbers(
                chunk_boundaries
            )
            if not line_numbers:
                return [text]
```

- That early return skips the size rules. The merge and the split of oversized pieces happen only on the path that has line numbers (lines 842–844):

```python
# unified_kg_rag/adapters/ingestion/chunker.py, lines 842-844
            merged_chunks = self.chunk_processor.merge_small_chunks(chunks)

            return self._split_large_line_chunks(merged_chunks)
```

- The caller treats any non-empty result as a success and labels it `llm` (lines 698–702). The failure counter is only raised when the result is empty or rejected:

```python
# unified_kg_rag/adapters/ingestion/chunker.py, lines 693-703
            for i, pre_chunk in enumerate(pre_chunks):
                if i not in response_of:
                    final_chunks.append(("unsplit", pre_chunk, i + 1))
                    continue
                llm_response = response_of[i]
                chunks = self._get_chunks_from_response(pre_chunk, llm_response)
                if chunks:
                    final_chunks.extend([("llm", chunk, i + 1) for chunk in chunks])
                else:
                    self._handle_llm_failure(pre_chunk, i, final_chunks)
            return final_chunks
```

- A proper "keep as one chunk" reply takes the same path, so the code cannot tell "the model chose one chunk" from "the model's reply was unusable":

```python
# unified_kg_rag/adapters/ingestion/chunker.py, lines 161-184
    def extract_line_numbers(self, boundaries: dict[str, Any] | list[Any]) -> list[int]:
        try:
            if not boundaries:
                return []

            if self._is_single_chunk_request(boundaries):
                return []

            line_numbers = self._extract_line_numbers_from_response(boundaries)

            valid_line_numbers = [
                num for num in line_numbers if isinstance(num, int) and num > 1
            ]
            return sorted(set(valid_line_numbers))

        except Exception as e:
            logger.debug("Failed to extract line numbers: %s", e)
            return []

    @staticmethod
    def _is_single_chunk_request(boundaries: dict[str, Any] | list[Any]) -> bool:
        if isinstance(boundaries, dict):
            return boundaries.get("single_chunk") in [True, "true"]
        return False
```

**Effect.**

- A piece of text can be up to `pre_chunk_size` (default 50,000 characters) when it reaches the model. With an unusable or "one chunk" reply it stays that size, although `max_chunk_size` is 8,000.
- The setting's own description says every chunk is embedded whole and must fit the embedding model's input, "or its tail is never embedded or reranked":

```python
# unified_kg_rag/domain/models/config.py, lines 687-699
    max_chunk_size: int = Field(
        default=8000,
        ge=1,
        description=(
            "Maximum chunk size in characters. Every chunk is embedded whole and "
            "reranked as one document, so it must fit the embedding model's "
            "input (Titan Text Embeddings V2: 8,192 tokens) and the reranker's "
            "per-document limit (Cohere Rerank 3.5: 4,096 tokens), or its tail "
            "is never embedded or reranked. Default 8,000 fits Titan V2 even at "
            "~1 character per token (CJK scripts) and is ~2K tokens of English, "
            "inside the reranker limit."
        ),
    )
```

- The run's statistics show no failure. The only trace is a logged warning from the quality check:

```python
# unified_kg_rag/adapters/ingestion/chunker.py, lines 645-651
            validation = self.quality_validator.validate_chunks(chunks)
            if not validation["is_valid"]:
                logger.warning(
                    "Chunk quality issues for document '%s': %s",
                    doc.file_name,
                    validation["issues"],
                )
```

**Evidence from the test run.** Default settings, stand-in model, a 24,160-character text file with no headings (`trace_oversized.py`):

| Reply from the model | Chunks produced | Failures counted | Quality check |
| --- | --- | --- | --- |
| "Keep as one chunk" | 1 chunk of 24,159 characters, labelled `llm` | None | "1 chunks exceed maximum size" |
| Words where numbers should be | 1 chunk of 24,159 characters, labelled `llm` | None | "1 chunks exceed maximum size" |
| Usable line numbers (49, 97, 145) | 4 chunks of 6,039 characters | None | No issues |

On the 2,804-character test file, two unusable replies (words for numbers; invented sentences with no numbers) each gave one chunk labelled `llm`, with one model call and no fallback (`trace_ai_answers.py`, cases 4 and 5). The full output of both scripts is in `HANDOFF.md`, section 8.6.

**Not yet checked.**

- What the later stages (embedding, indexing) do with a chunk over the limit. They have not been traced.
- How often a real model gives such a reply. The replies here were written by hand.
- A reply that is not XML at all goes to a second "repair" model first. That path was only run with a stand-in repair model.

---

## Candidate 8 (shown 12 October, not yet approved): The translation prompt names the language as `LanguageCode.ES` on Python 3.11 and 3.12

The translator passes the language enum object itself into the prompt template, and how that object prints depends on the Python version.

**Cause.** `adapters/ingestion/translator.py`:

```python
# unified_kg_rag/adapters/ingestion/translator.py, lines 162-172
    @staticmethod
    def _create_chain_inputs(
        texts: list[str], target_language: LanguageCode
    ) -> list[dict[str, Any]]:
        try:
            return [
                {"text": text, "target_language": target_language} for text in texts
            ]
        except Exception as e:
            logger.error("Failed to create translation inputs: %s", e)
            return []
```

`LanguageCode` is a `(str, Enum)`:

```python
# unified_kg_rag/domain/models/config.py, lines 63-73
class LanguageCode(str, Enum):
    DE = "de"
    EN = "en"
    ES = "es"
    FR = "fr"
    IT = "it"
    JA = "ja"
    KO = "ko"
    PT = "pt"
    RU = "ru"
    ZH = "zh"
```

**Evidence.** The human message of the first translation prompt, captured on Python 3.11.17, began:

```
Translate the following text to LanguageCode.ES while preserving all original content
```

The formatting call on three Python versions (`lang_format_demo.sh`; the 3.10 and 3.12 lines use a stand-alone enum of the same kind, not the repo):

| Python | `"{x}".format(x=...)` gives |
| --- | --- |
| 3.10.20 | `es` |
| 3.11.17 (repo) | `LanguageCode.ES` |
| 3.12.3 | `L.ES` (the stand-alone enum's own name; **[INFERRED]** the repo's enum would give `LanguageCode.ES`) |

`pyproject.toml` declares support for Python 3.10 to 3.12, so the prompt text differs between supported versions.

**Not yet checked.** Whether a real model translates correctly when told "LanguageCode.ES". Whether other prompts receive enum objects the same way.

**Possible fix.** Pass `target_language.value` (or a language name) instead of the enum object.

---

## Candidate 9 (shown 12 October, not yet approved): Any non-empty model reply is stored as the translation

**Cause.** The only test on the reply is that it is not empty:

```python
# unified_kg_rag/adapters/ingestion/translator.py, lines 174-196
    def _apply_translation_result(
        self, text_unit: TextUnit, result: str | None, target_language: LanguageCode
    ) -> None:
        if not result or not result.strip():
            if self.stats:
                self.stats.num_failed_translations += 1
            return

        try:
            if text_unit.translated_texts is None:
                text_unit.translated_texts = {}

            text_unit.translated_texts[target_language.value] = result.strip()

            if self.stats:
                self.stats.num_translated += 1
                self.stats.num_successful_translations += 1
        except Exception as e:
            logger.error(
                "Failed to apply translation for text unit '%s': %s", text_unit.id, e
            )
            if self.stats:
                self.stats.num_failed_translations += 1
```

**Evidence.**

- Capture pass, target Spanish: the stand-in model replied with leftover chunking XML (`<chunk_boundaries><single_chunk>true</single_chunk></chunk_boundaries>`). It was stored as the Spanish translation of all five chunks, and the stage reported `units_translated: 5`.
- Claude, writing the answers by hand, matched two translations to the wrong prompts on the first try. The chunk about Meera Shah received the translation of the chunk about Orbit Logistics. It was accepted without complaint.

**Why it matters [NOT CHECKED].** From a search of the code, later stages read the translation instead of the original when one exists. If so, a wrong or unrelated translation is what the graph is built from.

---

## Candidate 10 (shown 12 October, not yet approved): Stage 4 reports `completed` when every translation call failed

**Cause.** Errors are caught and logged inside the translator, and the stage counts the chunks it was given as its output:

```python
# unified_kg_rag/adapters/ingestion/translator.py, lines 111-121
        try:
            for target_language in self.all_target_languages:
                logger.info("Translating to '%s'...", target_language.value)
                self._translate_text_units_batch(text_units, target_language)

            self.stats.total_processing_time = time.time() - start_time
            self._log_completion_summary(self.stats)
        except Exception as e:
            logger.exception("Translation failed: %s", e)

        return text_units
```

```python
# unified_kg_rag/application/ingestion/pipeline_stages.py, lines 721-755
        translated_units = self.translator.translate_text_units(context.text_units)
        context.translated_units = translated_units

        translation_stats: dict[str, Any] = {}
        try:
            if hasattr(self.translator, "stats"):
                stats = self.translator.stats
                if stats is not None:
                    translation_stats = self._stats_to_dict(stats)
        except Exception as e:
            logger.warning("Failed to get translation stats: %s", e)

        units_translated_count = len(
            [
                u
                for u in translated_units
                if u.translated_texts and self.target_language in u.translated_texts
            ]
        )

        metrics = {
            "target_language": self.target_language,
            "units_processed": len(context.text_units),
            "units_translated": units_translated_count,
            "translation_stats": translation_stats,
        }

        logger.info("=" * 60)
        logger.info(
            "TRANSLATION STAGE - COMPLETED (Translated %s text units)",
            units_translated_count,
        )
        logger.info("=" * 60)

        return len(context.text_units), len(translated_units), metrics
```

**Evidence.** Target Spanish, a stand-in model that raises an error on every call:

```
stage result: status = completed | in = 5 | out = 5
stage metrics: {'target_language': 'es', 'units_processed': 5, 'units_translated': 0}
```

The five failures appear only in `translation_stats` (`num_failed_translations: 5`). The full output is in `HANDOFF.md`, section 9.1.

**Not yet checked.** Whether anything downstream (metrics, alarms) reacts to `units_translated: 0`. Later stages would then use the untranslated text, which is the same as translation being off.
