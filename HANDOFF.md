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
| 9 | Stage 5, graph extraction | **Next.** Not started. |
| 9b | Stages 6 to 12 | Not started. |
| 10 | The other four commands (`run-rag`, `run-eval`, `run-visualization`, `run-prompt-tuning`) | Not started. |

Open with the person: should the "merged pieces lose the gap between them" finding (candidate 5 in `POTENTIAL_BUGS.md`) be added to the bug log? They had not answered. Candidate 6 has not been shown to them. Bug 7 was approved and added on 11 October. Three stage 4 findings (bugs 8, 9 and 10) were shown to them on 12 October and approved and added the same day.

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

```text
37ef4a7df28bdd19a5f277d30aff026ddf8cbd50
Python 3.11.17
10:__version__ = "0.2.3"
110 docs/01_acme.txt
117 docs/02_meera.txt
124 docs/03_orbit.txt
125 docs/04_product.txt
115 docs/05_investor.txt
591 total
```

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

```toml
# pyproject.toml, lines 92-97
[project.scripts]
run-ingestion = "unified_kg_rag.application.cli.run_ingestion_pipeline:main"
run-rag = "unified_kg_rag.application.cli.run_rag_chain:main"
run-eval = "unified_kg_rag.application.cli.run_evaluation:main"
run-visualization = "unified_kg_rag.application.cli.run_visualization:main"
run-prompt-tuning = "unified_kg_rag.application.cli.run_prompt_tuning:main"
```

The session traced only the first one, `run-ingestion`.

---

## 4. Trace of `run-ingestion`

### 4.1 The front door

`main()` builds the argument parser, parses the flags, builds a runner, and calls `runner.run()`. It turns three kinds of failure into exit codes.

```python
# unified_kg_rag/application/cli/run_ingestion_pipeline.py, lines 425-439
def main() -> None:
    try:
        cli = CommandLineInterface()
        args = cli.parse_args()
        runner = IngestionPipelineRunner(args)
        runner.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline interrupted by user.[/yellow]")
        sys.exit(130)
    except PipelineExecutionError:
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]An unexpected error occurred: {e}[/red]")
        logger.exception("Unexpected error during pipeline execution")
        sys.exit(1)
```

The runner's constructor loads the config and checks the flags:

```python
# unified_kg_rag/application/cli/run_ingestion_pipeline.py, lines 148-196
class IngestionPipelineRunner:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.config = get_config(Path(args.config_path) if args.config_path else None)
        setup_logging(self.config)
        self.pipeline: DataIngestionPipeline | None = None
        self._validate_args()

    def _validate_args(self) -> None:
        metadata_only = self.args.verify_metadata or self.args.repair_metadata

        if not metadata_only and not self.args.source_directory:
            console.print(
                "[red]Error: --source-directory is required for pipeline execution.[/red]"
            )
            sys.exit(1)

        if self.args.source_directory:
            self.args.source_directory = Path(self.args.source_directory)
            if not self.args.source_directory.is_dir():
                console.print(
                    f"[red]Error: Source directory not found: {self.args.source_directory}[/red]"
                )
                sys.exit(1)

        if self.args.s3_sync and not self.args.s3_bucket_name:
            console.print(
                "[red]Error: --s3-bucket-name must be specified for S3 sync.[/red]"
            )
            sys.exit(1)

        if self.args.resume_from_stage and not self.args.pipeline_id:
            console.print(
                "[red]Error: --pipeline-id is required for --resume-from-stage.[/red]"
            )
            sys.exit(1)

        if metadata_only and not self.args.pipeline_id:
            console.print(
                "[red]Error: --pipeline-id is required for metadata operations.[/red]"
            )
            sys.exit(1)

        self.args.cache_directory = (
            Path(self.args.cache_directory)
            if self.args.cache_directory
            else Path("cache")
        )
        self.args.cache_directory.mkdir(parents=True, exist_ok=True)
```

The flag checks, in order **[READ]**: a source folder is required unless this is a metadata-only operation; the source folder must exist; `--s3-sync` needs `--s3-bucket-name`; `--resume-from-stage` needs `--pipeline-id`; metadata operations need `--pipeline-id`. The cache folder defaults to `cache` relative to the current directory and is created if missing.

`runner.run()` then builds the pipeline object, runs the two optional metadata operations, runs an integrity check, and finally calls `pipeline.run()`:

```python
# unified_kg_rag/application/cli/run_ingestion_pipeline.py, lines 370-422
    def run(self) -> None:
        display_ascii_art(__version__)
        self._display_run_info()

        console.print("\n[bold]Initializing pipeline...[/bold]")
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

            if context:
                display_pipeline_results(context)
                # A soft stage failure stops the run but does NOT raise — the
                # pipeline returns a context with status=FAILED. Without this
                # check the CLI would print success and exit 0, so Step Functions
                # (RUN_JOB, keyed on container exit code) marks the phase
                # SUCCEEDED and the failure is invisible. Raise so main() exits
                # non-zero and the failure surfaces.
                if context.status == PipelineStageStatus.FAILED:
                    failed = [
                        r.stage_name
                        for r in context.stage_results
                        if r.status == PipelineStageStatus.FAILED
                    ]
                    raise PipelineExecutionError(
                        f"Pipeline failed at stage(s): {', '.join(failed) or 'unknown'}"
                    )
                success_msg = "✓ Pipeline completed successfully!"
                console.print(
                    Panel.fit(
                        f"[bold green]{success_msg}[/bold green]", border_style="green"
                    )
                )
        finally:
            # Release the indexers' Neptune/OpenSearch connections so a finished
            # ingest run does not leak websockets/HTTP pools until interpreter
            # exit. Best-effort: pipeline.close() never raises.
            self.pipeline.close()
```

Note the order of lines 377, 390 and 393. It matters for bug 1.

The runner translates flags into a `PipelineConfig`. Line 268 matters for bug 3:

```python
# unified_kg_rag/application/cli/run_ingestion_pipeline.py, lines 242-276
    def _create_pipeline_config(self) -> PipelineConfig:
        all_stages = {stage.name: stage for stage in PipelineStageType}

        if self.args.enabled_stages:
            enabled_stages_set = {
                stage_name.upper() for stage_name in self.args.enabled_stages
            }
            stages = {
                stage_enum: stage_name in enabled_stages_set
                for stage_name, stage_enum in all_stages.items()
            }
            invalid_stages = enabled_stages_set - set(all_stages.keys())
            if invalid_stages:
                console.print(
                    f"[red]Error: Invalid stage names provided: {', '.join(invalid_stages)}[/red]"
                )
                console.print(
                    f"[yellow]Available stages are: {', '.join(all_stages.keys())}[/yellow]"
                )
                sys.exit(1)
        else:
            stages = dict.fromkeys(PipelineStageType, True)

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

### 4.2 The 12 stages

**[READ]** The stage order is fixed by this dictionary:

```python
# unified_kg_rag/application/ingestion/pipeline.py, lines 64-109
class DataIngestionPipeline:
    # Run order; kept in PipelineStageType's declaration order (tested).
    STAGE_CLASSES = {
        PipelineStageType.DOCUMENT_PARSING: DocumentParsingStage,
        PipelineStageType.DOCUMENT_LOADING: DocumentLoadingStage,
        PipelineStageType.TEXT_CHUNKING: TextChunkingStage,
        PipelineStageType.TRANSLATION: TranslationStage,
        PipelineStageType.GRAPH_EXTRACTION: GraphExtractionStage,
        PipelineStageType.GLEANING: GleaningStage,
        PipelineStageType.GRAPH_RESOLUTION: GraphResolutionStage,
        PipelineStageType.CLAIM_EXTRACTION: ClaimExtractionStage,
        PipelineStageType.CLAIM_RESOLUTION: ClaimResolutionStage,
        PipelineStageType.GRAPH_ANALYSIS: GraphAnalysisStage,
        PipelineStageType.COMMUNITY_DETECTION: CommunityDetectionStage,
        PipelineStageType.INDEXING: IndexingStage,
    }

    INPUT_DIR_REQUIRED_STAGES = {
        PipelineStageType.DOCUMENT_PARSING,
        PipelineStageType.DOCUMENT_LOADING,
    }

    BOTO_REQUIRED_STAGES = {
        PipelineStageType.CLAIM_EXTRACTION,
        PipelineStageType.COMMUNITY_DETECTION,
        PipelineStageType.GLEANING,
        PipelineStageType.GRAPH_ANALYSIS,
        PipelineStageType.GRAPH_EXTRACTION,
        # Graph resolution merges descriptions and then re-summarizes the
        # over-long ones with an LLM (DescriptionSummarizer), so it needs Bedrock.
        PipelineStageType.GRAPH_RESOLUTION,
        PipelineStageType.TEXT_CHUNKING,
        PipelineStageType.TRANSLATION,
    }

    # Stages that build LLM/embedding adapters; they receive the pipeline's
    # provider bundle.
    PROVIDER_STAGES = BOTO_REQUIRED_STAGES | {PipelineStageType.INDEXING}

    # Stages that consume the document-status registry (incremental indexing).
    # The DocStatusPort adapter is built ONCE at this orchestration layer and
    # injected, rather than each stage constructing its own.
    DOC_STATUS_STAGES = {
        PipelineStageType.DOCUMENT_LOADING,
        PipelineStageType.INDEXING,
    }
```

**[RAN]** With no config file, these are the relevant defaults (printed by `step2b.py`, section 4.3): gleaning enabled, claim extraction disabled, community detection enabled, DynamoDB disabled.

**[INFERRED]** A default run with AWS access would therefore build 10 stages, since the two claim stages are switched off by lines 238 to 244 below. This was never run.

### 4.3 Constructing `DataIngestionPipeline`

```python
# unified_kg_rag/application/ingestion/pipeline.py, lines 124-165
    def __init__(
        self,
        config: Config,
        pipeline_config: PipelineConfig,
        source_directory: Path | None = None,
        target_directory: Path | None = None,
        boto_session: boto3.Session | None = None,
        metrics_sink: MetricsSink | None = None,
        *,
        providers: Providers | None = None,
    ) -> None:
        self.config = config
        self.pipeline_config = pipeline_config
        # Where pipeline metrics are forwarded (CloudWatch EMF, etc.). Defaults
        # to a no-op so the library assumes no monitoring backend.
        self.metrics_sink: MetricsSink = metrics_sink or NullMetricsSink()
        self.source_directory = source_directory or Path(
            self.config.processing.document_parsing.source_directory
        )
        # Parsed-JSON export directory, if any. Unset means no export; it
        # must never default to the source corpus (see DocumentParsingStage).
        explicit_target = (
            target_directory or self.config.processing.document_parsing.target_directory
        )
        self.target_directory: Path | None = (
            Path(explicit_target) if explicit_target else None
        )
        # Composition root for ingestion: one provider bundle (session plus
        # LLM/embedding factories) built here or injected, and passed to every
        # stage, so an injected factory reaches every LLM/embedding adapter
        # and the default Bedrock clients are created once per pipeline.
        self.providers = Providers.resolve(config, providers, boto_session)
        self.boto_session = self.providers.boto_session

        self._initialize_managers()
        self.stages, self.name_to_type_map = self._initialize_stages()

        logger.info(
            "Successfully initialized pipeline with %s stages: '%s'",
            len(self.stages),
            ", ".join([stage.name for stage in self.stages]),
        )
```

What the constructor does **[READ]**:

1. Stores the config and the source folder.
2. Gets a `Providers` object. `Providers` holds the AWS session and the model factories, and builds each one only on first use (`adapters/providers.py`, lines 90 to 130).
3. `_initialize_managers` builds three helpers: a cache manager, a state manager, and a resume manager. It also builds an S3 cache manager if `--s3-sync` was given.
4. `_initialize_stages` loops over the 12 stage classes and builds each enabled one.

```python
# unified_kg_rag/application/ingestion/pipeline.py, lines 167-200
    def _initialize_managers(self) -> None:
        cache_config = self.config.cache
        chunking_config = cache_config.chunking

        cache_manager_class = get_cache_manager()
        # force_rebuild ignores existing cached stage outputs: FORCE_REFRESH makes
        # the cache treat every entry as a miss so stages actually re-execute.
        cache_strategy = (
            CacheStrategy.FORCE_REFRESH
            if self.pipeline_config.force_rebuild
            else CacheStrategy.CONTENT_HASH
        )
        self.cache_manager = cache_manager_class(
            config=self.config,
            cache_directory=self.pipeline_config.local_directory,
            strategy=cache_strategy,
            ttl_seconds=cache_config.ttl_seconds,
            chunk_size=chunking_config.chunk_size,
            max_file_size_mb=chunking_config.max_file_size_mb,
            enable_chunking=chunking_config.enabled,
        )
        self.state_manager = PipelineStateManager(self.cache_manager)
        # The resume manager must reconstruct the same input-fingerprinted cache
        # keys the save path writes, so it needs the same config.
        self.resume_manager = PipelineResumeManager(self.state_manager, self.config)

        self.s3_cache_manager: S3CacheManager | None = None
        if self.pipeline_config.s3_sync_enabled:
            self.s3_cache_manager = S3CacheManager(
                config=self.config,
                boto_session=self.boto_session,
                bucket_name=self.pipeline_config.s3_bucket_name,
                prefix=self.pipeline_config.s3_prefix,
            )
```

```python
# unified_kg_rag/application/ingestion/pipeline.py, lines 218-288
    def _initialize_stages(
        self,
    ) -> tuple[list[PipelineStage], dict[str, PipelineStageType]]:
        stages = []
        name_to_type_map = {}
        enabled_stages = []
        disabled_stages = []

        # Build the doc-status adapter once (incremental mode) and inject it into
        # the stages that need it, instead of each stage constructing its own.
        doc_status = self._build_doc_status_store()

        for stage_type, stage_class in self.STAGE_CLASSES.items():
            stage_enabled = self.pipeline_config.stages_enabled.get(stage_type, True)

            if stage_type == PipelineStageType.GLEANING:
                gleaning_config = self.config.processing.gleaning
                if gleaning_config and hasattr(gleaning_config, "enabled"):
                    stage_enabled = stage_enabled and gleaning_config.enabled

            elif stage_type in [
                PipelineStageType.CLAIM_EXTRACTION,
                PipelineStageType.CLAIM_RESOLUTION,
            ]:
                claim_config = getattr(self.config.processing, "claim_extraction", None)
                if claim_config and hasattr(claim_config, "enabled"):
                    stage_enabled = stage_enabled and claim_config.enabled

            elif stage_type == PipelineStageType.COMMUNITY_DETECTION:
                # Optional for a LightRAG-only (mix/hybrid/naive) ingestion, which
                # needs no communities; skipping avoids the Leiden pass and all
                # community-report LLM calls. GraphRAG global/drift require it.
                community_config = getattr(
                    self.config.graph, "community_detection", None
                )
                if community_config and hasattr(community_config, "enabled"):
                    stage_enabled = stage_enabled and community_config.enabled

            if stage_enabled:
                kwargs: dict[str, Any] = {}
                if stage_type in self.INPUT_DIR_REQUIRED_STAGES:
                    kwargs["source_directory"] = self.source_directory
                if stage_type in self.BOTO_REQUIRED_STAGES:
                    kwargs["boto_session"] = self.boto_session
                if stage_type in self.PROVIDER_STAGES:
                    kwargs["providers"] = self.providers
                if stage_type == PipelineStageType.DOCUMENT_PARSING:
                    kwargs["target_directory"] = self.target_directory
                if stage_type in (
                    PipelineStageType.DOCUMENT_PARSING,
                    PipelineStageType.COMMUNITY_DETECTION,
                ):
                    kwargs["cache_directory"] = Path(
                        self.pipeline_config.local_directory
                    )
                if stage_type in self.DOC_STATUS_STAGES and doc_status is not None:
                    kwargs["doc_status"] = doc_status

                kwargs["config"] = self.config

                stage_instance = stage_class(**kwargs)
                stages.append(stage_instance)
                name_to_type_map[stage_instance.name] = stage_type
                enabled_stages.append(stage_type.value)
            else:
                disabled_stages.append(stage_type.value)

        if disabled_stages:
            logger.info("Disabled stages: %s", disabled_stages)

        return stages, name_to_type_map
```

**[RAN]** With only parsing and loading enabled, the constructor finishes and touches no documents. The checkpoints were added by wrapping methods from an outside script (`reproduce/scripts/step2b.py`); the repo's code was not edited.

```text
--- about to call DataIngestionPipeline(...) ---
CHECKPOINT  1: entering DataIngestionPipeline.__init__
CHECKPOINT  2: entering DataIngestionPipeline._initialize_managers
CHECKPOINT  3: entering DataIngestionPipeline._initialize_stages
CHECKPOINT  4: entering DataIngestionPipeline._build_doc_status_store
CHECKPOINT  5: entering DocumentParsingStage.__init__
CHECKPOINT  6: entering DocumentLoadingStage.__init__
--- constructor returned. What does the object hold now? ---
source_directory : docs
target_directory : None
providers        : Providers
cache_manager    : CacheManager | strategy = CacheStrategy.CONTENT_HASH
state_manager    : PipelineStateManager
resume_manager   : PipelineResumeManager
s3_cache_manager : None
stages built     : 2
    1. document_parsing       (DocumentParsingStage)
    2. document_loading       (DocumentLoadingStage)
stages skipped   : ['text_chunking', 'translation', 'graph_extraction', 'gleaning', 'graph_resolution', 'claim_extraction', 'claim_resolution', 'graph_analysis', 'community_detection', 'indexing']
gleaning.enabled = True | claim_extraction.enabled = False | community_detection.enabled = True | dynamodb.enabled = False
files on disk in cache/: []
```

**[RAN]** With all 12 stages enabled and no AWS access, the constructor fails while building the third stage:

```text
exit code: 1
--- about to call DataIngestionPipeline(...) ---
CHECKPOINT  1: entering DataIngestionPipeline.__init__
CHECKPOINT  2: entering DataIngestionPipeline._initialize_managers
CHECKPOINT  3: entering DataIngestionPipeline._initialize_stages
CHECKPOINT  4: entering DataIngestionPipeline._build_doc_status_store
CHECKPOINT  5: entering DocumentParsingStage.__init__
CHECKPOINT  6: entering DocumentLoadingStage.__init__
CHECKPOINT  7: entering TextChunkingStage.__init__
unified_kg_rag.shared.exceptions.GraphRAGException: Failed to create OutputFixingParser: Model 'anthropic.claude-sonnet-5-5' is only available through a cross-region inference profile, but none resolved in region 'us-west-2'. Enable aws.bedrock.enable_global_profile, grant bedrock:ListInferenceProfiles, or choose a region where a profile for this model exists.
```

**[READ]** The reason is that the chunking stage builds its model clients in its own constructor:

```python
# unified_kg_rag/application/ingestion/pipeline_stages.py, lines 613-631
class TextChunkingStage(PipelineStage):
    def __init__(
        self,
        config: Config,
        boto_session: boto3.Session | None = None,
        providers: Providers | None = None,
    ):
        super().__init__(
            PipelineStageType.TEXT_CHUNKING, config, boto_session, providers
        )

        chunker_type = self.config.processing.chunking.chunker_type
        self.chunker = ChunkerFactory.create_chunker(
            config=self.config,
            boto_session=self.boto_session,
            chunker_type=chunker_type,
            providers=self.providers,
        )
        self.chunker_type = chunker_type
```

```python
# unified_kg_rag/adapters/ingestion/chunker.py, lines 584-617
class IntelligentTextChunker(BaseChunker):
    def __init__(
        self,
        config: Config,
        boto_session: boto3.Session | None = None,
        show_progress: bool = True,
        *,
        providers: Providers | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(config, show_progress=show_progress)
        self.providers = Providers.resolve(config, providers, boto_session)
        self.boto_session = self.providers.boto_session
        self.ignore_errors = self.config.processing.ignore_errors

        self.factory = self.providers.llm_factory
        self.batch_processor = BatchProcessor(
            is_transient_error=is_transient_bedrock_error
        )

        robust_xml_output_parser = create_robust_xml_output_parser(
            model_purpose=ModelPurpose.INGESTION,
            factory=self.factory,
            enable_output_fixing=self.config.fixing.enabled,
            output_fixing_model_id=self.config.fixing.fixing_model_id,
        )
        self.chunker = setup_chain(
            model_purpose=ModelPurpose.INGESTION,
            factory=self.factory,
            model_id=self.chunking_config.chunking_model_id,
            prompt_class=TextChunkingPrompt,
            parser=robust_xml_output_parser,
            custom_prompts=self.config.custom_prompts,
        )
```

So without AWS access, or a substitute model factory, the pipeline object cannot even be created with stage 3 or later enabled. Section 9 shows the substitute.

### 4.4 `pipeline.run()`

```python
# unified_kg_rag/application/ingestion/pipeline.py, lines 303-382
    def run(
        self,
        source_directory: str | Path,
        pipeline_id: str | None = None,
        resume_from_stage: str | None = None,
    ) -> PipelineContext:
        log_context: Mapping[str, Any] = {}
        try:
            source_path = Path(source_directory).resolve()
            logger.info(
                "Starting pipeline run - source: '%s', pipeline_id: '%s', resume_from: '%s'",
                source_path,
                pipeline_id,
                resume_from_stage or "auto-detect",
            )

            self._validate_source_directory(source_path)

            resolved_pipeline_id = self._resolve_pipeline_id(source_path, pipeline_id)
            # Every log line of the run, the S3 sync and the failure report
            # included, carries the id (also in worker threads, see
            # ContextThreadPoolExecutor).
            log_context = bind_contextvars(pipeline_id=resolved_pipeline_id)
            resolved_resume_stage = (
                resume_from_stage or self.pipeline_config.resume_from_stage
            )

            logger.info("Resolved pipeline ID: '%s'", resolved_pipeline_id)

            if self.pipeline_config.s3_sync_enabled:
                self._sync_cache_with_s3(resolved_pipeline_id, "download")

            # Part of every stage cache key, so it must be set before the
            # resume decision reads the cache.
            self.corpus_fingerprint = self._compute_corpus_fingerprint(source_path)
            self.resume_manager.corpus_fingerprint = self.corpus_fingerprint

            # force_rebuild must ignore ALL existing cache: skip the resume path
            # entirely so the run re-executes from the beginning even when a
            # prior metadata file exists (FORCE_REFRESH alone only bypasses
            # per-stage cache reads, not the resume decision).
            can_resume = (
                resolved_pipeline_id
                and not self.pipeline_config.force_rebuild
                and self.state_manager.pipeline_exists(resolved_pipeline_id)
            )
            if can_resume:
                logger.info(
                    "Resuming existing pipeline '%s' from stage: '%s'",
                    resolved_pipeline_id,
                    resolved_resume_stage or "auto-detect",
                )
                context, start_stage_name = self._prepare_resume(
                    resolved_pipeline_id, resolved_resume_stage
                )
            else:
                if self.pipeline_config.force_rebuild:
                    logger.info(
                        "Force rebuild: ignoring any existing cache for '%s'",
                        resolved_pipeline_id,
                    )
                logger.info("Starting new pipeline run: '%s'", resolved_pipeline_id)
                context, start_stage_name = self._prepare_new_run(
                    source_path, resolved_pipeline_id, resolved_resume_stage
                )

            self._execute_pipeline(context, start_stage_name)

            logger.info(
                "Pipeline execution completed successfully - ID: '%s', Status: '%s'",
                context.pipeline_id,
                context.status,
            )
            return context

        except Exception as e:
            logger.exception("Pipeline execution failed: %s", e)
            raise PipelineExecutionError(f"Failed to run pipeline: {e}") from e
        finally:
            reset_contextvars(**log_context)
```

In order **[READ]**: check the source folder exists (line 319); settle the run ID (321); optionally download the cache from S3 (332); compute the folder fingerprint (337); decide between resume and new run (344 to 367); execute the stages (369).

The stage loop and the single-stage wrapper:

```python
# unified_kg_rag/application/ingestion/pipeline.py, lines 551-645
    def _execute_pipeline_stages(
        self, context: PipelineContext, start_stage_name: str | None
    ) -> None:
        stage_names = [stage.name for stage in self.stages]
        start_index = 0

        if start_stage_name:
            try:
                start_index = stage_names.index(start_stage_name)
            except ValueError:
                logger.warning(
                    "Start stage '%s' not found, starting from beginning",
                    start_stage_name,
                )

        completed_stage_names = {
            r.stage_name
            for r in context.stage_results
            if r.status == PipelineStageStatus.COMPLETED
        }

        if completed_stage_names:
            logger.info(
                "Found %s previously completed stages: '%s'",
                len(completed_stage_names),
                ", ".join(list(completed_stage_names)),
            )

        stages_to_execute = self.stages[start_index:]
        logger.info(
            "Executing %s stages: '%s'",
            len(stages_to_execute),
            ", ".join([s.name for s in stages_to_execute]),
        )

        for stage in stages_to_execute:
            if stage.name in completed_stage_names:
                logger.info("Skipping previously completed stage: '%s'", stage.name)
            else:
                logger.info("Executing stage: '%s'", stage.name)
                result = self._execute_stage(stage, context)

                if self._should_stop_pipeline(result):
                    logger.warning(
                        "Pipeline execution stopped due to stage failure: '%s'",
                        stage.name,
                    )
                    break

    def _execute_stage(
        self, stage: PipelineStage, context: PipelineContext
    ) -> PipelineStageResult:
        running_result = PipelineStageResult(
            stage_name=stage.name,
            status=PipelineStageStatus.RUNNING,
            start_time=datetime.now(),
        )
        self.state_manager.update_stage_result(context, running_result)

        try:
            result = stage.execute(context)
            self.state_manager.update_stage_result(context, result)

            if result.status == PipelineStageStatus.COMPLETED:
                self._save_stage_outputs_to_cache(context, stage.name)
            elif result.status == PipelineStageStatus.FAILED:
                logger.error("Stage '%s' failed: %s", stage.name, result.error_message)

            return result

        except PipelineStageError as e:
            logger.error("Stage '%s' validation failed: %s", stage.name, e)
            failed_result = PipelineStageResult(
                stage_name=stage.name,
                status=PipelineStageStatus.FAILED,
                start_time=running_result.start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )
            self.state_manager.update_stage_result(context, failed_result)
            return failed_result

        except Exception as e:
            logger.error(
                "Unexpected error in stage '%s': %s", stage.name, e, exc_info=True
            )
            failed_result = PipelineStageResult(
                stage_name=stage.name,
                status=PipelineStageStatus.FAILED,
                start_time=running_result.start_time,
                end_time=datetime.now(),
                error_message=f"Unexpected error: {str(e)}",
            )
            self.state_manager.update_stage_result(context, failed_result)
            return failed_result
```

Every stage shares one base class. Its `execute` times the stage, calls the stage's own `_execute_core`, validates the counts, and converts any exception into a FAILED result:

```python
# unified_kg_rag/application/ingestion/pipeline_stages.py, lines 116-155
    def execute(self, context: PipelineContext) -> PipelineStageResult:
        tokens = bind_contextvars(stage=self.name)
        logger.info("Starting stage: '%s'", self.name)
        start_time = datetime.now()

        try:
            input_count, output_count, metrics = self._execute_core(context)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            if not self._allows_empty_output(context):
                self._validate_critical_stage_output(input_count, output_count)

            logger.info(
                "Stage '%s' completed successfully in %.2f seconds. "
                "Inputs: %s, Outputs: %s",
                self.name,
                duration,
                input_count,
                output_count,
            )

            return self._create_result(
                PipelineStageStatus.COMPLETED,
                start_time,
                end_time,
                input_count,
                output_count,
                metrics,
            )

        except Exception as e:
            logger.exception("Stage '%s' failed: %s", self.name, e)
            end_time = datetime.now()

            return self._create_result(
                PipelineStageStatus.FAILED, start_time, end_time, error_message=str(e)
            )
        finally:
            reset_contextvars(**tokens)
```

```python
# unified_kg_rag/application/ingestion/pipeline_stages.py, lines 175-207
    def _validate_critical_stage_output(
        self, input_count: int, output_count: int
    ) -> None:
        is_critical = self._should_validate_output()
        must_have_input = self.stage_type in self.MUST_HAVE_INPUT_STAGES

        if input_count == 0:
            if must_have_input:
                error_msg = (
                    f"Stage '{self.name}' received 0 inputs "
                    f"but requires input to function. Check that the previous stage "
                    f"completed successfully."
                )
                logger.error(error_msg)
                raise PipelineStageError(error_msg)
            logger.info("Stage '%s' had no input to process", self.name)
            return

        if is_critical and output_count == 0:
            error_msg = (
                f"Critical stage '{self.name}' processed "
                f"{input_count} inputs but produced 0 outputs. Check the stage "
                f"configuration and input data quality."
            )
            logger.error(error_msg)
            raise PipelineStageError(error_msg)

        if output_count == 0:
            logger.warning(
                "Stage '%s' processed %s inputs but produced 0 outputs",
                self.name,
                input_count,
            )
```

After a failed stage the run stops unless `--continue-on-error` was given:

```python
# unified_kg_rag/application/ingestion/pipeline.py, lines 733-749
    def _should_stop_pipeline(self, result: PipelineStageResult) -> bool:
        if result.status == PipelineStageStatus.FAILED:
            if self.pipeline_config.continue_on_error:
                logger.warning(
                    "Stage '%s' failed but continuing due to continue_on_error setting: %s",
                    result.stage_name,
                    result.error_message,
                )
                return False
            else:
                logger.error(
                    "Stopping pipeline due to failure in stage '%s': %s",
                    result.stage_name,
                    result.error_message,
                )
                return True
        return False
```

### 4.5 Stage 1, document parsing

```python
# unified_kg_rag/application/ingestion/pipeline_stages.py, lines 499-563
    def _execute_core(
        self, context: PipelineContext
    ) -> tuple[int, int, dict[str, Any] | None]:
        logger.info("=" * 60)
        logger.info("DOCUMENT PARSING STAGE - STARTED")
        logger.info("=" * 60)

        files_to_parse = self._discover_files()
        input_count = len(files_to_parse)

        if not files_to_parse:
            logger.warning("No supported files found in '%s'", self.source_directory)
            return 0, 0, {"parsed_files": [], "failed_files": []}

        logger.info("Found %s files to parse", input_count)

        parsed_documents = []
        failed_files = []

        for file_path in files_to_parse:
            try:
                parser = ParserFactory.create_parser(file_path, self.config)
                document = parser.parse_file(
                    file_path, self.config.processing.document_parsing.index_value
                )
                assign_document_identity(
                    document,
                    self.source_directory,
                    self.config.indexing.additional_suffix,
                )
                parsed_documents.append(document)

                if self.target_directory is not None:
                    self._save_parsed_document(
                        document, file_path, self.target_directory
                    )

            except Exception as e:
                logger.error("Failed to parse '%s': %s", file_path, e)
                failed_files.append(str(file_path))

        context.documents = parsed_documents
        # Incremental delta detection must not mistake a file that failed to
        # parse for a deleted one (that would remove its indexed content).
        context.failed_source_files = failed_files
        output_count = len(parsed_documents)

        metrics = {
            "input_files": input_count,
            "parsed_files": [doc.file_name for doc in parsed_documents],
            "failed_files": failed_files,
            "success_rate": (
                (output_count / input_count * 100) if input_count > 0 else 0
            ),
        }

        logger.info("=" * 60)
        logger.info(
            "DOCUMENT PARSING STAGE - COMPLETED (%s/%s files parsed)",
            output_count,
            input_count,
        )
        logger.info("=" * 60)

        return input_count, output_count, metrics
```

One file that fails to parse does not stop the stage. It goes into `failed_files` (lines 536 to 538).

The file filter:

```python
# unified_kg_rag/application/ingestion/pipeline_stages.py, lines 565-597
    def _discover_files(self) -> list[Path]:
        if not self.source_directory.exists():
            raise FileNotFoundError(
                f"Source directory not found: {self.source_directory}"
            )

        # Pipeline-written trees nested under the source dir (the export
        # target, or the cache dir, e.g. source "." with cache "./cache") hold
        # JSON this pipeline produced, never source documents.
        owned_dirs = [
            d.resolve() for d in (self.target_directory, self.cache_directory) if d
        ]
        files = []
        for file_path in self.source_directory.rglob("*"):
            if (
                file_path.is_file()
                and file_path.suffix.lower() in self.supported_extensions
                and not self._should_exclude_file(file_path)
                and not any(file_path.resolve().is_relative_to(d) for d in owned_dirs)
            ):
                files.append(file_path)

        return sorted(files)

    @staticmethod
    def _should_exclude_file(file_path: Path) -> bool:
        exclude_patterns = {".*", "*.pyc", "__pycache__"}

        for pattern in exclude_patterns:
            if file_path.match(pattern):
                return True

        return False
```

A path is kept only if all four conditions hold **[READ]**: it is a file; its extension is supported; `_should_exclude_file` does not match it; and it is not inside the cache folder or the export folder.

**[RAN]** The real conditions on a deliberately messy folder (`reproduce/scripts/filter_demo.py`):

```text
supported: ['.csv', '.json', '.pdf', '.txt']
owned_dirs: [<abs>/src/cache]
path                            is_file  ext ok  excluded  in owned  KEPT
src/.secret.txt                 True     True    True      False     False
src/__pycache__                 False    False   True      False     False
src/__pycache__/x.pyc           True     False   True      False     False
src/__pycache__/y.txt           True     True    False     False     True
src/a.txt                       True     True    False     False     True
src/cache                       False    False   False     True      False
src/cache/run1                  False    False   False     True      False
src/cache/run1/documents.json   True     True    False     True      False
src/notes.docx                  True     False   False     False     False
src/real.json                   True     True    False     False     True
src/sub                         False    False   False     False     False
src/sub/b.txt                   True     True    False     False     True

is_relative_to demo:
  Path('/data/src/cache/run1/documents.json').is_relative_to('/data/src/cache') -> True
  Path('/data/src/real.json').is_relative_to('/data/src/cache') -> False
  Path('/data/src/cache2/x.json').is_relative_to('/data/src/cache') -> False
```

Two things that output shows:

- `is_relative_to` compares whole folder names, so `cache2` is not inside `cache`.
- `src/__pycache__/y.txt` is kept. The `__pycache__` pattern matches only something named exactly `__pycache__`, not files inside such a folder.

Supported extensions and the empty-text check come from the parser:

```python
# unified_kg_rag/adapters/ingestion/parser.py, lines 174-193
class ParserFactory:
    # Loaders with no heavy optional deps — always available.
    _loader_configs: dict[str, tuple[type[BaseLoader], dict, str]] = {
        ".csv": (CSVLoader, {}, "CSV"),
        # Stdlib-only: LangChain's JSONLoader needs the optional `jq` package.
        ".json": (JsonTextLoader, {}, "JSON"),
        ".pdf": (PyPDFLoader, {}, "PDF"),
        ".txt": (TextLoader, {}, "Text"),
    }
    # Markdown/HTML need the optional `unstructured` package; register them only
    # when it is importable so the supported-format list matches runtime reality.
    if _UNSTRUCTURED_AVAILABLE:
        _loader_configs.update(
            {
                ".htm": (UnstructuredHTMLLoader, {}, "HTML"),
                ".html": (UnstructuredHTMLLoader, {}, "HTML"),
                ".markdown": (UnstructuredMarkdownLoader, {}, "Markdown"),
                ".md": (UnstructuredMarkdownLoader, {}, "Markdown"),
            }
        )
```

```python
# unified_kg_rag/adapters/ingestion/parser.py, lines 127-161
    def parse_file(
        self, file_path: str | Path, index_value: str | None = None
    ) -> Document:
        try:
            try:
                langchain_docs = self._load_with_encoding(file_path, None)
            except Exception as exc:
                # Non-UTF-8 file: detect and retry instead of dropping it. A
                # whole non-UTF-8 corpus would otherwise fail 100% silently.
                if not (
                    issubclass(self.loader_class, _ENCODING_AWARE_LOADERS)
                    and self._is_decode_error(exc)
                ):
                    raise
                detected = self._detect_encoding(file_path) or "latin-1"
                langchain_docs = self._load_with_encoding(file_path, detected)
            document = convert_langchain_to_document(
                langchain_docs, file_path, index_value=index_value
            )

            if (
                document.content
                and hasattr(document.content, "text")
                and isinstance(document.content.text, str)
                and document.content.text.strip() == ""
            ):
                raise DataProcessingError(
                    f"Parsed text is empty for '{self.file_type_name}' '{file_path}'"
                )

            return document
        except Exception as e:
            raise DataProcessingError(
                f"Failed to parse '{self.file_type_name}' '{file_path}': {e}"
            ) from e
```

**[RAN]** In the session's environment the optional `unstructured` package was not installed, so the supported list was `.csv`, `.json`, `.pdf`, `.txt`.

### 4.6 Stage 2, document loading

```python
# unified_kg_rag/application/ingestion/pipeline_stages.py, lines 291-350
    def _execute_core(
        self, context: PipelineContext
    ) -> tuple[int, int, dict[str, Any] | None]:
        logger.info("=" * 60)
        logger.info("DOCUMENT LOADING STAGE - STARTED")
        logger.info("=" * 60)

        failed_files: list[str] = []
        if self._parsing_completed(context):
            documents = list(context.documents)
            input_count = len(documents)
            logger.info(
                "Using %s documents from the '%s' stage",
                input_count,
                PipelineStageType.DOCUMENT_PARSING.value,
            )
            if self.loader.deduplicate:
                documents = self.loader.deduplicate_documents(documents)
        else:
            discovered_files = self.loader.discover_files()
            input_count = len(discovered_files)
            documents = self.loader.load()
            for document in documents:
                assign_document_identity(
                    document,
                    self.loader.source_directory,
                    self.config.indexing.additional_suffix,
                )
            failed_files = self.loader.failed_files
            context.failed_source_files = list(failed_files)

        # Incremental indexing: when the DynamoDB doc-status registry is enabled,
        # diff against it, stash the delta/fingerprints for the IndexingStage, and
        # process only new/changed documents.
        delta_skipped = 0
        if self.config.aws.dynamodb.enabled:
            documents, delta_skipped = self._apply_incremental_filter(
                documents, context
            )

        context.documents = documents
        output_count = len(context.documents)

        if failed_files:
            logger.warning("Failed to load %s files", len(failed_files))

        metrics = {
            "file_count": input_count,
            "success_count": output_count,
            "delta_skipped": delta_skipped,
            "failed_files": failed_files,
        }

        logger.info("=" * 60)
        logger.info(
            "DOCUMENT LOADING STAGE - COMPLETED (%s documents loaded)", output_count
        )
        logger.info("=" * 60)

        return input_count, output_count, metrics
```

**[READ]** When parsing already completed in this run, loading does not read the folder again. It reuses `context.documents`, and removes duplicates only if `self.loader.deduplicate` is on. That flag comes from `processing.deduplicate`, which defaults to `False`:

```python
# unified_kg_rag/domain/models/config.py, lines 998-1014
    ignore_errors: bool = Field(
        default=False,
        description="Ignore errors and continue processing",
    )
    deduplicate: bool = Field(
        default=False, description="Enable document deduplication"
    )
    resolution_method: ResolutionMethod = Field(
        default=ResolutionMethod.MINHASH,
        description="Entity/relationship resolution method",
    )
    similarity_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Similarity threshold for entity/relationship resolution",
    )
```

**[READ]** If the DynamoDB option is on, loading also filters the documents down to new or changed ones (lines 325 to 329, and `_apply_incremental_filter` at lines 360 to 419). **[NOT CHECKED]** That path was never run; DynamoDB is off by default.

### 4.7 The first real run

**[RAN]** `reproduce/scripts/step3.py`, five documents, stages 1 and 2:

```text
--- calling p.run('docs') ---
CHECKPOINT  1: -> DataIngestionPipeline.run
CHECKPOINT  2: -> DataIngestionPipeline._resolve_pipeline_id
              returned: 'pipeline-46b42b42-20261011_052246'
CHECKPOINT  3: -> DataIngestionPipeline._compute_corpus_fingerprint
              returned: '70f976b347ba'
CHECKPOINT  4: -> DataIngestionPipeline._prepare_new_run
              returned: ('start stage =', 'document_parsing', '| context.documents =', [])
CHECKPOINT  5: -> DataIngestionPipeline._execute_pipeline_stages
CHECKPOINT  6: -> DataIngestionPipeline._execute_stage
CHECKPOINT  7: -> DocumentParsingStage._execute_core
CHECKPOINT  8: -> DocumentParsingStage._discover_files
              returned: ['01_acme.txt', '02_meera.txt', '03_orbit.txt', '04_product.txt', '05_investor.txt']
              returned: (5, 5, {'input_files': 5, 'parsed_files': ['01_acme.txt', '02_meera.txt', '03_orbit.txt', '04_product.txt',...
CHECKPOINT  9: -> DataIngestionPipeline._save_stage_outputs_to_cache
              returned: ('document_parsing', 'completed', 'in', 5, 'out', 5)
CHECKPOINT 10: -> DataIngestionPipeline._execute_stage
CHECKPOINT 11: -> DocumentLoadingStage._execute_core
              returned: (5, 5, {'file_count': 5, 'success_count': 5, 'delta_skipped': 0, 'failed_files': []})
CHECKPOINT 12: -> DataIngestionPipeline._save_stage_outputs_to_cache
              returned: ('document_loading', 'completed', 'in', 5, 'out', 5)
CHECKPOINT 13: -> DataIngestionPipeline._finalize_pipeline_execution
--- run() returned ---
pipeline_id : pipeline-46b42b42-20261011_052246
status      : completed
documents   : 5

FIRST DOCUMENT, field by field:
  page_content     = 'Acme Robotics is a company based in Pune. It was founded by Meera Shah in 2015. Acme builds warehouse robo...
  document_id      = '794e7e5b-edab-54aa-89e4-d0c34407471e'
  file_name        = '01_acme.txt'
  file_path        = 'docs/01_acme.txt'
  file_type        = 'txt'
  detected_language = 'Unknown'
  total_pages      = 1
  pages            = [{'page_number': 1, 'height': None, 'width': None, 'text_content': 'Acme Robotics is a company based in Pun...
  elements         = []
  content          = {'text': 'Acme Robotics is a company based in Pune. It was founded by Meera Shah in 2015. Acme builds wareh...
  metadata         = {'source': 'docs/01_acme.txt', 'relative_path': '01_acme.txt', 'registry_namespace': 'default'}
  error_info       = None

FILES NOW ON DISK under cache/:
  cache/pipeline-46b42b42-20261011_052246/cache_index.json  (1453 bytes)
  cache/pipeline-46b42b42-20261011_052246/document_loading/documents-76101e2dcda9.json  (5545 bytes)
  cache/pipeline-46b42b42-20261011_052246/document_parsing/documents-2e1fc5080839.json  (5545 bytes)
  cache/pipeline-46b42b42-20261011_052246/pipeline_metadata.json  (3134 bytes)
RUN1=pipeline-46b42b42-20261011_052246
```

Four files are written. `pipeline_metadata.json` is the run's logbook:

```text
{
  "pipeline_id": "pipeline-46b42b42-20261011_052246",
  "config": {
    "stages_enabled": {
      "document_parsing": true,
      "document_loading": true,
      "text_chunking": false,
      "translation": false,
      "graph_extraction": false,
      "gleaning": false,
      "graph_resolution": false,
      "claim_extraction": false,
      "claim_resolution": false,
      "graph_analysis": false,
      "community_detection": false,
      "indexing": false
    },
    "cache_enabled": true,
    "local_directory": "cache",
    "s3_sync_enabled": false,
    "s3_prefix": "pipeline-runs",
    "continue_on_error": false,
    "force_rebuild": false
  },
  "status": "completed",
  "start_time": "2026-10-11T05:22:46.125979",
  "end_time": "2026-10-11T05:22:46.135074",
  "duration_seconds": 0.008718252182006836,
  "source_directory": "/tmp/claude-0/-home-claude/bc133111-51e4-5491-aaed-c6588835038c/scratchpad/handoff_run/docs",
  "stage_results": [
    {
      "stage_name": "document_parsing",
      "status": "completed",
      "start_time": "2026-10-11T05:22:46.127510",
      "end_time": "2026-10-11T05:22:46.129119",
      "duration_seconds": 0.001609,
      "input_count": 5,
      "output_count": 5,
      "metrics": {
        "input_files": 5,
        "parsed_files": [
          "01_acme.txt",
          "02_meera.txt",
          "03_orbit.txt",
          "04_product.txt",
          "05_investor.txt"
        ],
        "failed_files": [],
        "success_rate": 100.0
      }
    },
    {
      "stage_name": "document_loading",
      "status": "completed",
      "start_time": "2026-10-11T05:22:46.132175",
      "end_time": "2026-10-11T05:22:46.132299",
      "duration_seconds": 0.000124,
      "input_count": 5,
      "output_count": 5,
      "metrics": {
        "file_count": 5,
        "success_count": 5,
        "delta_skipped": 0,
        "failed_files": []
      }
    }
  ],
  "global_metrics": {
    "pipeline_id": "pipeline-46b42b42-20261011_052246",
    "total_duration_seconds": 0.008718252182006836,
    "total_documents_processed": 5,
    "total_text_units_created": 0,
    "total_translated_units": 0,
    "total_entities_extracted": 0,
    "total_relationships_extracted": 0,
    "total_claims_extracted": 0,
    "total_communities_detected": 0,
    "total_community_reports_generated": 0,
    "total_items_indexed": 0,
    "total_items_index_failed": 0,
    "relationships_indexed": 0,
    "total_extraction_failures": 0,
    "total_gleaning_failures": 0,
    "total_claim_extraction_failures": 0,
    "gleaning_improvement_rate": 0.0,
    "entity_resolution_merge_rate": 0.0,
    "relationship_resolution_merge_rate": 0.0,
    "claim_resolution_merge_rate": 0.0,
    "community_modularity_score": 0.0,
    "stage_durations": {
      "document_parsing": 0.001609,
      "document_loading": 0.000124
    },
    "stage_throughput": {
      "document_parsing": 3107.520198881293,
      "document_loading": 40322.58064516129
    },
    "cache_hit_rate": 0.0,
    "cache_size_mb": 0.010576248168945312
  },
  "incremental_fingerprints": {},
  "failed_source_files": [],
  "failed_text_unit_ids": {}
}
```

**[READ]** The documents themselves are not in that file. These fields are excluded on purpose, and live in the per-stage output files instead:

```python
# unified_kg_rag/shared/pipeline_manager.py, lines 50-68
class PipelineStateManager:
    PIPELINE_METADATA_FILE = "pipeline_metadata.json"
    EXCLUDED_DATA_FIELDS = {
        "centrality_metrics",
        "claims",
        "communities",
        "community_reports",
        "documents",
        "entities",
        "graph",
        "graph_statistics",
        "knowledge_graph",
        "relationships",
        "resolved_claims",
        "resolved_entities",
        "resolved_relationships",
        "text_units",
        "translated_units",
    }
```

---

## 5. Run IDs, reruns and resume

### 5.1 How a run ID is made

```python
# unified_kg_rag/application/ingestion/pipeline.py, lines 402-427
    def _resolve_pipeline_id(
        self, source_directory: Path, pipeline_id: str | None
    ) -> str:
        return (
            pipeline_id
            or self.pipeline_config.pipeline_id
            or self._generate_pipeline_id(source_directory)
        )

    @staticmethod
    def _generate_pipeline_id(source_directory: Path | None = None) -> str:
        if source_directory is None:
            return f"pipeline-{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        subdirs = [
            str(path.relative_to(source_directory))
            for path in source_directory.rglob("*")
            if path.is_dir()
        ]

        subdirs.sort()
        directory_identifier = "_".join(subdirs) if subdirs else source_directory.name
        directory_hash = compute_hash(directory_identifier, length=8)

        return f"pipeline-{directory_hash}-{timestamp}"
```

**[READ]** If no ID is passed, one is generated: the word `pipeline`, an 8-character hash of the source folder's subfolder names (or of the folder's own name if it has no subfolders), and the current date and time to the second.

**[RAN]** For a folder named `docs` with no subfolders the middle part is always `46b42b42`. Only the timestamp differs between runs. A generated ID therefore never matches an earlier run.

### 5.2 The resume decision

```python
# unified_kg_rag/application/ingestion/pipeline.py, lines 340-367
            # force_rebuild must ignore ALL existing cache: skip the resume path
            # entirely so the run re-executes from the beginning even when a
            # prior metadata file exists (FORCE_REFRESH alone only bypasses
            # per-stage cache reads, not the resume decision).
            can_resume = (
                resolved_pipeline_id
                and not self.pipeline_config.force_rebuild
                and self.state_manager.pipeline_exists(resolved_pipeline_id)
            )
            if can_resume:
                logger.info(
                    "Resuming existing pipeline '%s' from stage: '%s'",
                    resolved_pipeline_id,
                    resolved_resume_stage or "auto-detect",
                )
                context, start_stage_name = self._prepare_resume(
                    resolved_pipeline_id, resolved_resume_stage
                )
            else:
                if self.pipeline_config.force_rebuild:
                    logger.info(
                        "Force rebuild: ignoring any existing cache for '%s'",
                        resolved_pipeline_id,
                    )
                logger.info("Starting new pipeline run: '%s'", resolved_pipeline_id)
                context, start_stage_name = self._prepare_new_run(
                    source_path, resolved_pipeline_id, resolved_resume_stage
                )
```

All three parts of `can_resume` must be true: there is an ID (always true); `--force-rebuild` was not given; and a saved record exists for that ID.

```python
# unified_kg_rag/shared/pipeline_manager.py, lines 88-93
    def pipeline_exists(self, pipeline_id: str) -> bool:
        metadata_path = (
            self.cache_manager.get_pipeline_cache_dir(pipeline_id)
            / self.PIPELINE_METADATA_FILE
        )
        return metadata_path.exists() and metadata_path.stat().st_size > 0
```

**[READ]** There is no separate resume command. Resume means running `run-ingestion` again with the old ID, through `--pipeline-id` or the environment variable `GRAPHRAG_PIPELINE_ID` (`run_ingestion_pipeline.py`, lines 97 to 103), with the same cache folder and without `--force-rebuild`.

### 5.3 Four rerun scenarios

**[RAN]** `reproduce/scripts/step4.py`. Scenario D first appends one sentence to `docs/01_acme.txt`.

```text

=== A: run again, no pipeline id given ===
  1. pipeline id        : pipeline-46b42b42-20261011_052301
  2. not force_rebuild  : True
  3. metadata file found: False
  corpus fingerprint    : 70f976b347ba
  path taken      : NEW RUN -> start stage = document_parsing
  stages that actually ran: ['document_parsing', 'document_loading'] | documents in context: 5

=== B: run again, SAME pipeline id, nothing changed ===
  1. pipeline id        : pipeline-46b42b42-20261011_052246
  2. not force_rebuild  : True
  3. metadata file found: True
  corpus fingerprint    : 70f976b347ba
  path taken      : RESUME  -> start stage = document_loading
  stages that actually ran: ['document_loading'] | documents in context: 5

=== C: SAME pipeline id + force_rebuild ===
  1. pipeline id        : pipeline-46b42b42-20261011_052246
  2. not force_rebuild  : False
  3. metadata file found: True
  corpus fingerprint    : 70f976b347ba
  path taken      : NEW RUN -> start stage = document_parsing
  stages that actually ran: ['document_parsing', 'document_loading'] | documents in context: 5

=== D: SAME pipeline id, but I edited 01_acme.txt ===
  1. pipeline id        : pipeline-46b42b42-20261011_052246
  2. not force_rebuild  : True
  3. metadata file found: True
  corpus fingerprint    : 11e583bd8e55
  path taken      : RESUME  -> start stage = document_parsing
  stages that actually ran: ['document_parsing', 'document_loading'] | documents in context: 5
run folders now:
pipeline-46b42b42-20261011_052246
pipeline-46b42b42-20261011_052301
```

| Scenario | Saved record found | Path | Stages that ran |
|---|---|---|---|
| A. No ID given | No, a new ID was generated | New run | Parsing, loading |
| B. Same ID, nothing changed | Yes | Resume from loading | Loading only |
| C. Same ID plus force rebuild | Yes | New run | Parsing, loading |
| D. Same ID, one file edited | Yes | Resume from parsing | Parsing, loading |

### 5.4 The code each scenario goes through

The resume path, once `can_resume` is true:

```python
# unified_kg_rag/application/ingestion/pipeline.py, lines 461-526
    def _prepare_resume(
        self, pipeline_id: str, resume_from_stage: str | None
    ) -> tuple[PipelineContext, str | None]:
        logger.info(
            "Preparing pipeline resume for '%s' from stage: '%s'",
            pipeline_id,
            resume_from_stage or "auto-detect",
        )

        try:
            start_stage_name, completed_stages = (
                self.resume_manager.determine_resume_strategy(
                    pipeline_id, resume_from_stage
                )
            )

            context = self.resume_manager.restore_pipeline_context(
                pipeline_id, completed_stages
            )

            self._prepare_context_for_resume(context, start_stage_name)

            logger.info(
                "Pipeline resume prepared successfully - will start from stage: '%s'",
                start_stage_name,
            )
            return context, start_stage_name
        except (PipelineResumeError, PipelineStateError) as e:
            logger.error(
                "Failed to prepare resume for pipeline '%s': %s", pipeline_id, e
            )
            raise PipelineExecutionError(f"Pipeline resume failed: {e}") from e

    def _prepare_context_for_resume(
        self, context: PipelineContext, start_stage_name: str
    ) -> None:
        # Order by the canonical pipeline sequence (STAGE_CLASSES), NOT the
        # enabled-stage subset: phased execution narrows self.stages to one
        # phase's window (e.g. just ["indexing"]), so judging "is this an
        # upstream result?" against that subset would wrongly discard every
        # earlier phase's results — silently dropping resolved_relationships /
        # resolved_claims before indexing. The full order keeps them.
        canonical_order = [st.value for st in self.STAGE_CLASSES]
        try:
            start_index = canonical_order.index(start_stage_name)
        except ValueError:
            logger.warning(
                "Start stage '%s' not in canonical pipeline order; "
                "keeping all %s previous stage results",
                start_stage_name,
                len(context.stage_results),
            )
            return

        valid_results = [
            res
            for res in context.stage_results
            if res.stage_name in canonical_order
            and canonical_order.index(res.stage_name) < start_index
        ]
        context.stage_results = valid_results
        logger.info(
            "Context prepared for resume from '%s' - keeping %s previous stage results",
            start_stage_name,
            len(valid_results),
        )
```

```python
# unified_kg_rag/shared/pipeline_manager.py, lines 385-434
    def determine_resume_strategy(
        self, pipeline_id: str, explicit_stage: str | None = None
    ) -> tuple[str, list[str]]:
        logger.info(
            "Determining resume strategy for pipeline '%s'%s",
            pipeline_id,
            f" from stage: {explicit_stage}" if explicit_stage else "",
        )

        try:
            metadata = self.state_manager.load_pipeline_metadata(pipeline_id)
            stage_results = metadata.get("stage_results", [])

            if explicit_stage:
                start_stage, completed_stages = self._handle_explicit_stage_resume(
                    stage_results, explicit_stage
                )
            else:
                start_stage, completed_stages = self._handle_auto_resume(stage_results)

            # A recorded "completed" only stands for output the cache still
            # holds. Cache keys carry a fingerprint of the inputs that produced
            # the output, so a changed model or prompt (or a cache written
            # under the pre-fingerprint keys) leaves the status in place while
            # the output becomes unreachable. Scheduling from the status alone
            # would then start downstream of the stale stage on an empty
            # context, so the resume point is derived from what the cache
            # verifiably holds.
            result = self._verify_completed_stages_against_cache(
                pipeline_id, start_stage, completed_stages, explicit_stage
            )

            logger.info(
                "Resume strategy determined - Start from: '%s', Load %s completed stages",
                result[0],
                len(result[1]),
            )
            return result

        except PipelineResumeError:
            raise
        except Exception as e:
            logger.error(
                "Failed to determine resume strategy for pipeline '%s': %s",
                pipeline_id,
                e,
            )
            raise PipelineResumeError(
                f"Failed to determine resume strategy for pipeline '{pipeline_id}': {e}"
            ) from e
```

Where the old run got to:

```python
# unified_kg_rag/shared/pipeline_manager.py, lines 469-486
    @staticmethod
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

Whether each completed stage's saved output is still there under the current inputs:

```python
# unified_kg_rag/shared/pipeline_manager.py, lines 488-559
    def _verify_completed_stages_against_cache(
        self,
        pipeline_id: str,
        start_stage: str,
        completed_stages: list[str],
        explicit_stage: str | None,
    ) -> tuple[str, list[str]]:
        """Keep only the completed prefix whose output the cache still holds.

        Walks the completed stages in canonical order and stops at the first
        one with no cached output under the current inputs. An auto resume
        moves its start back to that stage, so it and every stage downstream
        of it are recomputed. An explicit resume names its start and, in a
        phased run, may not have the upstream stages in its window, so it
        fails here instead of running downstream stages on an empty context.
        """
        for stage_name in sorted(completed_stages, key=_canonical_index):
            missing = self._missing_cache_keys(pipeline_id, stage_name)
            if not missing:
                continue

            self._log_unbacked_stage(pipeline_id, stage_name, missing)

            if explicit_stage:
                missing_keys = ", ".join(f"'{key}'" for _, key in missing)
                message = (
                    f"Cannot resume from '{explicit_stage}': upstream stage "
                    f"'{stage_name}' is recorded completed, but the cache does not "
                    f"hold its output under the current inputs (missing "
                    f"{missing_keys}). Resume from '{stage_name}' to recompute it, "
                    f"or force a rebuild."
                )
                logger.error(message)
                raise PipelineResumeError(message)

            verified = [
                name
                for name in completed_stages
                if _canonical_index(name) < _canonical_index(stage_name)
            ]
            logger.warning(
                "Rewinding resume point from '%s' to '%s': it and every stage "
                "downstream of it will be recomputed",
                start_stage,
                stage_name,
            )
            return stage_name, verified

        return start_stage, completed_stages

    def _missing_cache_keys(
        self, pipeline_id: str, stage_name: str
    ) -> list[tuple[str, str]]:
        """List ``(context_attr, cache_key)`` for each output of ``stage_name``
        the cache does not hold under the current inputs.

        A stage with no cache mapping (document_parsing, indexing) produces
        nothing the resume reads back, so there is nothing to verify.
        """
        try:
            stage_type = PipelineStageType(stage_name)
        except ValueError:
            return []

        missing = []
        for context_attr in self.STAGE_CACHE_MAPPING.get(stage_type, {}):
            cache_key = stage_cache_key(
                self.config, stage_type, context_attr, self.corpus_fingerprint
            )
            if not self.cache_manager.cache_exists(cache_key, pipeline_id):
                missing.append((context_attr, cache_key))
        return missing
```

Loading the saved outputs back into the context:

```python
# unified_kg_rag/shared/pipeline_manager.py, lines 589-670
    def restore_pipeline_context(
        self, pipeline_id: str, completed_stages: list[str]
    ) -> PipelineContext:
        logger.info(
            "Restoring pipeline context for '%s' with %s completed stages",
            pipeline_id,
            len(completed_stages),
        )

        try:
            metadata = self.state_manager.load_pipeline_metadata(pipeline_id)
            context = self.state_manager.create_context_from_metadata(metadata)
            loaded_count = 0

            for stage_name in completed_stages:
                try:
                    if self._load_stage_cache_data(pipeline_id, stage_name, context):
                        loaded_count += 1
                except Exception as e:
                    logger.error(
                        "Error loading cache for stage '%s': %s", stage_name, e
                    )

            logger.info(
                "Context restoration completed for '%s': %s/%s stages loaded",
                pipeline_id,
                loaded_count,
                len(completed_stages),
            )
            return context

        except Exception as e:
            logger.error(
                "Failed to restore pipeline context for '%s': %s", pipeline_id, e
            )
            raise PipelineResumeError(
                f"Failed to restore pipeline context for '{pipeline_id}': {e}"
            ) from e

    def _load_stage_cache_data(
        self, pipeline_id: str, stage_name: str, context: PipelineContext
    ) -> bool:
        try:
            stage_type = PipelineStageType(stage_name)
            cache_mapping = self.STAGE_CACHE_MAPPING.get(stage_type, {})
        except ValueError:
            return True

        if not cache_mapping:
            return True

        loaded_files_count = 0

        for context_attr, _ in cache_mapping.items():
            try:
                model_class = self.CONTEXT_ATTR_TO_MODEL.get(context_attr)
                data: Any = self.cache_manager.load_stage_result(
                    cache_key=stage_cache_key(
                        self.config, stage_type, context_attr, self.corpus_fingerprint
                    ),
                    pipeline_id=pipeline_id,
                    data_type=model_class if model_class else None,
                )

                if data is not None:
                    setattr(context, context_attr, data)
                    loaded_files_count += 1
                else:
                    logger.warning(
                        "Cache data not found for stage '%s': '%s'",
                        stage_name,
                        context_attr,
                    )
            except Exception as e:
                logger.error(
                    "Failed to load cache data '%s' for stage '%s': %s",
                    context_attr,
                    stage_name,
                    e,
                )

        return loaded_files_count > 0
```

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

```python
# unified_kg_rag/shared/utils/cache_keys.py, lines 238-306
def stage_input_fingerprint(
    config: Config,
    stage_type: PipelineStageType,
    corpus_fingerprint: str | None = None,
) -> str:
    """Fingerprint the configuration that determines ``stage_type``'s output.

    Args:
        config: The active framework configuration.
        stage_type: Ingestion stage whose inputs are being fingerprinted.
        corpus_fingerprint: :func:`corpus_manifest_fingerprint` of the run's
            source corpus. Every stage consumes the corpus (directly or through
            its predecessors), so it is folded into every key. ``None`` leaves
            the key a function of the configuration only.

    Returns:
        A short hex digest, identical for two equal configurations and
        different as soon as any output-determining input changes.

    Example:
        >>> fp = stage_input_fingerprint(Config(), PipelineStageType.TEXT_CHUNKING)
        >>> len(fp)
        12
    """
    projection: list[tuple[str, Any]] = []
    for path in _input_paths_through(stage_type):
        value = _canonicalize(_resolve_path(config, path))
        if path in _NON_OUTPUT_SUBFIELDS and isinstance(value, dict):
            value = {
                k: v for k, v in value.items() if k not in _NON_OUTPUT_SUBFIELDS[path]
            }
        if path in _OMIT_WHEN_DEFAULT and value == _OMIT_WHEN_DEFAULT[path]:
            continue
        projection.append((path, value))
    if corpus_fingerprint is not None:
        projection.append(("corpus_manifest", corpus_fingerprint))
    payload = json.dumps(projection, sort_keys=True, default=str)
    return compute_hash(payload, length=FINGERPRINT_LENGTH)


def stage_cache_key(
    config: Config,
    stage_type: PipelineStageType,
    context_attr: str,
    corpus_fingerprint: str | None = None,
) -> str:
    """Build the cache key for one stage output.

    Args:
        config: The active framework configuration.
        stage_type: Ingestion stage that produces (or produced) the output.
        context_attr: ``PipelineContext`` attribute holding the output, e.g.
            "documents" or "resolved_entities".
        corpus_fingerprint: The run's corpus manifest fingerprint (see
            :func:`stage_input_fingerprint`).

    Returns:
        The context attribute suffixed with the stage's input fingerprint, so a
        configuration change reads as a cache miss instead of a stale hit.

    Example:
        >>> key = stage_cache_key(
        ...     Config(), PipelineStageType.DOCUMENT_LOADING, "documents"
        ... )
        >>> key.startswith("documents-")
        True
    """
    fingerprint = stage_input_fingerprint(config, stage_type, corpus_fingerprint)
    return f"{context_attr}-{fingerprint}"
```

Which settings count for which stage:

```python
# unified_kg_rag/shared/utils/cache_keys.py, lines 69-122
_STAGE_INPUT_PATHS: dict[PipelineStageType, tuple[str, ...]] = {
    PipelineStageType.DOCUMENT_PARSING: (
        "processing.document_parsing",
        "processing.ignore_errors",
        "fixing",
        # LLM knobs that change generated content. Region, role and profile
        # routing are excluded: they change WHERE the call goes, not its output.
        "aws.bedrock.effort",
        "aws.bedrock.fast_effort",
        "aws.bedrock.enable_1m_context",
        "aws.bedrock.guardrail",
        # The per-request output cap truncates long generations, and per-model
        # overrides change a model's capabilities (output cap, effort support).
        "aws.bedrock.default_max_output_tokens",
        "aws.bedrock.model_overrides",
    ),
    PipelineStageType.DOCUMENT_LOADING: ("processing.deduplicate",),
    PipelineStageType.TEXT_CHUNKING: ("processing.chunking",),
    PipelineStageType.TRANSLATION: ("processing.translation",),
    PipelineStageType.GRAPH_EXTRACTION: (
        "processing.graph_extraction",
        "custom_prompts.graph_extraction_system",
        "custom_prompts.graph_extraction_human",
        "custom_prompts.description_summarization_system",
        "custom_prompts.description_summarization_human",
    ),
    PipelineStageType.GLEANING: (
        "processing.gleaning",
        "custom_prompts.graph_refinement_system",
        "custom_prompts.graph_refinement_human",
    ),
    PipelineStageType.GRAPH_RESOLUTION: (
        "processing.resolution_method",
        "processing.similarity_threshold",
    ),
    PipelineStageType.CLAIM_EXTRACTION: (
        "processing.claim_extraction",
        "custom_prompts.claim_extraction_system",
        "custom_prompts.claim_extraction_human",
    ),
    # Claim resolution reuses the resolution knobs already folded in upstream.
    PipelineStageType.CLAIM_RESOLUTION: (),
    # Graph analysis caches the resolved entities and relationships it passes
    # through; `graph.analysis` only shapes centrality and statistics, which
    # no later stage reads (visualization recomputes them), so it is not an
    # output-determining input of this stage or any later one.
    PipelineStageType.GRAPH_ANALYSIS: (),
    PipelineStageType.COMMUNITY_DETECTION: (
        "graph.community_detection",
        "custom_prompts.community_report_system",
        "custom_prompts.community_report_human",
    ),
    PipelineStageType.INDEXING: ("indexing",),
}
```

**[READ]** The module's own header notes a limit: built-in prompt templates are code, so editing one does not change the fingerprint (lines 38 to 40).

### 6.2 The folder fingerprint

```python
# unified_kg_rag/shared/utils/cache_keys.py, lines 195-235
def corpus_manifest_fingerprint(
    source_directory: str | Path,
    extensions: Iterable[str],
    exclude_directories: Iterable[str | Path] = (),
) -> str:
    """Fingerprint the corpus contents under ``source_directory``.

    Every file the pipeline could ingest contributes its path relative to the
    source root, its size, and a SHA-256 of its bytes. Modification times are
    deliberately not used: an ``aws s3 sync`` into a fresh container or a new
    checkout changes them without changing the content, which would turn every
    phase handoff into a cache miss.

    Args:
        source_directory: Corpus root.
        extensions: File suffixes the pipeline ingests (case-insensitive).
        exclude_directories: Directories the pipeline writes into (cache,
            parsed-JSON export), skipped so its own output never changes the
            fingerprint mid-run.

    Returns:
        A short hex digest; an empty or missing corpus has a fixed digest.
    """
    root = Path(source_directory).resolve()
    suffixes = {ext.lower() for ext in extensions}
    excluded = [Path(d).resolve() for d in exclude_directories]
    entries: list[str] = []
    if root.is_dir():
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root)
            if (
                not path.is_file()
                or path.suffix.lower() not in suffixes
                or any(part.startswith(".") for part in relative.parts)
                or any(path.resolve().is_relative_to(d) for d in excluded)
            ):
                continue
            entries.append(
                f"{relative.as_posix()}\t{path.stat().st_size}\t{_file_digest(path)}"
            )
    return compute_hash("\n".join(entries), length=FINGERPRINT_LENGTH)
```

**[READ]** One line per source file: relative path, size in bytes, SHA-256 of the contents. Modification times are deliberately not used.

**[RAN]** Recomputed by hand for the five documents after the edit (`reproduce/scripts/manifest_demo.py`). The result matches what the pipeline logged:

```text
   01_acme.txt	134	623c55d166e165754cf9adbf1f27b7302ca6240e153d...
   02_meera.txt	117	9db18212845c2e25a48c647ade110cd96c8bd35f7b3...
   03_orbit.txt	124	62cfcca68978b7eeb429b98d84a38e55ee51d6f9f2f...
   04_product.txt	125	c4af8543b454d6f30faae748243955dc9570dbb40...
   05_investor.txt	115	22184e971586f5f453ce6d020177149faf9ae000...
  fingerprint = 11e583bd8e55
```

**[RAN]** The fingerprint was `70f976b347ba` for the five original documents and `11e583bd8e55` after one sentence was appended to `01_acme.txt`.

**[READ]** The pipeline does not compare old and new files and does not know which file changed. It only finds that the file names it expects no longer exist.

### 6.3 Saving

```python
# unified_kg_rag/application/ingestion/pipeline.py, lines 647-731
    def _save_stage_outputs_to_cache(
        self, context: PipelineContext, stage_name: str
    ) -> None:
        if not self.pipeline_config.cache_enabled:
            logger.info(
                "Cache disabled, skipping output save for stage: '%s'", stage_name
            )
            return

        stage_type = self.name_to_type_map.get(stage_name)
        if not stage_type or stage_type not in self.STAGE_OUTPUT_MAPPING:
            logger.info(
                "No output mapping found for stage: '%s', skipping cache save",
                stage_name,
            )
            return

        try:
            saved_outputs = []
            for _, (_, context_attr) in self.STAGE_OUTPUT_MAPPING[stage_type].items():
                data_to_save = getattr(context, context_attr, None)
                # An empty list is still this stage's output under these
                # inputs (translation is off by default and completes with no
                # translated units). It is saved so that the resume can tell
                # "produced nothing" from "not in the cache" and does not
                # rewind to this stage on every run.
                if data_to_save is None:
                    logger.debug(
                        "No data found for context attribute: %s", context_attr
                    )
                    continue

                logger.info(
                    "Saving %s %s to cache",
                    len(data_to_save) if isinstance(data_to_save, list) else 1,
                    context_attr,
                )

                # The key carries a fingerprint of the inputs that produced this
                # output, so a changed prompt/model/config reads as a miss on the
                # next run instead of silently resuming from stale output.
                cache_entry = self.cache_manager.save_stage_result(
                    data=data_to_save,
                    cache_key=stage_cache_key(
                        self.config,
                        stage_type,
                        context_attr,
                        self.corpus_fingerprint,
                    ),
                    stage_name=stage_name,
                    pipeline_id=context.pipeline_id,
                    metadata={
                        "stage_type": (
                            stage_type.value
                            if hasattr(stage_type, "value")
                            else str(stage_type)
                        ),
                        "context_attribute": context_attr,
                    },
                )

                if cache_entry:
                    item_count = cache_entry.record_count or (
                        len(data_to_save) if isinstance(data_to_save, list) else 1
                    )
                    chunked_info = ""
                    if getattr(cache_entry.metadata, "is_chunked", False):
                        chunk_count = getattr(cache_entry.metadata, "chunk_count", 0)
                        chunked_info = f" (chunked into {chunk_count} files)"

                    saved_outputs.append(f"{item_count} {context_attr}{chunked_info}")
                    logger.info("Successfully cached %s", context_attr)
                else:
                    logger.warning("Cache manager returned None for %s", context_attr)

            if saved_outputs:
                logger.info(
                    "Stage '%s' outputs cached: %s",
                    stage_name,
                    ", ".join(saved_outputs),
                )
        except Exception as e:
            logger.warning(
                "Failed to save outputs to cache for stage '%s': %s", stage_name, e
            )
```

```python
# unified_kg_rag/shared/cache_manager.py, lines 313-356
    def _save_single_file_data(
        self,
        data: Any,
        cache_key: str,
        stage_name: str,
        pipeline_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> CacheEntry:
        cache_directory = self.get_pipeline_cache_dir(pipeline_id)
        stage_cache_dir = cache_directory / stage_name
        stage_cache_dir.mkdir(parents=True, exist_ok=True)

        serialized_data = self.serialize_data(data)
        content_hash = compute_hash(serialized_data, length=16)
        cache_file = stage_cache_dir / f"{cache_key}.json"

        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(serialized_data)

        entry = CacheEntry(
            key=cache_key,
            stage_name=stage_name,
            pipeline_id=pipeline_id,
            local_path=cache_file,
            file_size=cache_file.stat().st_size,
            content_hash=content_hash,
            record_count=len(data) if isinstance(data, list) else 1,
            data_type=type(data).__name__,
            metadata={**(metadata or {}), "is_chunked": False},
            created_at=datetime.now(),
            expires_at=(
                datetime.now() + timedelta(seconds=self.ttl_seconds)
                if self.ttl_seconds is not None and self.ttl_seconds > 0
                else None
            ),
        )

        self._update_cache_index(entry)
        logger.info(
            "Cached single file for key '%s' (size: %s bytes)",
            cache_key,
            entry.file_size,
        )
        return entry
```

### 6.4 "Is it there?" and expiry

```python
# unified_kg_rag/shared/cache_manager.py, lines 58-70
    def cache_exists(self, cache_key: str, pipeline_id: str) -> bool:
        if self.strategy == CacheStrategy.FORCE_REFRESH:
            return False

        index = self.load_cache_index(pipeline_id)
        entry = index.get_entry(cache_key)
        if entry is None:
            return False

        if entry.metadata.get("is_chunked", False):
            return self._chunked_cache_exists(entry, pipeline_id)

        return entry.exists_locally and not entry.is_expired
```

```python
# unified_kg_rag/domain/models/cache.py, lines 56-60
    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
```

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

```text
similarity_threshold default: 0.6
changed to: 0.55 

stage                 before         after          still valid?
document_parsing      54cf4641e850   54cf4641e850   yes
document_loading      0842cedc0821   0842cedc0821   yes
text_chunking         9fcbd193c678   9fcbd193c678   yes
translation           64bc0bc08eed   64bc0bc08eed   yes
graph_extraction      6c874c6a9e71   6c874c6a9e71   yes
gleaning              6d3b14e6d688   6d3b14e6d688   yes
graph_resolution      7d5bce1ee591   cc32ecbec5bb   NO - redo
claim_extraction      cb31ed4487a5   7436faf6edaa   NO - redo
claim_resolution      cb31ed4487a5   7436faf6edaa   NO - redo
graph_analysis        cb31ed4487a5   7436faf6edaa   NO - redo
community_detection   3eb2cb6c0a1c   dc53a249bcdd   NO - redo
indexing              86550627de53   af93d04f9861   NO - redo
```

   Stages 1 to 6 keep their fingerprint. **[INFERRED]** A resume with the new value would reuse their saved outputs and redo stage 7 onward. A full 12-stage resume was never run.
3. **The run is split across machines [READ].** Comments in the code describe "phased execution", where separate tasks share one run ID through S3 (`pipeline.py` lines 497 to 502; `pipeline_manager.py` lines 145 to 151). **[NOT CHECKED]** The deployment code under `iac/` was not read.

---

## 7. The real command, run for real

### 7.1 Resume with nobody at the keyboard

**[RAN]** `run-ingestion --source-directory docs --pipeline-id <first run's ID> --enabled-stages DOCUMENT_PARSING,DOCUMENT_LOADING`, with standard input closed:

```text
exit code: 1
│ Built by AWS Professional Services | Version 0.2.3                        │
│ Graph RAG Document Processing Pipeline                                       │
│ Source Directory:                                                            │
│ '/tmp/claude-0/-home-claude/bc133111-51e4-5491-aaed-c6588835038c/scratchpad/ │
│ handoff_run/docs'                                                            │
│ Timestamp: '2026-10-11 05:23:16'                                             │
│ Cache Directory:                                                             │
│ '/tmp/claude-0/-home-claude/bc133111-51e4-5491-aaed-c6588835038c/scratchpad/ │
│ handoff_run/cache'                                                           │
│ Force Rebuild: False                                                         │
│ S3 Sync: False                                                               │
│ Continue on Error: False                                                     │
│ Pipeline ID: 'pipeline-46b42b42-20261011_052246'                             │
│ Resume Mode: 'Auto-detect Failed/Incomplete Stage'                           │
Initializing pipeline...
LOG: Initialized Cache Manager at 'cache' with strategy='content_hash', TTL=86400s, chunk_size=1000, max_file_size=50MB, chunking_enabled=True
LOG: Disabled stages: ['text_chunking', 'translation', 'graph_extraction', 'gleaning', 'graph_resolution', 'claim_extraction', 'claim_resolution', 'graph_analysis', 'community_detection', 'indexing']
LOG: Successfully initialized pipeline with 2 stages: 'document_parsing, document_loading'
LOG: Validating pipeline integrity for 'pipeline-46b42b42-20261011_052246'
LOG: Missing cache for completed stage 'document_parsing', key: 'documents-1035b7a62512'
LOG: Missing cache for completed stage 'document_loading', key: 'documents-ac616352a4e7'
LOG: Pipeline integrity validation failed for 'pipeline-46b42b42-20261011_052246' with 2 errors
Pipeline integrity check failed for 'pipeline-46b42b42-20261011_052246':
• Missing cache for completed stage 'document_parsing', key:
'documents-1035b7a62512'
• Missing cache for completed stage 'document_loading', key:
'documents-ac616352a4e7'
Continue despite integrity issues? [y/n]:
An unexpected error occurred: EOF when reading a line
LOG: Unexpected error during pipeline execution
```

The command asks a question and, with nobody to answer, exits with code 1. This is bug 1.

### 7.2 Why the check fails

**[RAN]** The names the early check looks for, against the names really on disk (`reproduce/scripts/keys_demo.py`):

```text
parsing key, NO folder fingerprint : documents-1035b7a62512
parsing key, with 11e583bd8e55      : documents-54cf4641e850
loading key, NO folder fingerprint : documents-ac616352a4e7
loading key, with 11e583bd8e55      : documents-0842cedc0821
files on disk for RUN1:
cache/pipeline-46b42b42-20261011_052246/cache_index.json
cache/pipeline-46b42b42-20261011_052246/document_loading/documents-0842cedc0821.json
cache/pipeline-46b42b42-20261011_052246/document_loading/documents-76101e2dcda9.json
cache/pipeline-46b42b42-20261011_052246/document_parsing/documents-2e1fc5080839.json
cache/pipeline-46b42b42-20261011_052246/document_parsing/documents-54cf4641e850.json
cache/pipeline-46b42b42-20261011_052246/pipeline_metadata.json
```

**[READ]** The check builds names without the folder fingerprint, because at that point the fingerprint slot is still empty:

```python
# unified_kg_rag/shared/pipeline_manager.py, lines 370-383
    def __init__(
        self, state_manager: PipelineStateManager, config: Config | None = None
    ) -> None:
        self.state_manager = state_manager
        self.cache_manager = state_manager.cache_manager
        # Cache keys carry a fingerprint of the config that produced the stage
        # output, so resuming needs the same config the save path used. Omitting
        # it falls back to framework defaults, which fingerprints to a different
        # key for any customised run — a cache miss (recompute), never a stale
        # hit.
        self.config = config or Config()
        # Set by the pipeline once the run's corpus is known; folded into the
        # cache keys exactly as the save path folds it.
        self.corpus_fingerprint: str | None = None
```

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

```python
# unified_kg_rag/shared/pipeline_manager.py, lines 672-702
    def validate_pipeline_integrity(self, pipeline_id: str) -> tuple[bool, list[str]]:
        logger.info("Validating pipeline integrity for '%s'", pipeline_id)
        errors = []

        try:
            metadata = self.state_manager.load_pipeline_metadata(pipeline_id)
        except PipelineStateError as e:
            logger.error("Pipeline integrity validation failed: %s", e)
            return False, [str(e)]

        for result in metadata.get("stage_results", []):
            if result.get("status") != "completed":
                continue

            stage_name = result["stage_name"]
            for _, cache_key in self._missing_cache_keys(pipeline_id, stage_name):
                error_msg = (
                    f"Missing cache for completed stage '{stage_name}', "
                    f"key: '{cache_key}'"
                )
                errors.append(error_msg)
                logger.warning(error_msg)

        is_valid = not errors
        logger.info(
            "Pipeline integrity validation %s for '%s'%s",
            "passed" if is_valid else "failed",
            pipeline_id,
            f" with {len(errors)} errors" if not is_valid else "",
        )
        return is_valid, errors
```

### 7.3 Resume, answering "y"

**[RAN]** The same command with `y` piped in. The integrity prompt appears, then the real resume logic runs with the right names, skips parsing, and re-runs loading:

```text
exit code: 0
│ Built by AWS Professional Services | Version 0.2.3                        │
│ Graph RAG Document Processing Pipeline                                       │
│ Source Directory:                                                            │
│ '/tmp/claude-0/-home-claude/bc133111-51e4-5491-aaed-c6588835038c/scratchpad/ │
│ handoff_run/docs'                                                            │
│ Timestamp: '2026-10-11 05:23:31'                                             │
│ Cache Directory:                                                             │
│ '/tmp/claude-0/-home-claude/bc133111-51e4-5491-aaed-c6588835038c/scratchpad/ │
│ handoff_run/cache'                                                           │
│ Force Rebuild: False                                                         │
│ S3 Sync: False                                                               │
│ Continue on Error: False                                                     │
│ Pipeline ID: 'pipeline-46b42b42-20261011_052246'                             │
│ Resume Mode: 'Auto-detect Failed/Incomplete Stage'                           │
Initializing pipeline...
LOG: Initialized Cache Manager at 'cache' with strategy='content_hash', TTL=86400s, chunk_size=1000, max_file_size=50MB, chunking_enabled=True
LOG: Disabled stages: ['text_chunking', 'translation', 'graph_extraction', 'gleaning', 'graph_resolution', 'claim_extraction', 'claim_resolution', 'graph_analysis', 'community_detection', 'indexing']
LOG: Successfully initialized pipeline with 2 stages: 'document_parsing, document_loading'
LOG: Validating pipeline integrity for 'pipeline-46b42b42-20261011_052246'
LOG: Missing cache for completed stage 'document_parsing', key: 'documents-1035b7a62512'
LOG: Missing cache for completed stage 'document_loading', key: 'documents-ac616352a4e7'
LOG: Pipeline integrity validation failed for 'pipeline-46b42b42-20261011_052246' with 2 errors
Pipeline integrity check failed for 'pipeline-46b42b42-20261011_052246':
• Missing cache for completed stage 'document_parsing', key:
'documents-1035b7a62512'
• Missing cache for completed stage 'document_loading', key:
'documents-ac616352a4e7'
Continue despite integrity issues? [y/n]:
Starting pipeline execution...
LOG: Starting pipeline run - source: '/tmp/claude-0/-home-claude/bc133111-51e4-5491-aaed-c6588835038c/scratchpad/handoff_run/docs', pipeline_id: 'pipeline-46b42b42-20261011_052246', resume_from: 'auto-detect'
LOG: Resolved pipeline ID: 'pipeline-46b42b42-20261011_052246'
LOG: Corpus manifest fingerprint: '11e583bd8e55'
LOG: Resuming existing pipeline 'pipeline-46b42b42-20261011_052246' from stage: 'auto-detect'
LOG: Preparing pipeline resume for 'pipeline-46b42b42-20261011_052246' from stage: 'auto-detect'
LOG: Determining resume strategy for pipeline 'pipeline-46b42b42-20261011_052246'
LOG: Resume strategy determined - Start from: 'document_loading', Load 2 completed stages
LOG: Restoring pipeline context for 'pipeline-46b42b42-20261011_052246' with 2 completed stages
LOG: Created context from metadata for pipeline 'pipeline-46b42b42-20261011_052246' (status: PipelineStageStatus.COMPLETED -> running)
LOG: Context restoration completed for 'pipeline-46b42b42-20261011_052246': 2/2 stages loaded
LOG: Context prepared for resume from 'document_loading' - keeping 1 previous stage results
LOG: Pipeline resume prepared successfully - will start from stage: 'document_loading'
LOG: Found 1 previously completed stages: 'document_parsing'
LOG: Executing 1 stages: 'document_loading'
LOG: Executing stage: 'document_loading'
LOG: Pipeline metadata saved for 'pipeline-46b42b42-20261011_052246' (status: running)
LOG: Starting stage: 'document_loading'
LOG: DOCUMENT LOADING STAGE - STARTED
LOG: Using 5 documents from the 'document_parsing' stage
LOG: DOCUMENT LOADING STAGE - COMPLETED (5 documents loaded)
LOG: Stage 'document_loading' completed successfully in 0.00 seconds. Inputs: 5, Outputs: 5
LOG: Pipeline status updated: 'running' -> 'completed'
LOG: Pipeline metadata saved for 'pipeline-46b42b42-20261011_052246' (status: completed)
LOG: Saving 5 documents to cache
LOG: Cached single file for key 'documents-0842cedc0821' (size: 5620 bytes)
LOG: Successfully cached documents
LOG: Stage 'document_loading' outputs cached: 5 documents
LOG: Finalizing pipeline execution - ID: 'pipeline-46b42b42-20261011_052246'
LOG: Pipeline completed successfully with all stages passed
LOG: Pipeline metadata saved for 'pipeline-46b42b42-20261011_052246' (status: completed)
LOG: PIPELINE SUMMARY
LOG: Pipeline ID: pipeline-46b42b42-20261011_052246
Status: completed
Duration: 0.01s
Stages: 2 completed, 0 failed, 0 running
Data processed: 5 documents -> 0 entities, 0 relationships, 0 claims -> 0 communities
LOG: Pipeline execution completed successfully - ID: 'pipeline-46b42b42-20261011_052246', Status: 'PipelineStageStatus.COMPLETED'
================================================================================
│ Pipeline Results Summary │
Processing Summary
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric              ┃ Count ┃ Details                                 ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Documents Processed │     5 │ Source documents loaded into the system │
│ Text Units Created  │     0 │ Text segments created through chunking  │
└─────────────────────┴───────┴─────────────────────────────────────────┘
================================================================================
│ Pipeline Stage Execution Details │
Stage Execution Summary
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━
┃ Stage                ┃     Status      ┃     Duration ┃      Input ┃     Outpu
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━
│ Document Parsing     │   ✓ COMPLETED   │        0.00s │          5 │
│ Document Loading     │   ✓ COMPLETED   │        0.00s │          5 │
└──────────────────────┴─────────────────┴──────────────┴────────────┴──────────
================================================================================
│ Performance Summary │
Total Pipeline Duration         0.00 seconds
Stages Executed                            2
Stages from Cache                          0
Cache Hit Rate                         0.00%
Gleaning Improvement Rate              0.00%
Entity Merge Rate                      0.00%
Relationship Merge Rate                0.00%
Claim Merge Rate                       0.00%
Community Modularity                    0.00
Avg. Throughput            6357.35 items/sec
│ ✓ Pipeline completed successfully! │
```

### 7.4 Force rebuild

**[RAN]** On a brand-new run ID, then a plain resume of that ID:

```text
exit code: 0
LOG: Force rebuild: ignoring any existing cache for 'force-test'
LOG: Starting new pipeline run: 'force-test'
LOG: Executing 2 stages: 'document_parsing, document_loading'
LOG: Cache disabled, skipping output save for stage: 'document_parsing'
LOG: Using 5 documents from the 'document_parsing' stage
LOG: Cache disabled, skipping output save for stage: 'document_loading'
files:
cache/force-test/pipeline_metadata.json
exit code: 0
LOG: Validating pipeline integrity for 'force-test'
LOG: Missing cache for completed stage 'document_parsing', key: 'documents-1035b7a62512'
LOG: Missing cache for completed stage 'document_loading', key: 'documents-ac616352a4e7'
LOG: Pipeline integrity validation failed for 'force-test' with 2 errors
Pipeline integrity check failed for 'force-test':
• Missing cache for completed stage 'document_parsing', key:
• Missing cache for completed stage 'document_loading', key:
Continue despite integrity issues? [y/n]:
LOG: Rewinding resume point from 'document_loading' to 'document_parsing': it and every stage downstream of it will be recomputed
LOG: Resume strategy determined - Start from: 'document_parsing', Load 0 completed stages
LOG: Executing 2 stages: 'document_parsing, document_loading'
LOG: Cached single file for key 'documents-54cf4641e850' (size: 5620 bytes)
LOG: Using 5 documents from the 'document_parsing' stage
LOG: Cached single file for key 'documents-0842cedc0821' (size: 5620 bytes)
files:
cache/force-test/cache_index.json
cache/force-test/document_loading/documents-0842cedc0821.json
cache/force-test/document_parsing/documents-54cf4641e850.json
cache/force-test/pipeline_metadata.json
```

The force rebuild wrote only `pipeline_metadata.json`. The resume that followed had nothing to load and redid both stages.

**[RAN]** On an ID that already has saved outputs. A marker string was written by hand into the first run's saved files, so that its output can be recognised later:

```text
[1] normal run, id demo-force
exit code: 0
LOG: Starting new pipeline run: 'demo-force'
LOG: Executing 2 stages: 'document_parsing, document_loading'
LOG: Cached single file for key 'documents-54cf4641e850' (size: 5620 bytes)
LOG: Using 5 documents from the 'document_parsing' stage
LOG: Cached single file for key 'documents-0842cedc0821' (size: 5620 bytes)
[2] marker stamped into run 1's saved outputs:
   cache/demo-force/document_loading/documents-0842cedc0821.json | saved at 05:24:17 | doc1 text starts: MARKER-FROM-FIRST-RUN Acme R
   cache/demo-force/document_parsing/documents-54cf4641e850.json | saved at 05:24:17 | doc1 text starts: MARKER-FROM-FIRST-RUN Acme R
[3a] force rebuild, same id, nobody at the keyboard
exit code: 1
LOG: Validating pipeline integrity for 'demo-force'
LOG: Missing cache for completed stage 'document_parsing', key: 'documents-1035b7a62512'
LOG: Missing cache for completed stage 'document_loading', key: 'documents-ac616352a4e7'
LOG: Pipeline integrity validation failed for 'demo-force' with 2 errors
Pipeline integrity check failed for 'demo-force':
• Missing cache for completed stage 'document_parsing', key:
• Missing cache for completed stage 'document_loading', key:
Continue despite integrity issues? [y/n]:
An unexpected error occurred: EOF when reading a line
[3b] force rebuild, same id, answering y
exit code: 0
LOG: Validating pipeline integrity for 'demo-force'
LOG: Missing cache for completed stage 'document_parsing', key: 'documents-1035b7a62512'
LOG: Missing cache for completed stage 'document_loading', key: 'documents-ac616352a4e7'
LOG: Pipeline integrity validation failed for 'demo-force' with 2 errors
Pipeline integrity check failed for 'demo-force':
• Missing cache for completed stage 'document_parsing', key:
• Missing cache for completed stage 'document_loading', key:
Continue despite integrity issues? [y/n]:
LOG: Force rebuild: ignoring any existing cache for 'demo-force'
LOG: Starting new pipeline run: 'demo-force'
LOG: Executing 2 stages: 'document_parsing, document_loading'
LOG: Cache disabled, skipping output save for stage: 'document_parsing'
LOG: Using 5 documents from the 'document_parsing' stage
LOG: Cache disabled, skipping output save for stage: 'document_loading'
    saved files after the force rebuild:
   cache/demo-force/document_loading/documents-0842cedc0821.json | saved at 05:24:17 | doc1 text starts: MARKER-FROM-FIRST-RUN Acme R
   cache/demo-force/document_parsing/documents-54cf4641e850.json | saved at 05:24:17 | doc1 text starts: MARKER-FROM-FIRST-RUN Acme R
[4] resume, same id, no force
exit code: 0
LOG: Validating pipeline integrity for 'demo-force'
LOG: Missing cache for completed stage 'document_parsing', key: 'documents-1035b7a62512'
LOG: Missing cache for completed stage 'document_loading', key: 'documents-ac616352a4e7'
LOG: Pipeline integrity validation failed for 'demo-force' with 2 errors
Pipeline integrity check failed for 'demo-force':
• Missing cache for completed stage 'document_parsing', key:
• Missing cache for completed stage 'document_loading', key:
Continue despite integrity issues? [y/n]:
LOG: Resume strategy determined - Start from: 'document_loading', Load 2 completed stages
LOG: Executing 1 stages: 'document_loading'
LOG: Using 5 documents from the 'document_parsing' stage
LOG: Cached single file for key 'documents-0842cedc0821' (size: 5642 bytes)
    saved files after the resume:
   cache/demo-force/document_loading/documents-0842cedc0821.json | saved at 05:25:06 | doc1 text starts: MARKER-FROM-FIRST-RUN Acme R
   cache/demo-force/document_parsing/documents-54cf4641e850.json | saved at 05:24:17 | doc1 text starts: MARKER-FROM-FIRST-RUN Acme R
```

What that shows:

- Step 3a: a force rebuild of an existing run ID hits the same integrity prompt, and exits with code 1 when nobody can answer. This was first seen on 11 October (section 12, item 5).
- Step 3b: answered with `y`, the force rebuild runs both stages and saves nothing. The files on disk keep their old save time and the marker.
- Step 4: a later resume skips parsing, loads the old marked files, and the loading output it writes carries the marker. The forced run's fresh results were never saved.

This is bug 3.

### 7.5 Expiry

**[RAN]** The expiry was simulated by editing the dates in `cache_index.json`. Nobody waited 24 hours.

```text
[1] normal run, id demo-ttl
exit code: 0
LOG: Starting new pipeline run: 'demo-ttl'
LOG: Executing 2 stages: 'document_parsing, document_loading'
LOG: Cached single file for key 'documents-54cf4641e850' (size: 5620 bytes)
LOG: Using 5 documents from the 'document_parsing' stage
LOG: Cached single file for key 'documents-0842cedc0821' (size: 5620 bytes)
   entry documents-54cf4641e850 | created 2026-10-11T05:25:21 | expires 2026-10-12T05:25:21
   entry documents-0842cedc0821 | created 2026-10-11T05:25:21 | expires 2026-10-12T05:25:21
[2] resume right away
exit code: 0
LOG: Validating pipeline integrity for 'demo-ttl'
LOG: Missing cache for completed stage 'document_parsing', key: 'documents-1035b7a62512'
LOG: Missing cache for completed stage 'document_loading', key: 'documents-ac616352a4e7'
LOG: Pipeline integrity validation failed for 'demo-ttl' with 2 errors
Pipeline integrity check failed for 'demo-ttl':
• Missing cache for completed stage 'document_parsing', key:
• Missing cache for completed stage 'document_loading', key:
Continue despite integrity issues? [y/n]:
LOG: Resume strategy determined - Start from: 'document_loading', Load 2 completed stages
LOG: Executing 1 stages: 'document_loading'
LOG: Using 5 documents from the 'document_parsing' stage
LOG: Cached single file for key 'documents-0842cedc0821' (size: 5620 bytes)
[3] expiry dates edited to the past, then resume
   expiry of every entry set to 2000-01-01
exit code: 0
LOG: Validating pipeline integrity for 'demo-ttl'
LOG: Missing cache for completed stage 'document_parsing', key: 'documents-1035b7a62512'
LOG: Missing cache for completed stage 'document_loading', key: 'documents-ac616352a4e7'
LOG: Pipeline integrity validation failed for 'demo-ttl' with 2 errors
Pipeline integrity check failed for 'demo-ttl':
• Missing cache for completed stage 'document_parsing', key:
• Missing cache for completed stage 'document_loading', key:
Continue despite integrity issues? [y/n]:
LOG: Rewinding resume point from 'document_loading' to 'document_parsing': it and every stage downstream of it will be recomputed
LOG: Resume strategy determined - Start from: 'document_parsing', Load 0 completed stages
LOG: Executing 2 stages: 'document_parsing, document_loading'
LOG: Cached single file for key 'documents-54cf4641e850' (size: 5620 bytes)
LOG: Using 5 documents from the 'document_parsing' stage
LOG: Cached single file for key 'documents-0842cedc0821' (size: 5620 bytes)
```

This is bug 4, logged as a "gotcha" because the behaviour looks intended.

---

## 8. Stage 3, text chunking

### 8.1 What the stage does

**[READ]** For each document it calls the chunker and collects the pieces into `context.text_units` (`pipeline_stages.py` lines 633 to 662, in Appendix C). The work is in `adapters/ingestion/chunker.py`.

Default settings **[READ]**:

```python
# unified_kg_rag/domain/models/config.py, lines 664-731
class ChunkingConfig(BaseModel):
    chunker_type: ChunkingStrategy = Field(
        default=ChunkingStrategy.INTELLIGENT,
        description="Text chunking strategy to use",
    )
    chunking_model_id: BedrockModelId = role_model_field(
        "fast",
        description="Language model for intelligent chunking",
    )
    content_type: str = Field(
        default="markdown",
        pattern="^(text|html|markdown)$",
        description="Content format for processing",
    )
    min_chunk_size: int = Field(
        default=1000,
        ge=1,
        description=(
            "Minimum chunk size in characters; shorter pieces are merged into a "
            "neighbour. Default 1,000 (~250 English tokens) keeps headings and "
            "short trailing paragraphs from becoming chunks of their own."
        ),
    )
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
    chunk_overlap: int = Field(
        default=500, ge=0, description="Chunk overlap in characters"
    )
    pre_chunk_size: int = Field(
        default=50000,
        ge=1,
        description=(
            "Pre-chunk size in characters: the window the intelligent chunker's "
            "LLM picks boundaries in. Not embedded itself (its chunks are capped "
            "by max_chunk_size), so it is sized for the chunking model's prompt."
        ),
    )
    pre_chunk_overlap: int = Field(
        default=500, ge=0, description="Pre-chunk overlap in characters"
    )
    fallback_chunk_size: int = Field(
        default=4800,
        ge=1,
        description=(
            "Target chunk size for the size-based splitter (the simple chunker, "
            "and intelligent chunking when the LLM fails or a chunk exceeds "
            "max_chunk_size). Default 4,800 characters ~= 1,200 English tokens, "
            "the default chunk size of MS GraphRAG and LightRAG."
        ),
    )
    max_marker_miss_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Maximum allowed boundary marker miss rate",
    )

```

### 8.2 The decisions per document

**Step 1, rough cut.** The default `content_type` is `markdown`, so the document is first split at its headings. Small sections are glued together until each piece reaches `min_chunk_size`.

```python
# unified_kg_rag/adapters/ingestion/chunker.py, lines 850-910
    def _create_pre_chunks(self, content: str) -> list[str]:
        try:
            content_type = self.config.processing.chunking.content_type
            if content_type in ["markdown", "html"]:
                logger.debug("Creating structured pre-chunks for %s", content_type)
                return self._create_structured_pre_chunks(content, content_type)
            return self.pre_splitter.split_text(content)
        except Exception as e:
            logger.warning("Failed to create pre-chunks: %s", e)
            return [content] if content else []

    def _create_structured_pre_chunks(
        self, content: str, content_type: str
    ) -> list[str]:
        try:
            splitter = self._get_structured_splitter(content_type)
            return self._merge_structured_chunks(splitter.split_text(content))
        except Exception as e:
            logger.warning(
                "Failed to create structured pre-chunks for %s: %s", content_type, e
            )
            return self.pre_splitter.split_text(content)

    def _merge_structured_chunks(self, structured_chunks: list[Any]) -> list[str]:
        try:
            final_pre_chunks = []
            i = 0
            while i < len(structured_chunks):
                current_content, i = self._merge_small_structured_chunks(
                    structured_chunks, i
                )
                if (
                    len(current_content)
                    > self.config.processing.chunking.pre_chunk_size
                ):
                    final_pre_chunks.extend(
                        self.pre_splitter.split_text(current_content)
                    )
                else:
                    final_pre_chunks.append(current_content)
                i += 1
            return final_pre_chunks
        except Exception as e:
            logger.warning("Failed to merge structured chunks: %s", e)
            return [chunk.page_content for chunk in structured_chunks]

    def _merge_small_structured_chunks(
        self, chunks: list[Any], start_idx: int
    ) -> tuple[str, int]:
        i = start_idx
        content = chunks[i].page_content
        config = self.config.processing.chunking

        while len(content) < config.min_chunk_size and (i + 1) < len(chunks):
            next_content = chunks[i + 1].page_content
            if len(content) + len(next_content) <= config.pre_chunk_size:
                content += "\n\n" + next_content
                i += 1
            else:
                break
        return content, i
```

**Step 2, is the model needed?** Only for a piece of at least twice `min_chunk_size` (2,000 characters by default) or longer than `max_chunk_size`.

```python
# unified_kg_rag/adapters/ingestion/chunker.py, lines 664-706
    def _process_pre_chunks(
        self, pre_chunks: list[str], doc_name: str
    ) -> list[tuple[str, str, int]]:
        try:
            logger.debug(
                "Processing %s pre-chunks for document '%s'", len(pre_chunks), doc_name
            )
            self.stats.num_pre_chunks_processed = (
                self.stats.num_pre_chunks_processed or 0
            ) + len(pre_chunks)
            # Any split of a pre-chunk shorter than 2 * min_chunk_size leaves at
            # least one piece under min_chunk_size, and merge_small_chunks folds
            # it back, so the result is the pre-chunk itself: skip the LLM call
            # (unless it is oversized and must be split anyway).
            processor = self.chunk_processor
            needs_llm = [
                i
                for i, pre_chunk in enumerate(pre_chunks)
                if len(pre_chunk) >= 2 * processor.min_chunk_size
                or len(pre_chunk) > processor.max_chunk_size
            ]
            llm_results = (
                self._get_boundary_results([pre_chunks[i] for i in needs_llm], doc_name)
                if needs_llm
                else []
            )
            response_of = dict(zip(needs_llm, llm_results, strict=True))

            final_chunks: list[tuple[str, str, int]] = []
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
        except Exception as e:
            logger.error("Failed to process pre-chunks for '%s': %s", doc_name, e)
            return [("fallback", chunk, i + 1) for i, chunk in enumerate(pre_chunks)]
```

**Step 3, ask the model.** Each line of the piece is numbered. The model is asked for the line numbers where new chunks should start.

```python
# unified_kg_rag/adapters/ingestion/chunker.py, lines 924-948
    def _create_chain_inputs(self, chunks: list[str]) -> list[dict[str, Any]]:
        try:
            config = self.config.processing.chunking
            inputs = []

            for chunk in chunks:
                lines = chunk.split("\n")
                numbered_lines = []
                for i, line in enumerate(lines, 1):
                    numbered_lines.append(f"{i}: {line}")

                numbered_text = "\n".join(numbered_lines)

                inputs.append(
                    {
                        "numbered_text": numbered_text,
                        "min_chunk_size": config.min_chunk_size,
                        "max_chunk_size": config.max_chunk_size,
                    }
                )

            return inputs
        except Exception as e:
            logger.debug("Failed to create chain inputs: %s", e)
            return []
```

**Step 4, apply the answer and tidy up.**

```python
# unified_kg_rag/adapters/ingestion/chunker.py, lines 779-848
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

            indices, missed = (
                self.line_boundary_processor.convert_line_numbers_to_indices(
                    lines, line_numbers
                )
            )

            if not self.line_boundary_processor.validate_error_rate(
                missed, len(line_numbers)
            ):
                logger.debug(
                    "Line boundary error rate too high: %s/%s",
                    missed,
                    len(line_numbers),
                )
                return None

            if not indices:
                return [text]

            return self._extract_chunks_from_line_indices(text, indices)

        except Exception as e:
            logger.debug("Failed LLM line-based boundary chunking: %s", e)
            return None

    def _extract_chunks_from_line_indices(
        self, text: str, indices: list[int]
    ) -> list[str]:
        try:
            if not indices:
                return [text] if text.strip() else []

            chunks = []
            start_pos = 0

            for end_pos in sorted(set(indices)):
                if end_pos > start_pos:
                    chunk = text[start_pos:end_pos].strip()
                    if chunk:
                        chunks.append(chunk)
                start_pos = end_pos

            if start_pos < len(text):
                final_chunk = text[start_pos:].strip()
                if final_chunk:
                    chunks.append(final_chunk)

            merged_chunks = self.chunk_processor.merge_small_chunks(chunks)

            return self._split_large_line_chunks(merged_chunks)

        except Exception as e:
            logger.debug("Failed to extract chunks from line indices: %s", e)
            return [text] if text.strip() else []
```

```python
# unified_kg_rag/adapters/ingestion/chunker.py, lines 325-355
    def merge_small_chunks(self, chunks: list[str]) -> list[str]:
        if not chunks:
            return []

        try:
            merged_chunks = []
            i = 0
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

**Step 5, build a text unit for each chunk.**

```python
# unified_kg_rag/adapters/ingestion/chunker.py, lines 475-519
    def _create_text_unit(
        self,
        chunk_text: str,
        document: Document,
        chunk_id: int,
        total_chunks: int,
        method: str,
        pre_chunk_id: int,
    ) -> TextUnit:
        try:
            n_tokens = self._calculate_token_count(chunk_text)

            attributes = {
                "file_name": document.file_name,
                "file_path": document.file_path,
                "chunk_id": chunk_id,
                "total_chunks": total_chunks,
                "chunking_method": method,
                "pre_chunk_id": pre_chunk_id,
            }

            if "index" in document.metadata:
                attributes["index"] = document.metadata["index"]

            if "filters" in document.metadata:
                attributes["filters"] = document.metadata["filters"]

            text_unit_id_content = f"text_unit:{document.document_id}:{chunk_id}"
            text_unit_id = generate_stable_id(text_unit_id_content)

            return TextUnit(
                id=text_unit_id,
                short_id=text_unit_id[:8],
                text=chunk_text,
                document_ids=[document.document_id],
                entity_ids=[],
                relationship_ids=[],
                community_ids=[],
                n_tokens=n_tokens,
                attributes=attributes,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        except Exception as e:
            raise DataProcessingError(f"Failed to create text unit: {e}") from e
```

### 8.3 How the model was replaced

**[READ]** `Providers` accepts a substitute model factory (`adapters/providers.py`, lines 60 to 78), and `DataIngestionPipeline` accepts a `providers` argument (`pipeline.py`, line 133).

The session used a stand-in model (`reproduce/scripts/fake_llm.py`, full text in Appendix B). It records every prompt to `prompts.jsonl`. It replies from `answers.json`, a file of answers that Claude wrote by hand after reading the prompt. If no answer is on file it replies "keep as one chunk" and marks the call `PLACEHOLDER`.

Limits of this method:

- The replies are Claude's, written in the conversation. They are not what the configured Bedrock model would say.
- It covers chat models only. **[NOT CHECKED]** Embeddings (lists of numbers for similarity search) cannot be written by hand; a later stage that needs them will need fake vectors.

### 8.4 The run

Two longer documents were added, because the five short ones (about 120 characters each) never reach the model.

**[RAN]** Capture pass, no answers on file yet:

```text
 134 docs/01_acme.txt
 117 docs/02_meera.txt
 124 docs/03_orbit.txt
 125 docs/04_product.txt
 115 docs/05_investor.txt
2414 docs/06_profile.txt
2804 docs/07_review.txt
5833 total
min_chunk_size = 1000 | max_chunk_size = 8000
models the chunking stage asked the factory for:
    anthropic.claude-sonnet-5-5 {'model_purpose': 'ModelPurpose.INGESTION', 'min_output_tokens': '0'}
    anthropic.claude-haiku-5-5 {'model_purpose': 'ModelPurpose.INGESTION', 'min_output_tokens': '0'}
-> _chunk_single_document('01_acme.txt')
   pre-chunks: 1  sizes=[133]
   chunk 1/1  method=unsplit  chars=133   starts: 'Acme Robotics is a company based in Pune. It '
-> _chunk_single_document('02_meera.txt')
   pre-chunks: 1  sizes=[116]
   chunk 1/1  method=unsplit  chars=116   starts: 'Meera Shah studied engineering at IIT Bombay.'
-> _chunk_single_document('03_orbit.txt')
   pre-chunks: 1  sizes=[123]
   chunk 1/1  method=unsplit  chars=123   starts: 'Orbit Logistics runs warehouses in Mumbai and'
-> _chunk_single_document('04_product.txt')
   pre-chunks: 1  sizes=[124]
   chunk 1/1  method=unsplit  chars=124   starts: 'The Acme Picker X2 is a warehouse robot that '
-> _chunk_single_document('05_investor.txt')
   pre-chunks: 1  sizes=[114]
   chunk 1/1  method=unsplit  chars=114   starts: 'Banyan Capital invested in Acme Robotics in 2'
-> _chunk_single_document('06_profile.txt')
   pre-chunks: 2  sizes=[1532, 884]
   chunk 1/2  method=unsplit  chars=1532  starts: '# Acme Robotics: Company Profile  \nAcme Robot'
   chunk 2/2  method=unsplit  chars=884   starts: '## Customers  \nOrbit Logistics is the largest'
-> _chunk_single_document('07_review.txt')
   pre-chunks: 1  sizes=[2803]
   chunk 1/1  method=llm      chars=2803  starts: 'Acme Robotics annual review, prepared for the'

stage results: [('document_parsing', 'completed', 7, 7), ('document_loading', 'completed', 7, 7), ('text_chunking', 'completed', 7, 8)]
AI calls made: 1
   prompt 266920b75e | model: anthropic.claude-haiku-5-5 | reply used: PLACEHOLDER | - Target chunk size: 1000 to 8000 characters
--- system message: 2129 chars ---
--- human message: 4878 chars ---
DOCUMENT TO ANALYZE:
1: Acme Robotics annual review, prepared for the board by the operations team.
2: The Chennai installation at Orbit Logistics ran for the full year with sixty Picker X2 robots on the warehouse floor.
3: Average uptime across the fleet was ninety-six percent, slightly below the ninety-eight percent promised in the service agreement.
4: Most of the downtime came from worn drive wheels, which had to be replaced on forty of the sixty robots during the summer.
5: The service office in Chennai added two technicians in June so that a failed robot could be repaired within one working day.
6: Orbit Logistics reported that the time a picker spends walking fell by roughly half compared with the year before the robots arrived.
7: A software fault in Fleet Console caused a four-hour stoppage in August, and a patch was released the following week.
8: Orbit Logistics has asked for a written plan to bring uptime back above the agreed level before the contract is renewed.
9: The engineering team spent most of the year designing the Picker X3, the planned successor to the Picker X2.
10: The X3 is intended to lift sixty kilograms, which is twenty kilograms more than the X2 can carry today.
11: Priya Nair, who leads hardware engineering, chose a new motor supplier in Coimbatore after the old supplier missed two deliveries.
12: The first X3 prototype completed a week of continuous testing in the Hinjewadi workshop in October without a mechanical failure.
13: Battery life on the prototype is about six hours, shorter than the eight hours of the X2, because the larger motors draw more power.
14: The team is evaluating a bigger battery pack, but it would add weight and raise the price of each robot by about eight percent.
15: Fleet Console will need an update so that a warehouse can run X2 and X3 robots side by side in one fleet.
16: Meera Shah has set a target of shipping the first X3 units to a paying customer in the second half of next year.
17: Acme Robotics hired thirty-one people during the year, bringing the total to about one hundred and twenty employees.
18: Most of the new hires were service technicians and software engineers, with a smaller number joining the sales team.
19: The company opened a sales office in Singapore in September, its first location outside India.
20: Arjun Rao moved from Pune to lead the Singapore office and has started talks with two logistics operators there.
21: Banyan Capital has indicated that it would take part in a second funding round to pay for the Southeast Asia expansion.
22: Ravi Menon, the Banyan Capital partner on the board, asked for a detailed hiring plan before the round is opened.
23: The board discussed whether to build a small assembly line in Singapore or to keep shipping finished robots from Pune.
24: No decision was taken, and the operations team will present costs for both options at the next board meeting.

CHUNKING PARAMETERS:
- Target chunk size: 1000 to 8000 characters

ANALYSIS PROCESS:
1. Identify structural elements (headers, sections, lists) by line numbers
2. Locate semantic transition points between different topics
3. Calculate cumulative character count to ensure appropriate chunk sizes
4. Select line numbers that preserve semantic coherence
5. Output line numbers where new chunks should begin

OUTPUT REQUIREMENTS:
1. **XML FORMAT ONLY**: Start with `<?xml` and end with `</chunk_boundaries>`
2. **LINE NUMBERS ONLY**: Each `<line_number>` contains only an integer
3. **NO LINE 1**: Never include line 1 as a boundary
4. **SINGLE CHUNK**: If text should remain as one chunk, output:
   `<chunk_boundaries><single_chunk>true</single_chunk></chunk_boundaries>`
5. **ASCENDING ORDER**: Line numbers in ascending order
6. **VALID LINES**: Only reference existing line numbers

Provide ONLY the XML output with no additional text or explanations.

<?xml version="1.0" encoding="UTF-8"?>
<chunk_boundaries>
```

Read from that output:

- The stage asked the factory for two models when it was built: `anthropic.claude-sonnet-5-5` (the one used to repair malformed replies, `fixing.fixing_model_id`) and `anthropic.claude-haiku-5-5` (`chunking.chunking_model_id`).
- `06_profile.txt` (2,414 characters, with headings) was cut at its headings into pieces of 1,532 and 884 characters. Both are under 2,000, so the model was not asked.
- `07_review.txt` (2,804 characters, no headings) stayed as one piece of 2,803 characters and was sent to the model. One model call in total.

The prompt's fixed text is in Appendix D.

**The hand-written answer.** The document covers three topics: operations at the Chennai site (lines 1 to 8), the next robot model (lines 9 to 16), and hiring and expansion (lines 17 to 24). Claude's reply was that new chunks start at lines 9 and 17.

**[RAN]** Default settings, with that answer:

```text
{
 "266920b75e": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<chunk_boundaries>\n    <line_number>9</line_number>\n    <line_number>17</line_number>\n</chunk_boundaries>",
 "0b6352c8bf": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<chunk_boundaries>\n    <line_number>9</line_number>\n    <line_number>17</line_number>\n</chunk_boundaries>"
}
min_chunk_size = 1000 | max_chunk_size = 8000
models the chunking stage asked the factory for:
    anthropic.claude-sonnet-5-5 {'model_purpose': 'ModelPurpose.INGESTION', 'min_output_tokens': '0'}
    anthropic.claude-haiku-5-5 {'model_purpose': 'ModelPurpose.INGESTION', 'min_output_tokens': '0'}
-> _chunk_single_document('01_acme.txt')
   pre-chunks: 1  sizes=[133]
   chunk 1/1  method=unsplit  chars=133   starts: 'Acme Robotics is a company based in Pune. It '
-> _chunk_single_document('02_meera.txt')
   pre-chunks: 1  sizes=[116]
   chunk 1/1  method=unsplit  chars=116   starts: 'Meera Shah studied engineering at IIT Bombay.'
-> _chunk_single_document('03_orbit.txt')
   pre-chunks: 1  sizes=[123]
   chunk 1/1  method=unsplit  chars=123   starts: 'Orbit Logistics runs warehouses in Mumbai and'
-> _chunk_single_document('04_product.txt')
   pre-chunks: 1  sizes=[124]
   chunk 1/1  method=unsplit  chars=124   starts: 'The Acme Picker X2 is a warehouse robot that '
-> _chunk_single_document('05_investor.txt')
   pre-chunks: 1  sizes=[114]
   chunk 1/1  method=unsplit  chars=114   starts: 'Banyan Capital invested in Acme Robotics in 2'
-> _chunk_single_document('06_profile.txt')
   pre-chunks: 2  sizes=[1532, 884]
   chunk 1/2  method=unsplit  chars=1532  starts: '# Acme Robotics: Company Profile  \nAcme Robot'
   chunk 2/2  method=unsplit  chars=884   starts: '## Customers  \nOrbit Logistics is the largest'
-> _chunk_single_document('07_review.txt')
   pre-chunks: 1  sizes=[2803]
   chunk 1/1  method=llm      chars=2801  starts: 'Acme Robotics annual review, prepared for the'

stage results: [('document_parsing', 'completed', 7, 7), ('document_loading', 'completed', 7, 7), ('text_chunking', 'completed', 7, 8)]
AI calls made: 1
   prompt 266920b75e | model: anthropic.claude-haiku-5-5 | reply used: hand-written answer | - Target chunk size: 1000 to 8000 characters
```

The result is one chunk of 2,801 characters, not three. The three pieces were 945, 952 and 904 characters, all under the 1,000 minimum, so step 4 merged them back together.

**[RAN]** The same answer with `min_chunk_size` lowered to 900:

```text
min_chunk_size = 900 | max_chunk_size = 8000
models the chunking stage asked the factory for:
    anthropic.claude-sonnet-5-5 {'model_purpose': 'ModelPurpose.INGESTION', 'min_output_tokens': '0'}
    anthropic.claude-haiku-5-5 {'model_purpose': 'ModelPurpose.INGESTION', 'min_output_tokens': '0'}
-> _chunk_single_document('01_acme.txt')
   pre-chunks: 1  sizes=[133]
   chunk 1/1  method=unsplit  chars=133   starts: 'Acme Robotics is a company based in Pune. It '
-> _chunk_single_document('02_meera.txt')
   pre-chunks: 1  sizes=[116]
   chunk 1/1  method=unsplit  chars=116   starts: 'Meera Shah studied engineering at IIT Bombay.'
-> _chunk_single_document('03_orbit.txt')
   pre-chunks: 1  sizes=[123]
   chunk 1/1  method=unsplit  chars=123   starts: 'Orbit Logistics runs warehouses in Mumbai and'
-> _chunk_single_document('04_product.txt')
   pre-chunks: 1  sizes=[124]
   chunk 1/1  method=unsplit  chars=124   starts: 'The Acme Picker X2 is a warehouse robot that '
-> _chunk_single_document('05_investor.txt')
   pre-chunks: 1  sizes=[114]
   chunk 1/1  method=unsplit  chars=114   starts: 'Banyan Capital invested in Acme Robotics in 2'
-> _chunk_single_document('06_profile.txt')
   pre-chunks: 2  sizes=[1532, 884]
   chunk 1/2  method=unsplit  chars=1532  starts: '# Acme Robotics: Company Profile  \nAcme Robot'
   chunk 2/2  method=unsplit  chars=884   starts: '## Customers  \nOrbit Logistics is the largest'
-> _chunk_single_document('07_review.txt')
   pre-chunks: 1  sizes=[2803]
   chunk 1/3  method=llm      chars=945   starts: 'Acme Robotics annual review, prepared for the'
   chunk 2/3  method=llm      chars=952   starts: 'The engineering team spent most of the year d'
   chunk 3/3  method=llm      chars=904   starts: 'Acme Robotics hired thirty-one people during '

stage results: [('document_parsing', 'completed', 7, 7), ('document_loading', 'completed', 7, 7), ('text_chunking', 'completed', 7, 10)]
AI calls made: 1
   prompt 0b6352c8bf | model: anthropic.claude-haiku-5-5 | reply used: hand-written answer | - Target chunk size: 900 to 8000 characters
one finished text unit (chunk 2 of 07_review.txt):
  id                 = '73f8dff9-270d-550f-a570-aa47439d81c1'
  short_id           = '73f8dff9'
  attributes         = {'file_name': '07_review.txt', 'file_path': 'docs/07_review.txt', 'chunk_id': 2, 'total_chun...
  created_at         = '2026-10-11T05:26:33.368966'
  updated_at         = '2026-10-11T05:26:33.368967'
  text               = 'The engineering team spent most of the year designing the Picker X3, the planned successor ...
  translated_texts   = None
  entity_ids         = []
  relationship_ids   = []
  community_ids      = []
  document_ids       = ['067f7c10-8a16-5ff8-9b33-0629e4945b8f']
  n_tokens           = 238
```

Three chunks, split at lines 9 and 17. So the model only proposes cut points; the size rules decide.

**[RAN]** The merge function called directly (`reproduce/scripts/merge_demo.py`):

```text
three pieces (lines 1-8, 9-16, 17-24), sizes: [945, 952, 904]
after merge_small_chunks (min 1000, max 8000): [2801]
text at the first join: 'ore the contract is renewed.The engineering team spe'
```

The merged text is 2,801 characters where the original was 2,803. The two line breaks at the joins are gone, and the sentences run together with no space: `renewed.The engineering team`. **[READ]** Line 832 of `chunker.py` strips each piece, and line 337 joins pieces with `+=` and no separator. This is candidate 5 in `POTENTIAL_BUGS.md`.

### 8.5 The reply parser

**[RAN]** In the 9 October session the hand-written XML was passed through the repo's parser and came back as `{'chunk_boundaries': {'line_number': ['9', '17']}}`. **[READ]** The parser is `RobustXMLOutputParser` in `shared/utils/langchain.py`, lines 597 to 868. It tries four methods in turn before giving up.

### 8.6 Follow-up questions on stage 3 (11 October)

These three scripts are not part of `run_all.sh`. Run them by hand from the work folder that `run_all.sh` leaves behind (they need its `docs/` folder and `fake_llm.py`); they are in Appendix G.

**Is size checked twice, and are tokens counted?** **[READ]** Size is in characters throughout. It is used at four points in `chunker.py`: deciding whether to ask the model (lines 679 to 684); in the prompt, where the model is told the target range (lines 937 to 942); after the reply, where pieces under the minimum are merged and pieces over the maximum are split (lines 842 to 844); and in a quality check that only logs a warning (lines 645 to 651). The code never checks whether the model obeyed the range. Tokens are estimated once per finished chunk and stored as `n_tokens`; the estimate is not used for any decision in this stage:

```python
# unified_kg_rag/adapters/aws/token_counter.py, lines 119-126
    if not text:
        return 0
    dense_chars = sum(1 for ch in text if _is_dense_script_char(ch))
    other_chars = len(text) - dense_chars
    # ~1 token per dense-script char + ~4 chars per token for the rest.
    char_estimate = dense_chars + (other_chars // 4)
    word_count = len(text.split())
    return max(word_count, char_estimate, 1)
```

**Why a model and not only a size count?** **[READ]** The model's job is to choose cut points; it does not count. The setting `processing.chunking.chunker_type` has two values, `intelligent` (default, the path traced here) and `simple`, which cuts by size alone with no model (section 8.1 shows the settings and their descriptions). **[NOT CHECKED]** The design document was not read, so the authors' reasons for the default are unknown.

**Is there overlap between chunks?** **[READ]** `chunk_overlap` (default 500) is given only to the size-only splitter (`chunker.py`, lines 365 to 367). That splitter is used by the simple chunker, by the fallback when a model reply is rejected, and when a chunk is over the maximum. Cuts chosen by the model and cuts at headings are plain slices with no overlap. **[RAN]** `reproduce/scripts/overlap_demo.py`:

```text
settings: fallback_chunk_size = 4800 | chunk_overlap = 500 | min = 1000 | max = 8000
input text: 15099 characters

size-only splitter (used by the 'simple' chunker and the fallback path):
  piece 1: 4688 chars
  piece 2: 4790 chars | shares its first 419 chars with the end of piece 1
  piece 3: 4767 chars | shares its first 498 chars with the end of piece 2
  piece 4: 2258 chars | shares its first 487 chars with the end of piece 3

model path, the three chunks of 07_review.txt (lines 1-8, 9-16, 17-24):
  chunk 2 shares 0 chars with the end of chunk 1
  chunk 3 shares 0 chars with the end of chunk 2

token estimate for the middle chunk: 238 | its length in characters: 952
```

**Can the model put invented text into a chunk?** **[READ]** No. The model returns line numbers only; chunk text is always sliced from the original (`chunker.py`, lines 830 to 835, in section 8.2). **[RAN]** Seven different replies, including wrong and invented ones, fed into the real chunker with checkpoints (`reproduce/scripts/trace_ai_answers.py`, minimum chunk size set to 900 so that splits are visible):

```text
settings: min_chunk_size = 900, max_chunk_size = 8000, max_marker_miss_rate = 0.1
document: 07_review.txt, 24 lines, 2804 bytes

====================================================================================================
CASE 1. sensible reply: lines 9 and 17
   model reply: '<chunk_boundaries>\n<line_number>9</line_number><line_number>17</line_number>\n</chunk_boundaries>'
   CHECKPOINT IntelligentTextChunker._get_boundary_results -> [{'chunk_boundaries': {'line_number': ['9', '17']}}]
   CHECKPOINT LineBasedBoundaryProcessor.extract_line_numbers({'line_number': ['9', '17']}) -> [9, 17]
   CHECKPOINT LineBasedBoundaryProcessor.convert_line_numbers_to_indices -> ([946, 1899], 0)
   CHECKPOINT LineBasedBoundaryProcessor.validate_error_rate -> True
   CHECKPOINT IntelligentTextChunker._chunk_with_llm_boundaries -> 3 piece(s), sizes [945, 952, 904]
   model calls made: 1  [('claude-haiku-5-5', 'hand-written answer')]
   RESULT: [('llm', 945), ('llm', 952), ('llm', 904)]
   every chunk is an exact piece of the original file: True | any invented words in a chunk: False
====================================================================================================
CASE 2. a line that does not exist: 9 and 99
   model reply: '<chunk_boundaries>\n<line_number>9</line_number><line_number>99</line_number>\n</chunk_boundaries>'
   CHECKPOINT IntelligentTextChunker._get_boundary_results -> [{'chunk_boundaries': {'line_number': ['9', '99']}}]
   CHECKPOINT LineBasedBoundaryProcessor.extract_line_numbers({'line_number': ['9', '99']}) -> [9, 99]
   CHECKPOINT LineBasedBoundaryProcessor.convert_line_numbers_to_indices -> ([946], 1)
   CHECKPOINT LineBasedBoundaryProcessor.validate_error_rate -> False
   CHECKPOINT IntelligentTextChunker._chunk_with_llm_boundaries -> None (reply rejected)
   CHECKPOINT IntelligentTextChunker._create_fallback_chunks -> ['Acme Robotics annual review, prepared for the board by the operations team.\nThe Chennai installation at Orbit Logi...
   model calls made: 1  [('claude-haiku-5-5', 'hand-written answer')]
   RESULT: [('fallback', 2803)]
   every chunk is an exact piece of the original file: True | any invented words in a chunk: False
====================================================================================================
CASE 3. forbidden or nonsense numbers: 1, 0, -5, 9
   model reply: '<chunk_boundaries>\n<line_number>1</line_number><line_number>0</line_number><line_number>-5</line_number><line_number>9</line_number>\n</chunk_boundaries>'
   CHECKPOINT IntelligentTextChunker._get_boundary_results -> [{'chunk_boundaries': {'line_number': ['1', '0', '-5', '9']}}]
   CHECKPOINT LineBasedBoundaryProcessor.extract_line_numbers({'line_number': ['1', '0', '-5', '9']}) -> [9]
   CHECKPOINT LineBasedBoundaryProcessor.convert_line_numbers_to_indices -> ([946], 0)
   CHECKPOINT LineBasedBoundaryProcessor.validate_error_rate -> True
   CHECKPOINT IntelligentTextChunker._chunk_with_llm_boundaries -> 2 piece(s), sizes [945, 1857]
   model calls made: 1  [('claude-haiku-5-5', 'hand-written answer')]
   RESULT: [('llm', 945), ('llm', 1857)]
   every chunk is an exact piece of the original file: True | any invented words in a chunk: False
====================================================================================================
CASE 4. words instead of numbers
   model reply: '<chunk_boundaries>\n<line_number>nine</line_number><line_number>seventeen</line_number>\n</chunk_boundaries>'
   CHECKPOINT IntelligentTextChunker._get_boundary_results -> [{'chunk_boundaries': {'line_number': ['nine', 'seventeen']}}]
   CHECKPOINT LineBasedBoundaryProcessor.extract_line_numbers({'line_number': ['nine', 'seventeen']}) -> []
   CHECKPOINT IntelligentTextChunker._chunk_with_llm_boundaries -> 1 piece(s), sizes [2803]
   model calls made: 1  [('claude-haiku-5-5', 'hand-written answer')]
   RESULT: [('llm', 2803)]
   every chunk is an exact piece of the original file: True | any invented words in a chunk: False
====================================================================================================
CASE 5. model writes its own text instead of numbers
   model reply: '<chunk_boundaries>\n<chunk>Acme Robotics was founded on the Moon in 1850.</chunk><chunk>It has two million employees.</chunk>\n</chunk_boundaries>'
   CHECKPOINT IntelligentTextChunker._get_boundary_results -> [{'chunk_boundaries': {'chunk': ['Acme Robotics was founded on the Moon in 1850.', 'It has two million employees.']}}]
   CHECKPOINT LineBasedBoundaryProcessor.extract_line_numbers({'chunk': ['Acme Robotics was founded on the Moon in 1850.', 'It ha...) -> []
   CHECKPOINT IntelligentTextChunker._chunk_with_llm_boundaries -> 1 piece(s), sizes [2803]
   model calls made: 1  [('claude-haiku-5-5', 'hand-written answer')]
   RESULT: [('llm', 2803)]
   every chunk is an exact piece of the original file: True | any invented words in a chunk: False
====================================================================================================
CASE 6. model adds invented text AND a line number
   model reply: '<chunk_boundaries>\n<summary>Acme was founded on the Moon.</summary><line_number>9</line_number>\n</chunk_boundaries>'
   CHECKPOINT IntelligentTextChunker._get_boundary_results -> [{'chunk_boundaries': {'summary': 'Acme was founded on the Moon.', 'line_number': '9'}}]
   CHECKPOINT LineBasedBoundaryProcessor.extract_line_numbers({'summary': 'Acme was founded on the Moon.', 'line_number': '9'}) -> [9]
   CHECKPOINT LineBasedBoundaryProcessor.convert_line_numbers_to_indices -> ([946], 0)
   CHECKPOINT LineBasedBoundaryProcessor.validate_error_rate -> True
   CHECKPOINT IntelligentTextChunker._chunk_with_llm_boundaries -> 2 piece(s), sizes [945, 1857]
   model calls made: 1  [('claude-haiku-5-5', 'hand-written answer')]
   RESULT: [('llm', 945), ('llm', 1857)]
   every chunk is an exact piece of the original file: True | any invented words in a chunk: False
====================================================================================================
CASE 7. not XML at all
   model reply: 'Sure! I would cut it after the part about Chennai, around line 9.'
   CHECKPOINT IntelligentTextChunker._get_boundary_results -> [{'chunk_boundaries': {'single_chunk': 'true'}}]
   CHECKPOINT LineBasedBoundaryProcessor.extract_line_numbers({'single_chunk': 'true'}) -> []
   CHECKPOINT IntelligentTextChunker._chunk_with_llm_boundaries -> 1 piece(s), sizes [2803]
   model calls made: 2  [('claude-haiku-5-5', 'hand-written answer'), ('claude-sonnet-5-5', 'PLACEHOLDER')]
   RESULT: [('llm', 2803)]
   every chunk is an exact piece of the original file: True | any invented words in a chunk: False
```

Read from that output:

- Numbers of 1 or below, and anything that is not a whole number, are dropped (lines 171 to 174).
- A line number past the end counts as a miss. If more than 10% miss (`max_marker_miss_rate`), the whole reply is rejected and the size-only splitter is used; the chunk is labelled `fallback` (case 2).
- Invented text in the reply is never used (cases 5 and 6).
- A reply with no usable numbers gives one chunk, still labelled `llm`, with nothing counted as a failure (cases 4 and 5). This is bug 7.
- Case 7 went to the second, "repair" model. The stand-in for that model always answers "keep as one chunk", so what a real repair model would return is **[NOT CHECKED]**.
- **[INFERRED]** A valid line number in a poor place (the middle of a topic) would be accepted. The model cannot change the text, but it can choose bad cut points.

**Does the model add context between chunks?** **[READ]** No. A chunk is the sliced text with nothing added. Its place is recorded beside the text, in the attributes built at lines 487 to 494 (section 8.2, step 5). **[NOT CHECKED]** Whether a later stage shows the model neighbouring chunks.

**What if the reply is unusable and the piece is large?** **[RAN]** `reproduce/scripts/trace_oversized.py`, default settings, a 24,160-character text with no headings:

```text
settings (defaults): min_chunk_size=1000, max_chunk_size=8000, pre_chunk_size=50000
document: 08_long.txt, 24160 characters, no headings

REPLY: model says keep as one chunk
   chunks: [('llm', 24159)]
   largest chunk: 24159 characters | over max_chunk_size (8000): True
   stats: llm_processing_failures=None, fallback_chunks_used=None
   quality check: ['1 chunks exceed maximum size']

REPLY: model writes words instead of numbers
   chunks: [('llm', 24159)]
   largest chunk: 24159 characters | over max_chunk_size (8000): True
   stats: llm_processing_failures=None, fallback_chunks_used=None
   quality check: ['1 chunks exceed maximum size']

REPLY: model gives usable numbers (lines 49, 97, 145)
   chunks: [('llm', 6039), ('llm', 6039), ('llm', 6039), ('llm', 6039)]
   largest chunk: 6039 characters | over max_chunk_size (8000): False
   stats: llm_processing_failures=None, fallback_chunks_used=None
   quality check: []
```

With a "keep as one chunk" reply, or a reply with no usable numbers, the result is a single chunk of 24,159 characters, three times `max_chunk_size`. This is bug 7.

**The prompt exactly as sent** for `07_review.txt` under default settings. System message:

```text
You are an expert document analysis AI that specializes in intelligent semantic chunking
for maximum information retrieval effectiveness. Your goal is to create optimal chunks that preserve semantic coherence
and contextual relationships while maximizing retrieval performance.

CORE OBJECTIVE:
Analyze document structure and content to identify optimal chunk boundaries that maintain semantic integrity, preserve
contextual relationships, and maximize retrieval effectiveness for RAG applications.

CHUNKING STRATEGY (Priority Order):

1. STRUCTURAL BOUNDARIES (Highest Priority):
   • Section headers and subheaders (marked with #, ##, ###)
   • Numbered sections, clauses, and subsections
   • Document divisions and parts
   • Clear topic transitions
   • Chapter or article boundaries

2. SEMANTIC BOUNDARIES (High Priority):
   • Topic shifts and thematic changes
   • Concept transitions
   • Entity or subject changes
   • Process or procedure boundaries
   • Definition and explanation sections

3. LOGICAL BOUNDARIES (Medium Priority):
   • List beginnings and endings
   • Table boundaries
   • Paragraph transitions with topic shifts
   • Examples and case studies
   • Conclusion and summary sections

4. SIZE-DRIVEN BOUNDARIES (Fallback):
   • Natural sentence endings within size limits
   • Paragraph breaks when necessary
   • Punctuation-based splits as last resort

INTELLIGENT SIZE OPTIMIZATION:
• Target range: 1000 to 8000 characters
• Prioritize semantic completeness over strict size adherence
• Merge small fragments to achieve minimum viable chunk size
• Split oversized sections at natural semantic boundaries
• Ensure each chunk provides standalone contextual value
• Maintain hierarchical relationships where possible

BOUNDARY SELECTION RULES:
• Analyze numbered lines to identify semantic boundaries
• Select line numbers where new chunks should logically begin
• Consider cumulative character count for size optimization
• Ensure chunks fall within target range when possible
• NEVER select line 1 as a boundary (document always starts there)
• Prefer semantic coherence over perfect size matching
```

Human message:

```text
Analyze the following document to determine optimal semantic chunk boundaries that
maximize information retrieval effectiveness while preserving semantic integrity and contextual relationships.

The document is split into numbered lines. Identify line numbers where new chunks should begin.

EXAMPLE:
INPUT DOCUMENT:
1: # Project Overview
2: This project involves comprehensive system analysis.
3:
4: ## 1. System Requirements
5: The system must handle multiple data sources and provide real-time processing.
6:
7: ### 1.1 Performance Requirements
8: Response time should not exceed 100ms for standard queries.
9:
10: ## 2. Technical Specifications
11: The architecture follows microservices patterns with containerized deployment.

TARGET: 100-300 characters

OUTPUT:
<?xml version="1.0" encoding="UTF-8"?>
<chunk_boundaries>
    <line_number>4</line_number>
    <line_number>7</line_number>
    <line_number>10</line_number>
</chunk_boundaries>

---

DOCUMENT TO ANALYZE:
1: Acme Robotics annual review, prepared for the board by the operations team.
2: The Chennai installation at Orbit Logistics ran for the full year with sixty Picker X2 robots on the warehouse floor.
3: Average uptime across the fleet was ninety-six percent, slightly below the ninety-eight percent promised in the service agreement.
4: Most of the downtime came from worn drive wheels, which had to be replaced on forty of the sixty robots during the summer.
5: The service office in Chennai added two technicians in June so that a failed robot could be repaired within one working day.
6: Orbit Logistics reported that the time a picker spends walking fell by roughly half compared with the year before the robots arrived.
7: A software fault in Fleet Console caused a four-hour stoppage in August, and a patch was released the following week.
8: Orbit Logistics has asked for a written plan to bring uptime back above the agreed level before the contract is renewed.
9: The engineering team spent most of the year designing the Picker X3, the planned successor to the Picker X2.
10: The X3 is intended to lift sixty kilograms, which is twenty kilograms more than the X2 can carry today.
11: Priya Nair, who leads hardware engineering, chose a new motor supplier in Coimbatore after the old supplier missed two deliveries.
12: The first X3 prototype completed a week of continuous testing in the Hinjewadi workshop in October without a mechanical failure.
13: Battery life on the prototype is about six hours, shorter than the eight hours of the X2, because the larger motors draw more power.
14: The team is evaluating a bigger battery pack, but it would add weight and raise the price of each robot by about eight percent.
15: Fleet Console will need an update so that a warehouse can run X2 and X3 robots side by side in one fleet.
16: Meera Shah has set a target of shipping the first X3 units to a paying customer in the second half of next year.
17: Acme Robotics hired thirty-one people during the year, bringing the total to about one hundred and twenty employees.
18: Most of the new hires were service technicians and software engineers, with a smaller number joining the sales team.
19: The company opened a sales office in Singapore in September, its first location outside India.
20: Arjun Rao moved from Pune to lead the Singapore office and has started talks with two logistics operators there.
21: Banyan Capital has indicated that it would take part in a second funding round to pay for the Southeast Asia expansion.
22: Ravi Menon, the Banyan Capital partner on the board, asked for a detailed hiring plan before the round is opened.
23: The board discussed whether to build a small assembly line in Singapore or to keep shipping finished robots from Pune.
24: No decision was taken, and the operations team will present costs for both options at the next board meeting.

CHUNKING PARAMETERS:
- Target chunk size: 1000 to 8000 characters

ANALYSIS PROCESS:
1. Identify structural elements (headers, sections, lists) by line numbers
2. Locate semantic transition points between different topics
3. Calculate cumulative character count to ensure appropriate chunk sizes
4. Select line numbers that preserve semantic coherence
5. Output line numbers where new chunks should begin

OUTPUT REQUIREMENTS:
1. **XML FORMAT ONLY**: Start with `<?xml` and end with `</chunk_boundaries>`
2. **LINE NUMBERS ONLY**: Each `<line_number>` contains only an integer
3. **NO LINE 1**: Never include line 1 as a boundary
4. **SINGLE CHUNK**: If text should remain as one chunk, output:
   `<chunk_boundaries><single_chunk>true</single_chunk></chunk_boundaries>`
5. **ASCENDING ORDER**: Line numbers in ascending order
6. **VALID LINES**: Only reference existing line numbers

Provide ONLY the XML output with no additional text or explanations.

<?xml version="1.0" encoding="UTF-8"?>
<chunk_boundaries>
```

---

## 9. Stage 4, and what is known about later stages

### 9.1 Stage 4, translation (traced 12 October)

**What it does [READ].** It asks the model to translate each chunk into a target language and stores the result beside the original. Stage class: `TranslationStage` in `pipeline_stages.py`. Work: `adapters/ingestion/translator.py` (216 lines, read in full). Prompt: `TextTranslationPrompt` in `domain/prompts/data_processing.py`, lines 187 to 272 (read).

The settings, and the languages on offer:

```python
# unified_kg_rag/domain/models/config.py, lines 743-775
class TranslationConfig(BaseModel):
    enabled: bool = Field(
        default=True,
        description="Run the translation pipeline stage. Defaults to True to "
        "preserve existing behavior. Even when enabled, translation is skipped "
        "as a no-op when source_language equals target_language and there are no "
        "additional_target_languages (e.g. an English-only corpus with an English "
        "target pays no LLM cost).",
    )
    translation_model_id: BedrockModelId = role_model_field(
        "fast",
        description="Language model for text translation",
    )
    source_language: LanguageCode = Field(
        default=LanguageCode.EN,
        description="Predominant source language of the corpus. Used only for the "
        "same-language no-op skip; translation is content-driven so this need not "
        "be exact for mixed corpora.",
    )
    target_language: LanguageCode = Field(
        default=LanguageCode.EN, description="Target language code for translation"
    )
    additional_target_languages: list[LanguageCode] | None = Field(
        default=None, description="Additional target languages for translation"
    )

    @property
    def is_noop(self) -> bool:
        """True when translation would do nothing useful (same-language skip)."""
        return (
            self.source_language == self.target_language
            and not self.additional_target_languages
        )
```

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

The stage:

```python
# unified_kg_rag/application/ingestion/pipeline_stages.py, lines 665-757
class TranslationStage(PipelineStage):
    def __init__(
        self,
        config: Config,
        boto_session: boto3.Session | None = None,
        providers: Providers | None = None,
    ):
        super().__init__(PipelineStageType.TRANSLATION, config, boto_session, providers)
        self.translation_config = self.config.processing.translation
        self.target_language = self.translation_config.target_language.value
        # Build the Bedrock-backed translator lazily so a disabled / no-op stage
        # costs nothing (no LLM client, no calls).
        self._translator: TextUnitTranslator | None = None

    @property
    def translator(self) -> TextUnitTranslator:
        if self._translator is None:
            self._translator = TextUnitTranslator(
                self.config, boto_session=self.boto_session, providers=self.providers
            )
        return self._translator

    def _should_skip(self) -> str | None:
        """Return a reason to skip translation, or None to run it."""
        if not self.translation_config.enabled:
            return "translation disabled in config"
        if self.translation_config.is_noop:
            return (
                f"source and target language are both "
                f"'{self.target_language}' with no additional targets"
            )
        return None

    def _execute_core(
        self, context: PipelineContext
    ) -> tuple[int, int, dict[str, Any] | None]:
        logger.info("=" * 60)
        logger.info("TRANSLATION STAGE - STARTED")
        logger.info("=" * 60)

        skip_reason = self._should_skip()
        if skip_reason is not None:
            logger.info("TRANSLATION STAGE - SKIPPED (%s)", skip_reason)
            # Leave translated_units empty; downstream stages fall back to
            # context.text_units, so this is a true no-op.
            context.translated_units = []
            metrics = {
                "target_language": self.target_language,
                "units_processed": len(context.text_units),
                "units_translated": 0,
                "skipped": True,
                "skip_reason": skip_reason,
            }
            logger.info("=" * 60)
            return len(context.text_units), len(context.text_units), metrics

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

The translator:

```python
# unified_kg_rag/adapters/ingestion/translator.py, lines 57-196
class TextUnitTranslator:
    def __init__(
        self,
        config: Config,
        boto_session: boto3.Session | None = None,
        show_progress: bool = True,
        *,
        providers: Providers | None = None,
    ) -> None:
        self.config = config
        self.translation_config = config.processing.translation
        self.target_language = self.translation_config.target_language
        self.additional_target_languages = (
            self.translation_config.additional_target_languages or []
        )
        self.all_target_languages = [
            self.target_language
        ] + self.additional_target_languages
        self.providers = Providers.resolve(config, providers, boto_session)
        self.boto_session = self.providers.boto_session
        self.ignore_errors = config.processing.ignore_errors
        self.show_progress = show_progress
        self.stats: TranslationStats | None = None

        self.factory = self.providers.llm_factory
        self.batch_processor = BatchProcessor(
            is_transient_error=is_transient_bedrock_error
        )

        self.translator = setup_chain(
            model_purpose=ModelPurpose.INGESTION,
            factory=self.factory,
            model_id=self.translation_config.translation_model_id,
            prompt_class=TextTranslationPrompt,
            parser=StrOutputParser(),
            custom_prompts=config.custom_prompts,
        )

    def translate_text_units(self, text_units: list[TextUnit]) -> list[TextUnit]:
        if not text_units:
            logger.info("No text units to translate")
            return text_units

        start_time = time.time()
        total_translation_tasks = len(text_units) * len(self.all_target_languages)
        self.stats = TranslationStats(num_total_units=total_translation_tasks)

        logger.info(
            "Starting translation of %s text units to %s language(s): %s",
            len(text_units),
            len(self.all_target_languages),
            ", ".join([lang.value for lang in self.all_target_languages]),
        )

        try:
            for target_language in self.all_target_languages:
                logger.info("Translating to '%s'...", target_language.value)
                self._translate_text_units_batch(text_units, target_language)

            self.stats.total_processing_time = time.time() - start_time
            self._log_completion_summary(self.stats)
        except Exception as e:
            logger.exception("Translation failed: %s", e)

        return text_units

    def _translate_text_units_batch(
        self, text_units: list[TextUnit], target_language: LanguageCode
    ) -> None:
        texts_to_translate = [unit.text for unit in text_units]

        try:
            translation_results = self.batch_processor.execute_with_fallback(
                items_to_process=texts_to_translate,
                prepare_inputs_func=lambda texts: self._create_chain_inputs(
                    texts, target_language
                ),
                batch_func=self.translator.batch,
                sequential_func=self.translator.invoke,
                task_name=f"Translation ({target_language.value})",
                run_config=self.config.processing.model_dump(),
                show_progress=self.show_progress,
            )
        except Exception as e:
            logger.error(
                "Translation to '%s' failed: %s",
                target_language.value,
                e,
                exc_info=True,
            )
            # Count the whole batch as failed so a fully-failed language does not
            # read as a quiet success: num_total_units was preset, so without
            # this the success rate drops but num_failed_translations stays 0 and
            # the "X units failed" summary warning never fires.
            if self.stats is not None:
                self.stats.num_failed_translations += len(text_units)
            return

        for text_unit, result in zip(text_units, translation_results, strict=True):
            self._apply_translation_result(
                text_unit,
                None if result is BATCH_ITEM_FAILED else result,
                target_language,
            )

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

**How the runs were made.** `reproduce/scripts/stage4.py`, with the stand-in model from section 8.3. It runs stages 1 to 4 on a folder `docs5` holding the five short documents, with `01_acme.txt` in its edited form (one sentence appended, as left by scenario D). To recreate after `run_all.sh`, from its work folder: `mkdir docs5 && cp docs/0[1-5]_*.txt docs5/`, then copy in `stage4.py`. Modes: `default`; `es` (target language Spanish); `es-broken` (target Spanish, and a model that raises an error on every call). Hand-written answers are in `reproduce/scripts/answers_es.json`; copy it to `answers.json` before the answered run.

**Run A, default settings [RAN].**

```text
translation settings: enabled=True | source=en | target=en | additional=None | is_noop=True
stages built: ['document_parsing', 'document_loading', 'text_chunking', 'translation']
models asked for while BUILDING the pipeline: ['anthropic.claude-sonnet-5-5', 'anthropic.claude-haiku-5-5']
CHECKPOINT -> TranslationStage._execute_core
CHECKPOINT -> TranslationStage._should_skip
           returned: "source and target language are both 'en' with no additional targets"
           returned: (5, 5, {'target_language': 'en', 'units_processed': 5, 'units_translated': 0, 'skipped': True, 'skip_reason...

models asked for DURING the run: []
model calls made: 0 []
stage result: status = completed | in = 5 | out = 5
stage metrics: {'target_language': 'en', 'units_processed': 5, 'units_translated': 0, 'skipped': True, 'skip_reason': "source and target language are both 'en' with no additional targets"}
context.text_units: 5 | context.translated_units: 0 | same objects: False
  01_acme.txt      text: 'Acme Robotics is a company based in Pune. It was founded b...
                   translated_texts: None
  02_meera.txt     text: 'Meera Shah studied engineering at IIT Bombay. Before Acme ...
                   translated_texts: None
  03_orbit.txt     text: 'Orbit Logistics runs warehouses in Mumbai and Chennai. In ...
                   translated_texts: None
  04_product.txt   text: 'The Acme Picker X2 is a warehouse robot that lifts up to 4...
                   translated_texts: None
  05_investor.txt  text: 'Banyan Capital invested in Acme Robotics in 2019. Ravi Men...
                   translated_texts: None
cache files: ['stage4-default/cache_index.json', 'stage4-default/document_loading/documents-0842cedc0821.json', 'stage4-default/document_parsing/documents-54cf4641e850.json', 'stage4-default/pipeline_metadata.json', 'stage4-default/text_chunking/text_units-9fcbd193c678.json', 'stage4-default/translation/translated_units-64bc0bc08eed.json']
```

The skip check fires, the translator is never built, no model is called, and an empty `translated_units` list is still saved to the cache.

**Run B1, Spanish, capture pass [RAN].** No answers on file, so the stand-in replied with its placeholder, which is leftover chunking XML:

```text
translation settings: enabled=True | source=en | target=es | additional=None | is_noop=False
stages built: ['document_parsing', 'document_loading', 'text_chunking', 'translation']
models asked for while BUILDING the pipeline: ['anthropic.claude-sonnet-5-5', 'anthropic.claude-haiku-5-5']
CHECKPOINT -> TranslationStage._execute_core
CHECKPOINT -> TranslationStage._should_skip
           returned: None
CHECKPOINT -> TextUnitTranslator.__init__
           returned: 'translator built'
CHECKPOINT -> TextUnitTranslator.translate_text_units
           returned: '5 units; same list object that went in: True'
           returned: (5, 5, {'target_language': 'es', 'units_processed': 5, 'units_translated': 5, 'translation_stats': {'num_to...

models asked for DURING the run: ['anthropic.claude-haiku-5-5']
model calls made: 5 ['PLACEHOLDER', 'PLACEHOLDER', 'PLACEHOLDER', 'PLACEHOLDER', 'PLACEHOLDER']
stage result: status = completed | in = 5 | out = 5
stage metrics: {'target_language': 'es', 'units_processed': 5, 'units_translated': 5}
translation_stats: {'num_total_units': 5, 'num_successful_translations': 5, 'num_failed_translations': 0, 'num_translated': 5, 'total_processing_time': 0.01}
context.text_units: 5 | context.translated_units: 5 | same objects: True
  01_acme.txt      text: 'Acme Robotics is a company based in Pune. It was founded b...
                   translated_texts: {'es': '<?xml version="1.0" encoding="UTF-8"?>\n<chunk_boundaries><single_chunk>true</single_chunk></chunk_boundaries>'}
  02_meera.txt     text: 'Meera Shah studied engineering at IIT Bombay. Before Acme ...
                   translated_texts: {'es': '<?xml version="1.0" encoding="UTF-8"?>\n<chunk_boundaries><single_chunk>true</single_chunk></chunk_boundaries>'}
  03_orbit.txt     text: 'Orbit Logistics runs warehouses in Mumbai and Chennai. In ...
                   translated_texts: {'es': '<?xml version="1.0" encoding="UTF-8"?>\n<chunk_boundaries><single_chunk>true</single_chunk></chunk_boundaries>'}
  04_product.txt   text: 'The Acme Picker X2 is a warehouse robot that lifts up to 4...
                   translated_texts: {'es': '<?xml version="1.0" encoding="UTF-8"?>\n<chunk_boundaries><single_chunk>true</single_chunk></chunk_boundaries>'}
  05_investor.txt  text: 'Banyan Capital invested in Acme Robotics in 2019. Ravi Men...
                   translated_texts: {'es': '<?xml version="1.0" encoding="UTF-8"?>\n<chunk_boundaries><single_chunk>true</single_chunk></chunk_boundaries>'}
cache files: ['stage4-es/cache_index.json', 'stage4-es/document_loading/documents-0842cedc0821.json', 'stage4-es/document_parsing/documents-54cf4641e850.json', 'stage4-es/pipeline_metadata.json', 'stage4-es/text_chunking/text_units-9fcbd193c678.json', 'stage4-es/translation/translated_units-bcd305bae257.json']
```

The five prompts, keyed by hash, and the chunk each one carries:

```text
421b2540a9 | Acme Robotics is a company based in Pune. It was founded by 
af891a25a1 | Orbit Logistics runs warehouses in Mumbai and Chennai. In 20
ebc47663f7 | Meera Shah studied engineering at IIT Bombay. Before Acme Ro
e2318ab369 | The Acme Picker X2 is a warehouse robot that lifts up to 40 
65a696ffe0 | Banyan Capital invested in Acme Robotics in 2019. Ravi Menon
```

The prompt as sent for the first chunk. System message:

```text
You are a professional translator with expertise in technical documents and specialized
materials. Your primary task is to translate text accurately while preserving the original structure and meaning.

TRANSLATION OBJECTIVES:
1. **ACCURACY**: Translate with precision, maintaining specialized terminology and technical language
2. **CONSISTENCY**: Use uniform terminology throughout the translation
3. **COMPLETENESS**: Always process and output the entire text, even if source and target languages match
4. **FIDELITY**: Preserve the original content's meaning and intent without modification
5. **CONSERVATIVE APPROACH**: When uncertain, maintain the original structure and phrasing

CONTENT PRESERVATION REQUIREMENTS:
- Preserve all technical terminology, measurements, and specialized standards
- Keep proper nouns (company names, locations, person names) unchanged
- Maintain all numerical values, dates, codes, and references exactly
- Preserve document hierarchy and logical structure
- Never add information not present in the original
- Never remove or omit content from the original
- Never modify the core meaning or intent

TEXT PROCESSING GUIDELINES:
- Complete fragmented sentences only using explicit context from surrounding text
- Make minimal improvements to sentence flow while preserving exact meaning
- Apply conservative formatting improvements that enhance readability without altering content
- Maintain original paragraph structure unless necessary for clarity

FORMATTING APPROACH:
- Convert to clean markdown format when appropriate
- Transform clear HTML tags to corresponding markdown (e.g., <h1> to #, <strong> to **)
- Convert obvious document formats (tables, lists, headers) to markdown equivalents
- Apply formatting standardization conservatively
- Ensure formatting changes are purely presentational and preserve meaning

CRITICAL REQUIREMENT - COMPLETE OUTPUT:
You MUST translate and output the ENTIRE document from beginning to end. NEVER truncate, summarize, or provide partial
translations. If you encounter a long document, continue processing until you reach the absolute end. Do not add any
meta-commentary like "translation continues" or "would you like me to continue" - simply provide the complete translated
text in its entirety.

STRICT OUTPUT REQUIREMENT:
Provide ONLY the translated and formatted text that maintains complete fidelity to the original content. Output the
COMPLETE document without any truncation, interruption, or additional notes. NEVER add explanatory notes, commentary,
or observations about the translation process, even when the source and target languages are the same.
```

Human message:

```text
Translate the following text to LanguageCode.ES while preserving all original content
and applying conservative formatting improvements:

Acme Robotics is a company based in Pune. It was founded by Meera Shah in 2015. Acme builds warehouse robots.
Acme has 120 employees.

Target Language: LanguageCode.ES

TRANSLATION INSTRUCTIONS:
1. Translate to LanguageCode.ES with complete accuracy (process even if source language matches target)
2. Preserve ALL original content without additions, deletions, or meaning changes
3. Apply conservative markdown formatting where it improves readability
4. Convert clear HTML tags and document structures to appropriate markdown
5. Complete the entire text processing task - OUTPUT THE FULL DOCUMENT FROM START TO FINISH

FORMATTING GUIDELINES:
- Use markdown for headers, emphasis, lists, and tables where clearly applicable
- Convert HTML tags to markdown equivalents when the mapping is obvious
- Maintain document structure and hierarchy
- Apply minimal formatting that enhances readability without changing content

MANDATORY REQUIREMENT:
You MUST output the COMPLETE translated document from the very beginning to the very end. Do not stop, truncate, or
provide partial output. Process the entire input text without interruption.

STRICTLY FORBIDDEN ACTIONS:
- Adding explanatory text, commentary, or notes about the translation
- Adding observations about language similarity or translation process
- Removing or summarizing content
- Enhancing beyond direct translation and conservative formatting
- Modifying document meaning or structure
- Stopping before the complete document is processed
- Adding continuation messages or asking if more is needed
- Adding ANY notes or explanations, even when translating between the same language

OUTPUT REQUIREMENT:
Provide ONLY the translated and formatted text - THE COMPLETE DOCUMENT IN ITS ENTIRETY. No additional notes,
explanations, or commentary of any kind.
```

**Run B, Spanish, with Claude's hand-written translations [RAN].**

`reproduce/scripts/answers_es.json`

```json
{
 "421b2540a9": "Acme Robotics es una empresa con sede en Pune. Fue fundada por Meera Shah en 2015. Acme fabrica robots de almacén.\nAcme tiene 120 empleados.",
 "af891a25a1": "Orbit Logistics opera almacenes en Mumbai y Chennai. En 2022 Orbit Logistics firmó un contrato de suministro con Acme Robotics.",
 "ebc47663f7": "Meera Shah estudió ingeniería en IIT Bombay. Antes de Acme Robotics trabajó en Orbit Logistics como responsable de hardware.",
 "e2318ab369": "El Acme Picker X2 es un robot de almacén que levanta hasta 40 kg. Orbit Logistics utiliza el Picker X2 en su almacén de Chennai.",
 "65a696ffe0": "Banyan Capital invirtió en Acme Robotics en 2019. Ravi Menon, socio de Banyan Capital, forma parte del consejo de administración de Acme."
}
```

```text
translation settings: enabled=True | source=en | target=es | additional=None | is_noop=False
stages built: ['document_parsing', 'document_loading', 'text_chunking', 'translation']
models asked for while BUILDING the pipeline: ['anthropic.claude-sonnet-5-5', 'anthropic.claude-haiku-5-5']
CHECKPOINT -> TranslationStage._execute_core
CHECKPOINT -> TranslationStage._should_skip
           returned: None
CHECKPOINT -> TextUnitTranslator.__init__
           returned: 'translator built'
CHECKPOINT -> TextUnitTranslator.translate_text_units
           returned: '5 units; same list object that went in: True'
           returned: (5, 5, {'target_language': 'es', 'units_processed': 5, 'units_translated': 5, 'translation_stats': {'num_to...

models asked for DURING the run: ['anthropic.claude-haiku-5-5']
model calls made: 5 ['hand-written answer', 'hand-written answer', 'hand-written answer', 'hand-written answer', 'hand-written answer']
stage result: status = completed | in = 5 | out = 5
stage metrics: {'target_language': 'es', 'units_processed': 5, 'units_translated': 5}
translation_stats: {'num_total_units': 5, 'num_successful_translations': 5, 'num_failed_translations': 0, 'num_translated': 5, 'total_processing_time': 0.03}
context.text_units: 5 | context.translated_units: 5 | same objects: True
  01_acme.txt      text: 'Acme Robotics is a company based in Pune. It was founded b...
                   translated_texts: {'es': 'Acme Robotics es una empresa con sede en Pune. Fue fundada por Meera Shah en 2015. Acme fabrica robots de almacén.\nAcme tiene 120 empleado...
  02_meera.txt     text: 'Meera Shah studied engineering at IIT Bombay. Before Acme ...
                   translated_texts: {'es': 'Meera Shah estudió ingeniería en IIT Bombay. Antes de Acme Robotics trabajó en Orbit Logistics como responsable de hardware.'}
  03_orbit.txt     text: 'Orbit Logistics runs warehouses in Mumbai and Chennai. In ...
                   translated_texts: {'es': 'Orbit Logistics opera almacenes en Mumbai y Chennai. En 2022 Orbit Logistics firmó un contrato de suministro con Acme Robotics.'}
  04_product.txt   text: 'The Acme Picker X2 is a warehouse robot that lifts up to 4...
                   translated_texts: {'es': 'El Acme Picker X2 es un robot de almacén que levanta hasta 40 kg. Orbit Logistics utiliza el Picker X2 en su almacén de Chennai.'}
  05_investor.txt  text: 'Banyan Capital invested in Acme Robotics in 2019. Ravi Men...
                   translated_texts: {'es': 'Banyan Capital invirtió en Acme Robotics en 2019. Ravi Menon, socio de Banyan Capital, forma parte del consejo de administración de Acme.'}
cache files: ['stage4-es/cache_index.json', 'stage4-es/document_loading/documents-0842cedc0821.json', 'stage4-es/document_parsing/documents-54cf4641e850.json', 'stage4-es/pipeline_metadata.json', 'stage4-es/text_chunking/text_units-9fcbd193c678.json', 'stage4-es/translation/translated_units-bcd305bae257.json']
```

**Run C, Spanish, every model call fails [RAN].**

```text
translation settings: enabled=True | source=en | target=es | additional=None | is_noop=False
stages built: ['document_parsing', 'document_loading', 'text_chunking', 'translation']
models asked for while BUILDING the pipeline: ['anthropic.claude-sonnet-5-5', 'anthropic.claude-haiku-5-5']
CHECKPOINT -> TranslationStage._execute_core
CHECKPOINT -> TranslationStage._should_skip
           returned: None
CHECKPOINT -> TextUnitTranslator.__init__
           returned: 'translator built'
CHECKPOINT -> TextUnitTranslator.translate_text_units
           returned: '5 units; same list object that went in: True'
           returned: (5, 5, {'target_language': 'es', 'units_processed': 5, 'units_translated': 0, 'translation_stats': {'num_to...

models asked for DURING the run: ['anthropic.claude-haiku-5-5']
model calls made: 0 []
stage result: status = completed | in = 5 | out = 5
stage metrics: {'target_language': 'es', 'units_processed': 5, 'units_translated': 0}
translation_stats: {'num_total_units': 5, 'num_successful_translations': 0, 'num_failed_translations': 5, 'num_translated': 0, 'total_processing_time': 0.01}
context.text_units: 5 | context.translated_units: 5 | same objects: True
  01_acme.txt      text: 'Acme Robotics is a company based in Pune. It was founded b...
                   translated_texts: None
  02_meera.txt     text: 'Meera Shah studied engineering at IIT Bombay. Before Acme ...
                   translated_texts: None
  03_orbit.txt     text: 'Orbit Logistics runs warehouses in Mumbai and Chennai. In ...
                   translated_texts: None
  04_product.txt   text: 'The Acme Picker X2 is a warehouse robot that lifts up to 4...
                   translated_texts: None
  05_investor.txt  text: 'Banyan Capital invested in Acme Robotics in 2019. Ravi Men...
                   translated_texts: None
cache files: ['stage4-es-broken/cache_index.json', 'stage4-es-broken/document_loading/documents-0842cedc0821.json', 'stage4-es-broken/document_parsing/documents-54cf4641e850.json', 'stage4-es-broken/pipeline_metadata.json', 'stage4-es-broken/text_chunking/text_units-9fcbd193c678.json', 'stage4-es-broken/translation/translated_units-bcd305bae257.json']
```

**How the language name reaches the prompt [RAN].** `reproduce/scripts/lang_format_demo.sh`. The 3.10 and 3.12 lines use a tiny stand-alone enum of the same kind, not the repo:

```text
repo venv, python 3.11.17
  LanguageCode.ES.value           -> 'es'
  '{x}'.format(x=LanguageCode.ES) -> 'LanguageCode.ES'
stand-alone enum, python 3.10.20 -> 'es'
stand-alone enum, python 3.12.3 -> 'L.ES'
```

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

```text
LAYER EDGES (importer -> imported: count)
  adapters       -> domain         70
  adapters       -> evaluation     2
  adapters       -> ports          8
  adapters       -> shared         68
  application    -> adapters       33
  application    -> domain         24
  application    -> evaluation     1
  application    -> ports          6
  application    -> shared         26
  application    -> visualization  1
  domain         -> adapters       1
  domain         -> ports          1
  domain         -> shared         17
  evaluation     -> adapters       6
  evaluation     -> application    1
  evaluation     -> domain         6
  evaluation     -> shared         5
  ports          -> domain         2
  ports          -> shared         3
  shared         -> domain         9
  shared         -> ports          1
  visualization  -> adapters       6
  visualization  -> domain         5
  visualization  -> ports          1
  visualization  -> shared         5

LINES PER LAYER
  adapters       19698
  domain         9540
  application    7226
  shared         3941
  evaluation     2012
  visualization  803
  ports          582
  root           10

MODULES (lines | classes | top-level funcs)
unified_kg_rag | 10 |  | 
adapters.aws | 25 |  | 
adapters.aws.bedrock | 987 | BaseBedrockWrapper,BaseBedrockModelFactory,BedrockCrossRegionModelHelper,BedrockEmbeddingsWrapper,BedrockEmbeddingModelFactory,GuardrailInterventionHandler,BedrockLanguageModelFactory,BedrockRerankWrapper,BedrockRerankModelFactory | _message_guardrail_intervened,get_assumed_role_boto_session
adapters.aws.bedrock_models | 785 | EmbeddingModelInfo,LanguageModelInfo,RerankModelInfo | base_model_id,_family_default,_warn_uncurated,get_language_model_info,effective_max_output_tokens
adapters.aws.bedrock_retry | 159 |  | is_transient_bedrock_error,_error_code,backoff_delay,next_transient_retry_delay,call_with_transient_retry,acall_with_transient_retry
adapters.aws.chain_factory | 316 | TransientRetryRunnable | _prompt_cache_marker,_build_chat_prompt,with_transient_retry,create_robust_xml_output_parser,setup_chain
adapters.aws.dynamodb | 282 | DynamoDBDocStatusStore | 
adapters.aws.embedding_cache | 130 | S3EmbeddingCache | 
adapters.aws.neptune | 216 | NeptuneClient | is_permanent_neptune_error,_handle_neptune_errors
adapters.aws.opensearch | 533 | OpenSearchClient | _handle_opensearch_errors,_handle_async_opensearch_errors,_running_loop,_finish_without_loop
adapters.aws.s3_cache | 261 | S3CacheManager | 
adapters.aws.token_counter | 251 | BedrockTokenCounter | is_count_tokens_unsupported_error,is_count_tokens_known_unsupported,mark_count_tokens_unsupported,_is_dense_script_char,estimate_token_count
adapters.evaluators | 8 |  | 
adapters.evaluators.langchain_evaluator | 390 | UnscoredJudgeOutputError,LangChainEvaluator | 
adapters.evaluators.ragas_evaluator | 412 | RagasEvaluator | 
adapters.ingestion.chunker | 992 | ChunkingStats,ChunkQualityValidator,LineBasedBoundaryProcessor,ChunkProcessor,BaseChunker,SimpleTextChunker,IntelligentTextChunker,ChunkerFactory | 
adapters.ingestion.claim_extractor | 451 | ClaimExtractionStats,ClaimExtractor | format_entities_with_limit_task,_prepare_claim_input_task
adapters.ingestion.community_detector | 1293 | HierarchicalCommunity,CommunityDetector | community_content_id,_canonical_graph
adapters.ingestion.description_summarizer | 196 | DescriptionSummarizer | 
adapters.ingestion.gleaner | 983 | GleaningRound,GleaningStats,GraphGleaner | format_entities_with_limit_task,format_relationships_with_limit_task,prepare_input_task
adapters.ingestion.graph_extractor | 721 | ExtractionStats,GraphExtractor | 
adapters.ingestion.json_loader | 84 | JsonTextLoader | _iter_strings
adapters.ingestion.loader | 378 | DirectoryLoader | compute_minhash,compute_jaccard_similarity
adapters.ingestion.parser | 260 | ParsingStats,BaseParser,FileParser,ParserFactory | 
adapters.ingestion.translator | 216 | TranslationStats,TextUnitTranslator | 
adapters.providers | 163 | Providers | 
adapters.renderers | 25 |  | 
adapters.renderers.adapters | 93 | InteractiveRendererAdapter,StaticRendererAdapter | _render_file
adapters.renderers.base | 79 | RenderContext,BaseRenderer | register_renderer,registered_renderers,get_renderer_class
adapters.renderers.interactive | 381 | InteractiveRenderer | 
adapters.renderers.static | 290 | StaticRenderer | 
adapters.retrieval.base | 449 | BaseGraphRAGRetriever,BaseSearchStrategy | is_fatal_retrieval_error
adapters.retrieval.hybrid_scorer | 605 | HybridScorer | _with_top_n
adapters.retrieval.memory_manager | 419 | GraphRAGChatMessageHistory,GraphRAGConversationBufferMemory,MemoryManager | build_entity_extractor,_memory_fingerprint,get_memory_manager
adapters.retrieval.token_manager | 535 | SectionType,ContextSection,OptimizedContext,TokenManager | 
adapters.retrievers | 6 |  | 
adapters.retrievers.neptune_retriever | 672 | NeptuneRetriever | 
adapters.retrievers.opensearch_retriever | 715 | OpenSearchRetriever | _is_index_not_found
adapters.search_strategies | 15 |  | 
adapters.search_strategies.drift_search | 637 | DriftSearchStrategy | 
adapters.search_strategies.global_search | 751 | _MapPoint,GlobalSearchStrategy | 
adapters.search_strategies.lightrag_search | 707 | LightRAGSearchStrategy | _pick_by_weighted_polling
adapters.search_strategies.local_search | 475 | LocalSearchStrategy | 
adapters.search_strategies.simple_search | 106 | SimpleSearchStrategy | 
adapters.storage | 8 |  | 
adapters.storage.filter_schema | 166 | FilterFields | union_filter_fields,opensearch_filter_fields
adapters.storage.neptune_codec | 204 |  | property_value,item_properties,entity_properties,relationship_properties,relationship_label,_values,_single,_vertex_list,_edge_list,_attribute_value,_attributes,entity_from_vertex,relationship_from_edge
adapters.storage.neptune_indexer | 838 | NeptuneIndexer | 
adapters.storage.opensearch_indexer | 1021 | OpenSearchIndexer | 
application.cli.run_evaluation | 345 | CommandLineInterface,EvaluationRunner | _failure_rate,failure_budget_breaches,exceeds_failure_budget,main
application.cli.run_ingestion_pipeline | 443 | CommandLineInterface,IngestionPipelineRunner | main
application.cli.run_prompt_tuning | 123 |  | load_corpus_texts,_build_parser,main
application.cli.run_rag_chain | 555 | CommandLineInterface,RAGChainRunner | async_main,main
application.cli.run_visualization | 198 |  | _hierarchy_entries,_to_hierarchical_communities,_to_communities,load_render_context,run_visualization,_build_parser,main
application.ingestion.incremental | 484 | _SuffixRemoval,IncrementalIndexer | build_document_lineage,_artifact_ids,_remap_lineage
application.ingestion.pipeline | 996 | DataIngestionPipeline | 
application.ingestion.pipeline_stages | 1639 | PipelineStage,DocumentLoadingStage,DocumentParsingStage,TextChunkingStage,TranslationStage,GraphExtractionStage,GleaningStage,GraphResolutionStage,ClaimExtractionStage,ClaimResolutionStage,GraphAnalysisStage,CommunityDetectionStage,IndexingStage | 
application.prompts.tuner | 312 | CorpusProfile,PromptTuner | 
application.retrieval.rag_chain | 1464 | ChainMode,ProcessedQuery,RAGInput,RAGOutput,GraphRAGChain,_LoopRunner | _aclose_retrievers,_iterate_async_generator,create_rag_chain
application.storage.indexing_manager | 647 | CrossRunMergeResult,IndexingTask,IndexingManager | 
domain.ingestion.base_processor | 380 | BaseProcessor | coerce_llm_text,check_entity_relevance_task,check_relationship_relevance_task
domain.ingestion.base_resolver | 527 | FuzzyMatcher,BaseResolver | discriminator_tokens,normalize_entity_type,entity_types_compatible
domain.ingestion.claim_resolver | 333 | ClaimResolutionStats,ClaimResolver | claim_date_key,claim_identity_suffix,resolve_entity_reference_task,resolve_single_claim_task
domain.ingestion.delta_detector | 193 |  | compute_content_hash,_document_suffix,assign_document_identity,document_doc_id,registry_scope,fingerprint_documents,detect_delta,filter_documents_to_process
domain.ingestion.entity_grounding | 95 |  | normalize_for_grounding,_tokens,token_overlap_ratio,is_grounded
domain.ingestion.graph_analyzer | 363 | CentralityMetrics,GraphStatistics,GraphAnalyzer | 
domain.ingestion.graph_builder | 147 | GraphBuilder | 
domain.ingestion.graph_resolver | 548 | _TypeAwareUnionFind,EntityResolutionStats,RelationshipResolutionStats,GraphResolutionStats,EntityResolver,RelationshipResolver,GraphResolver | _init_worker_fuzzy_matcher,find_all_matches_for_entity_task
domain.ingestion.merge | 38 |  | 
domain.ingestion.merge.merger | 479 | DeltaMergeResult | _dedupe_preserve_order,_merge_descriptions,_merge_attributes,_merge_entity_fields,merge_entities,_find_fuzzy_old_match,_relationship_weight,_remapped_endpoints,_relationship_key,merge_relationships,relationship_id_remap,remove_text_units,_community_content_key,_report_content_key,_placed_id,merge_communities,merge_community_reports
domain.models | 130 |  | 
domain.models.base | 27 | Identified,Named | 
domain.models.cache | 125 | CacheStrategy,CacheEntry,CacheIndex,CacheStats | 
domain.models.community | 51 | CommunityMetrics,Community | 
domain.models.community_report | 108 | CommunityFinding,CommunityReport | 
domain.models.config | 2702 | PipelineStageType,ChunkingStrategy,Constants,LanguageCode,ResolutionMethod,S3EncryptionType,EmbeddingModelId,LanguageModelId,ModelPurpose,RerankModelId,GuardrailConfig,TransientRetryConfig,BedrockConfig,NeptuneConfig,OpenSearchConfig,S3EncryptionConfig,S3Config,DynamoDBConfig,AWSConfig,FixingConfig,DocumentParsingConfig,ChunkingConfig,TranslationConfig,DescriptionSummarizationConfig,EntityGroundingConfig,GraphExtractionConfig,GleaningConfig,ClaimExtractionConfig,ProcessingConfig,CentralityConfig,StatisticsConfig,GraphAnalysisConfig,ReportGenerationConfig,CommunityDetectionConfig,VisualizationConfig,GraphConfig,NeptuneIndexingConfig,OpenSearchIndexingConfig,IndexingConfig,HybridConfig,FusionConfig,RerankingConfig,GlobalSearchConfig,LocalSearchQuotaConfig,LocalSearchConfig,DriftSearchConfig,ContextTypeBudgetConfig,TokenManagerConfig,LightRAGSearchConfig,SearchConfig,MemoryConfig,CacheChunkingConfig,CacheConfig,LoggingConfig,CustomPromptConfig,EvaluationConfig,Config,PipelineConfig | _coerce_model_id,role_model_field,_apply_model_tiers,_coerce_visualization_embeddings,_get_path,_with_path,_retries_to_attempts,_migrate_legacy_key
domain.models.conversation | 27 | MessageRole,ConversationContext | 
domain.models.covariate | 43 | Covariate,Claim | 
domain.models.document | 433 | ElementContent,ElementType,DocumentElement,DocumentContent,Page,DocStatus,DocStatusRecord,DocumentLineage,DocumentDelta,Document | _read_text_autodetect
domain.models.entity | 33 | Entity | 
domain.models.evaluation | 277 | EvaluationMetricType,EvaluatorType,EvaluationQuery,EvaluationGroundTruth,EvaluationResult,EvaluationMetric,EvaluationReport,EvaluationSummary | 
domain.models.pipeline | 245 | PipelineStageStatus,PipelineMetrics,PipelineStageResult,PipelineContext | 
domain.models.relationship | 27 | Relationship | 
domain.models.retrieval | 139 | FusionMethod,RetrieverRole,SearchStrategy,SearchType,RetrievalResult,SearchQuery,SearchResult | 
domain.models.text_unit | 25 | TextUnit | 
domain.prompts | 57 |  | 
domain.prompts.base | 138 | ResolvedPrompt,BasePrompt | 
domain.prompts.data_processing | 272 | TextChunkingPrompt,DescriptionSummarizationPrompt,TextTranslationPrompt | 
domain.prompts.graph_extraction | 582 | GraphExtractionPrompt,ClaimExtractionPrompt,GraphRefinementPrompt,CommunityReportPrompt | 
domain.prompts.retrieval | 750 | AnswerGenerationPrompt,CommunityRelevancePrompt,ContextBuildingPrompt,ConvergenceAssessmentPrompt,EntityExtractionPrompt,GlobalMapPrompt,KeywordsExtractionPrompt,KeywordExpansionPrompt,MapReduceSummaryPrompt,DriftPrimerPrompt,QueryRefinementPrompt,StrategySelectionPrompt,TranslationPrompt | 
domain.prompts.tuning | 50 | CorpusProfilePrompt | 
domain.retrieval.index_prefixes | 50 |  | all_index_prefixes,configured_index_prefixes
domain.retrieval.mixins | 18 | MetricsMixin | 
domain.retrieval.strategy_registry | 125 | QueryInput,StrategySpec | register_strategy,get_strategy_spec,registered_strategies
evaluation | 46 |  | __getattr__
evaluation.answer_match_evaluator | 158 | AnswerMatchEvaluator | exact_match,answer_contains,token_f1
evaluation.base | 178 | BaseEvaluator,BaseGraphRAGEvaluator | judge_model_kwargs
evaluation.evaluation_manager | 1036 | EvaluationManager | 
evaluation.graph_aware_evaluator | 180 | GraphAwareEvaluator | 
evaluation.retrieval_evaluator | 198 | RetrievalEvaluator | _is_path_like,source_keys
evaluation.source_resolver | 109 | SourceFileResolver,_DocumentRetriever,TextUnitFileResolver | file_name_of
evaluation.text_matching | 107 |  | _is_punctuation,normalize_answer,tokenize,_is_hangul,is_spaceless_script,_token_matches,phrase_in_text
ports | 61 |  | 
ports.cache | 68 | CachePort | 
ports.doc_status | 53 | DocStatusPort | 
ports.indexer | 324 | IndexingStats,BaseIndexer,GraphIndexer,VectorIndexer | 
ports.model_factory | 76 | ModelFactoryPort,TokenCounterPort | 
shared | 61 |  | get_cache_manager
shared.cache_manager | 467 | CacheManager | 
shared.config | 192 | ConfigLoader | _nested_model,warn_unknown_keys,get_config,reload_config
shared.exceptions | 65 | GraphRAGException,AWSServiceError,CacheSyncError,DataProcessingError,EvaluationException,GraphError,ModelError,EmbeddingModelError,InvalidFilterError,LanguageModelError,PipelineExecutionError,PipelineResumeError,PipelineStageError,PipelineStateError,RerankModelError | 
shared.logging | 170 | LoggingSetup | _configure_structlog,get_logger,setup_logging,warn_if_langsmith_tracing
shared.metrics | 132 | MetricsSink,NullMetricsSink,CloudWatchEMFSink | 
shared.pipeline_manager | 702 | PipelineStateManager,PipelineResumeManager | _canonical_index
shared.utils | 52 |  | 
shared.utils.cache_keys | 306 |  | _resolve_path,_canonicalize,_input_paths_through,_file_digest,corpus_manifest_fingerprint,stage_input_fingerprint,stage_cache_key
shared.utils.common | 247 |  | _available_cpu_count,_cgroup_cpu_quota,default_max_workers,compute_hash,ensure_list,generate_stable_id,normalize_name,clean_display_name,entity_key,safe_float_parse,parse_llm_json,strip_embedding_fields
shared.utils.concurrency | 35 | ContextThreadPoolExecutor | 
shared.utils.display | 406 |  | display_ascii_art,display_pipeline_results,_get_resolved_data,display_pipeline_summary,display_stage_results,display_sample_entities,_truncate_text,display_sample_relationships,display_sample_claims,display_communities,_create_entity_and_claim_lookup,_create_reports_lookup,display_performance_summary,_create_performance_metrics_table,_add_pipeline_metrics
shared.utils.document_converter | 72 |  | convert_langchain_to_document
shared.utils.document_identity | 84 |  | normalize_source_path,relative_source_path,compute_text_hash,compute_document_id,registry_namespace,compute_doc_id
shared.utils.event_loop | 38 |  | configure_event_loop,run
shared.utils.langchain | 873 | _BatchItemFailed,ProgressLogger,BatchProcessor,RobustXMLOutputParser | 
shared.utils.store_names | 39 |  | store_name,graph_label
visualization | 16 |  | 
visualization.base | 232 | GraphVisualizationManager | _strip_heavy_attributes
visualization.embeddings | 6 |  | 
visualization.embeddings.dimensionality | 140 | ReducerConfig,UMAPConfig,TSNEConfig,DimensionalityReducer | 
visualization.embeddings.node2vec | 131 | NodeEmbeddings,BedrockNodeEmbedder | 
visualization.exporters.html_exporter | 273 | HTMLExporter | 
```

### Appendix B. The tracing scripts

`reproduce/scripts/step2.py`: constructor with checkpoints, all 12 stages enabled.

```python
import functools, sys, logging
from pathlib import Path
import boto3
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.domain.models import PipelineConfig, PipelineStageType
from unified_kg_rag.application.ingestion import pipeline as P
from unified_kg_rag.application.ingestion.pipeline import DataIngestionPipeline

n = [0]
def checkpoint(cls, name):
    orig = getattr(cls, name)
    @functools.wraps(orig)
    def wrapper(self, *a, **k):
        n[0] += 1
        print(f"CHECKPOINT {n[0]:>2}: entering {cls.__name__}.{name}")
        return orig(self, *a, **k)
    setattr(cls, name, wrapper)

for m in ["__init__", "_initialize_managers", "_build_doc_status_store", "_initialize_stages"]:
    checkpoint(DataIngestionPipeline, m)
for cls in DataIngestionPipeline.STAGE_CLASSES.values():
    checkpoint(cls, "__init__")

config = get_config()                       # no config.yaml -> all defaults
pipeline_config = PipelineConfig(
    stages_enabled=dict.fromkeys(PipelineStageType, True),
    local_directory=Path("cache"),
)
print("--- about to call DataIngestionPipeline(...) ---")
p = DataIngestionPipeline(
    config=config, pipeline_config=pipeline_config,
    source_directory=Path("docs"), boto_session=boto3.Session(region_name="us-east-1"),
)
print("--- constructor returned. What does the object hold now? ---")
print("source_directory :", p.source_directory)
print("target_directory :", p.target_directory)
print("providers        :", type(p.providers).__name__)
print("cache_manager    :", type(p.cache_manager).__name__, "| strategy =", p.cache_manager.strategy)
print("state_manager    :", type(p.state_manager).__name__)
print("resume_manager   :", type(p.resume_manager).__name__)
print("s3_cache_manager :", p.s3_cache_manager)
print("stages built     :", len(p.stages))
for i, s in enumerate(p.stages, 1):
    print(f"   {i:>2}. {s.name:<22} ({type(s).__name__})")
skipped = [t.value for t in DataIngestionPipeline.STAGE_CLASSES if t.value not in p.name_to_type_map]
print("stages skipped   :", skipped)
print("gleaning.enabled =", config.processing.gleaning.enabled,
      "| claim_extraction.enabled =", config.processing.claim_extraction.enabled,
      "| community_detection.enabled =", config.graph.community_detection.enabled,
      "| dynamodb.enabled =", config.aws.dynamodb.enabled)
print("files on disk in cache/:", sorted(str(x) for x in Path("cache").rglob("*")))
```

`reproduce/scripts/step2b.py`: the same with only parsing and loading enabled.

```python
import functools, sys, logging
from pathlib import Path
import boto3
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.domain.models import PipelineConfig, PipelineStageType
from unified_kg_rag.application.ingestion import pipeline as P
from unified_kg_rag.application.ingestion.pipeline import DataIngestionPipeline

n = [0]
def checkpoint(cls, name):
    orig = getattr(cls, name)
    @functools.wraps(orig)
    def wrapper(self, *a, **k):
        n[0] += 1
        print(f"CHECKPOINT {n[0]:>2}: entering {cls.__name__}.{name}")
        return orig(self, *a, **k)
    setattr(cls, name, wrapper)

for m in ["__init__", "_initialize_managers", "_build_doc_status_store", "_initialize_stages"]:
    checkpoint(DataIngestionPipeline, m)
for cls in DataIngestionPipeline.STAGE_CLASSES.values():
    checkpoint(cls, "__init__")

config = get_config()                       # no config.yaml -> all defaults
pipeline_config = PipelineConfig(
    stages_enabled={t: t in (PipelineStageType.DOCUMENT_PARSING, PipelineStageType.DOCUMENT_LOADING) for t in PipelineStageType},
    local_directory=Path("cache"),
)
print("--- about to call DataIngestionPipeline(...) ---")
p = DataIngestionPipeline(
    config=config, pipeline_config=pipeline_config,
    source_directory=Path("docs"), boto_session=boto3.Session(region_name="us-east-1"),
)
print("--- constructor returned. What does the object hold now? ---")
print("source_directory :", p.source_directory)
print("target_directory :", p.target_directory)
print("providers        :", type(p.providers).__name__)
print("cache_manager    :", type(p.cache_manager).__name__, "| strategy =", p.cache_manager.strategy)
print("state_manager    :", type(p.state_manager).__name__)
print("resume_manager   :", type(p.resume_manager).__name__)
print("s3_cache_manager :", p.s3_cache_manager)
print("stages built     :", len(p.stages))
for i, s in enumerate(p.stages, 1):
    print(f"   {i:>2}. {s.name:<22} ({type(s).__name__})")
skipped = [t.value for t in DataIngestionPipeline.STAGE_CLASSES if t.value not in p.name_to_type_map]
print("stages skipped   :", skipped)
print("gleaning.enabled =", config.processing.gleaning.enabled,
      "| claim_extraction.enabled =", config.processing.claim_extraction.enabled,
      "| community_detection.enabled =", config.graph.community_detection.enabled,
      "| dynamodb.enabled =", config.aws.dynamodb.enabled)
print("files on disk in cache/:", sorted(str(x) for x in Path("cache").rglob("*")))
```

`reproduce/scripts/step3.py`: first run with checkpoints.

```python
import functools, logging, json
from pathlib import Path
import boto3
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.domain.models import PipelineConfig, PipelineStageType as T
from unified_kg_rag.application.ingestion.pipeline import DataIngestionPipeline as DIP
from unified_kg_rag.application.ingestion import pipeline_stages as PS

n = [0]
def short(v):
    s = repr(v)
    return s if len(s) < 110 else s[:107] + "..."
def checkpoint(cls, name, show=None):
    orig = getattr(cls, name)
    @functools.wraps(orig)
    def wrapper(self, *a, **k):
        n[0] += 1; me = n[0]
        print(f"CHECKPOINT {me:>2}: -> {cls.__name__}.{name}")
        out = orig(self, *a, **k)
        if show: print(f"              returned: {short(show(out, a))}")
        return out
    setattr(cls, name, wrapper)

config = get_config()
pc = PipelineConfig(stages_enabled={t: t in (T.DOCUMENT_PARSING, T.DOCUMENT_LOADING) for t in T},
                    local_directory=Path("cache"))
p = DIP(config=config, pipeline_config=pc, source_directory=Path("docs"),
        boto_session=boto3.Session(region_name="us-east-1"))

checkpoint(DIP, "run")
checkpoint(DIP, "_resolve_pipeline_id", lambda o, a: o)
checkpoint(DIP, "_compute_corpus_fingerprint", lambda o, a: o)
checkpoint(DIP, "_prepare_new_run", lambda o, a: ("start stage =", o[1], "| context.documents =", o[0].documents))
checkpoint(DIP, "_prepare_resume")
checkpoint(DIP, "_execute_pipeline_stages")
checkpoint(DIP, "_execute_stage", lambda o, a: (o.stage_name, o.status.value, "in", o.input_count, "out", o.output_count))
checkpoint(PS.DocumentParsingStage, "_discover_files", lambda o, a: [x.name for x in o])
checkpoint(PS.DocumentParsingStage, "_execute_core", lambda o, a: o)
checkpoint(PS.DocumentLoadingStage, "_execute_core", lambda o, a: o)
checkpoint(DIP, "_save_stage_outputs_to_cache")
checkpoint(DIP, "_finalize_pipeline_execution")

print("--- calling p.run('docs') ---")
ctx = p.run("docs")
print("--- run() returned ---")
print("pipeline_id :", ctx.pipeline_id)
print("status      :", ctx.status.value)
print("documents   :", len(ctx.documents))
d = ctx.documents[0]
print("\nFIRST DOCUMENT, field by field:")
for k, v in d.model_dump(mode="json").items():
    print(f"  {k:<16} = {short(v)}")
print("\nFILES NOW ON DISK under cache/:")
for f in sorted(Path("cache").rglob("*")):
    if f.is_file(): print(f"  {f}  ({f.stat().st_size} bytes)")
```

`reproduce/scripts/step4.py`: scenarios A to D.

```python
import functools, logging, sys
from pathlib import Path
import boto3
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.domain.models import PipelineConfig, PipelineStageType as T
from unified_kg_rag.application.ingestion.pipeline import DataIngestionPipeline as DIP

def scenario(title, pipeline_id=None, force=False):
    print(f"\n=== {title} ===")
    pc = PipelineConfig(stages_enabled={t: t in (T.DOCUMENT_PARSING, T.DOCUMENT_LOADING) for t in T},
                        local_directory=Path("cache"), force_rebuild=force, cache_enabled=not force)
    p = DIP(config=get_config(), pipeline_config=pc, source_directory=Path("docs"),
            boto_session=boto3.Session(region_name="us-east-1"))
    ran = []
    o_exec = p._execute_stage
    p._execute_stage = lambda st, ctx: (ran.append(st.name), o_exec(st, ctx))[1]
    o_res, o_new = p._prepare_resume, p._prepare_new_run
    def res(*a):
        out = o_res(*a); print("  path taken      : RESUME  -> start stage =", out[1]); return out
    def new(*a):
        out = o_new(*a); print("  path taken      : NEW RUN -> start stage =", out[1]); return out
    p._prepare_resume, p._prepare_new_run = res, new
    o_fp = p._compute_corpus_fingerprint
    def fp(src):
        f = o_fp(src); rid = p._resolve_pipeline_id(src, pipeline_id)
        print("  1. pipeline id        :", rid)
        print("  2. not force_rebuild  :", not pc.force_rebuild)
        print("  3. metadata file found:", p.state_manager.pipeline_exists(rid))
        print("  corpus fingerprint    :", f)
        return f
    p._compute_corpus_fingerprint = fp
    ctx = p.run("docs", pipeline_id=pipeline_id)
    print("  stages that actually ran:", ran, "| documents in context:", len(ctx.documents))

OLD = sorted(x.name for x in Path("cache").iterdir())[0]
scenario("A: run again, no pipeline id given")
scenario("B: run again, SAME pipeline id, nothing changed", OLD)
scenario("C: SAME pipeline id + force_rebuild", OLD, force=True)
Path("docs/01_acme.txt").write_text(Path("docs/01_acme.txt").read_text() + "Acme has 120 employees.\n")
scenario("D: SAME pipeline id, but I edited 01_acme.txt", OLD)
```

`reproduce/scripts/fake_llm.py`: the stand-in model.

```python
"""Stand-in model: records every prompt; replies from answers.json (written by hand)."""
import hashlib, json
from pathlib import Path
from typing import Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

PROMPTS = Path("prompts.jsonl"); ANSWERS = Path("answers.json")
PLACEHOLDER = '<?xml version="1.0" encoding="UTF-8"?>\n<chunk_boundaries><single_chunk>true</single_chunk></chunk_boundaries>'

class HandAnsweredModel(BaseChatModel):
    model_id: str = "hand-answered"
    @property
    def _llm_type(self) -> str: return "hand-answered"
    def _generate(self, messages, stop=None, run_manager=None, **kwargs: Any) -> ChatResult:
        parts = [{"role": m.type, "text": m.content if isinstance(m.content, str) else json.dumps(m.content)} for m in messages]
        key = hashlib.sha256(parts[-1]["text"].encode()).hexdigest()[:10]
        answers = json.loads(ANSWERS.read_text()) if ANSWERS.exists() else {}
        reply = answers.get(key); used = "hand-written answer" if reply else "PLACEHOLDER"
        with PROMPTS.open("a") as f:
            f.write(json.dumps({"key": key, "model_id": self.model_id, "messages": parts, "reply_used": used}) + "\n")
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=reply or PLACEHOLDER))])

class HandAnsweredFactory:
    def __init__(self, config): self.config = config; self.requested = []
    def get_model(self, model_id, **kwargs):
        self.requested.append((str(getattr(model_id, "value", model_id)), {k: str(v) for k, v in kwargs.items()}))
        return HandAnsweredModel(model_id=str(getattr(model_id, "value", model_id)))
    def get_model_info(self, model_id): return None
```

`reproduce/scripts/step5.py`: stages 1 to 3 with the stand-in model.

```python
import functools, logging, sys, json
from pathlib import Path
import boto3
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.domain.models import PipelineConfig, PipelineStageType as T
from unified_kg_rag.adapters.providers import Providers
from unified_kg_rag.application.ingestion.pipeline import DataIngestionPipeline as DIP
from unified_kg_rag.adapters.ingestion import chunker as C
from fake_llm import HandAnsweredFactory, PROMPTS

RUN_ID = sys.argv[1]
PROMPTS.unlink(missing_ok=True)
config = get_config()
if len(sys.argv) > 2: config.processing.chunking.min_chunk_size = int(sys.argv[2])
print("min_chunk_size =", config.processing.chunking.min_chunk_size, "| max_chunk_size =", config.processing.chunking.max_chunk_size)
factory = HandAnsweredFactory(config)
providers = Providers(config, boto3.Session(region_name="us-east-1"), llm_factory=factory)
pc = PipelineConfig(stages_enabled={t: t in (T.DOCUMENT_PARSING, T.DOCUMENT_LOADING, T.TEXT_CHUNKING) for t in T},
                    local_directory=Path("cache"), force_rebuild=True, cache_enabled=False)
p = DIP(config=config, pipeline_config=pc, source_directory=Path("docs"), providers=providers)
print("models the chunking stage asked the factory for:")
for mid, kw in factory.requested: print("   ", mid, kw)

o = C.IntelligentTextChunker._create_pre_chunks
def pre(self, content):
    out = o(self, content); print(f"   pre-chunks: {len(out)}  sizes={[len(x) for x in out]}"); return out
C.IntelligentTextChunker._create_pre_chunks = pre
o2 = C.IntelligentTextChunker._chunk_single_document
def one(self, doc):
    print(f"-> _chunk_single_document('{doc.file_name}')")
    out = o2(self, doc)
    for u in out: print(f"   chunk {u.attributes['chunk_id']}/{u.attributes['total_chunks']}  method={u.attributes['chunking_method']:<8} chars={len(u.text):<5} starts: {u.text[:45]!r}")
    return out
C.IntelligentTextChunker._chunk_single_document = one

ctx = p.run("docs", pipeline_id=RUN_ID)
print("\nstage results:", [(r.stage_name, r.status.value, r.input_count, r.output_count) for r in ctx.stage_results])
n = sum(1 for _ in PROMPTS.open()) if PROMPTS.exists() else 0
print("AI calls made:", n)
json.dump([u.model_dump(mode="json") for u in ctx.text_units], open("text_units.json", "w"), indent=1)
```

`reproduce/scripts/answers_handwritten.json`: Claude's replies, keyed by a hash of the prompt.

```json
{
 "266920b75e": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<chunk_boundaries>\n    <line_number>9</line_number>\n    <line_number>17</line_number>\n</chunk_boundaries>",
 "0b6352c8bf": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<chunk_boundaries>\n    <line_number>9</line_number>\n    <line_number>17</line_number>\n</chunk_boundaries>"
}
```

`reproduce/run_all.sh`: the driver.

```bash
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
```

### Appendix C. The chunking stage class

```python
# unified_kg_rag/application/ingestion/pipeline_stages.py, lines 613-662
class TextChunkingStage(PipelineStage):
    def __init__(
        self,
        config: Config,
        boto_session: boto3.Session | None = None,
        providers: Providers | None = None,
    ):
        super().__init__(
            PipelineStageType.TEXT_CHUNKING, config, boto_session, providers
        )

        chunker_type = self.config.processing.chunking.chunker_type
        self.chunker = ChunkerFactory.create_chunker(
            config=self.config,
            boto_session=self.boto_session,
            chunker_type=chunker_type,
            providers=self.providers,
        )
        self.chunker_type = chunker_type

    def _execute_core(
        self, context: PipelineContext
    ) -> tuple[int, int, dict[str, Any] | None]:
        logger.info("=" * 60)
        logger.info("TEXT CHUNKING STAGE - STARTED")
        logger.info("=" * 60)

        text_units = []
        for doc in context.documents:
            chunks = self.chunker.chunk_documents([doc])
            text_units.extend(chunks)

        context.text_units = text_units
        total_chunks = len(text_units)
        doc_count = len(context.documents)

        metrics = {
            "chunker_type": self.chunker_type.value,
            "documents_processed": doc_count,
            "total_chunks": total_chunks,
            "avg_chunks_per_doc": total_chunks / doc_count if doc_count else 0.0,
        }

        logger.info("=" * 60)
        logger.info(
            "TEXT CHUNKING STAGE - COMPLETED (%s text units created)", total_chunks
        )
        logger.info("=" * 60)

        return doc_count, total_chunks, metrics
```

### Appendix D. The chunking prompt

```python
# unified_kg_rag/domain/prompts/data_processing.py, lines 8-124
@dataclass(frozen=True)
class TextChunkingPrompt(BasePrompt):
    input_variables = [
        "numbered_text",
        "min_chunk_size",
        "max_chunk_size",
    ]

    system_prompt_template = """You are an expert document analysis AI that specializes in intelligent semantic chunking
for maximum information retrieval effectiveness. Your goal is to create optimal chunks that preserve semantic coherence
and contextual relationships while maximizing retrieval performance.

CORE OBJECTIVE:
Analyze document structure and content to identify optimal chunk boundaries that maintain semantic integrity, preserve
contextual relationships, and maximize retrieval effectiveness for RAG applications.

CHUNKING STRATEGY (Priority Order):

1. STRUCTURAL BOUNDARIES (Highest Priority):
   • Section headers and subheaders (marked with #, ##, ###)
   • Numbered sections, clauses, and subsections
   • Document divisions and parts
   • Clear topic transitions
   • Chapter or article boundaries

2. SEMANTIC BOUNDARIES (High Priority):
   • Topic shifts and thematic changes
   • Concept transitions
   • Entity or subject changes
   • Process or procedure boundaries
   • Definition and explanation sections

3. LOGICAL BOUNDARIES (Medium Priority):
   • List beginnings and endings
   • Table boundaries
   • Paragraph transitions with topic shifts
   • Examples and case studies
   • Conclusion and summary sections

4. SIZE-DRIVEN BOUNDARIES (Fallback):
   • Natural sentence endings within size limits
   • Paragraph breaks when necessary
   • Punctuation-based splits as last resort

INTELLIGENT SIZE OPTIMIZATION:
• Target range: {min_chunk_size} to {max_chunk_size} characters
• Prioritize semantic completeness over strict size adherence
• Merge small fragments to achieve minimum viable chunk size
• Split oversized sections at natural semantic boundaries
• Ensure each chunk provides standalone contextual value
• Maintain hierarchical relationships where possible

BOUNDARY SELECTION RULES:
• Analyze numbered lines to identify semantic boundaries
• Select line numbers where new chunks should logically begin
• Consider cumulative character count for size optimization
• Ensure chunks fall within target range when possible
• NEVER select line 1 as a boundary (document always starts there)
• Prefer semantic coherence over perfect size matching"""

    human_prompt_template = """Analyze the following document to determine optimal semantic chunk boundaries that
maximize information retrieval effectiveness while preserving semantic integrity and contextual relationships.

The document is split into numbered lines. Identify line numbers where new chunks should begin.

EXAMPLE:
INPUT DOCUMENT:
1: # Project Overview
2: This project involves comprehensive system analysis.
3:
4: ## 1. System Requirements
5: The system must handle multiple data sources and provide real-time processing.
6:
7: ### 1.1 Performance Requirements
8: Response time should not exceed 100ms for standard queries.
9:
10: ## 2. Technical Specifications
11: The architecture follows microservices patterns with containerized deployment.

TARGET: 100-300 characters

OUTPUT:
<?xml version="1.0" encoding="UTF-8"?>
<chunk_boundaries>
    <line_number>4</line_number>
    <line_number>7</line_number>
    <line_number>10</line_number>
</chunk_boundaries>

---

DOCUMENT TO ANALYZE:
{numbered_text}

CHUNKING PARAMETERS:
- Target chunk size: {min_chunk_size} to {max_chunk_size} characters

ANALYSIS PROCESS:
1. Identify structural elements (headers, sections, lists) by line numbers
2. Locate semantic transition points between different topics
3. Calculate cumulative character count to ensure appropriate chunk sizes
4. Select line numbers that preserve semantic coherence
5. Output line numbers where new chunks should begin

OUTPUT REQUIREMENTS:
1. **XML FORMAT ONLY**: Start with `<?xml` and end with `</chunk_boundaries>`
2. **LINE NUMBERS ONLY**: Each `<line_number>` contains only an integer
3. **NO LINE 1**: Never include line 1 as a boundary
4. **SINGLE CHUNK**: If text should remain as one chunk, output:
   `<chunk_boundaries><single_chunk>true</single_chunk></chunk_boundaries>`
5. **ASCENDING ORDER**: Line numbers in ascending order
6. **VALID LINES**: Only reference existing line numbers

Provide ONLY the XML output with no additional text or explanations.

<?xml version="1.0" encoding="UTF-8"?>
<chunk_boundaries>"""
```

### Appendix E. The sample documents

Each of these files ends with one newline after the text shown (see section 0.5).

`reproduce/docs_original/01_acme.txt`

```text
Acme Robotics is a company based in Pune. It was founded by Meera Shah in 2015. Acme builds warehouse robots.
```

`reproduce/docs_original/02_meera.txt`

```text
Meera Shah studied engineering at IIT Bombay. Before Acme Robotics she worked at Orbit Logistics as a hardware lead.
```

`reproduce/docs_original/03_orbit.txt`

```text
Orbit Logistics runs warehouses in Mumbai and Chennai. In 2022 Orbit Logistics signed a supply contract with Acme Robotics.
```

`reproduce/docs_original/04_product.txt`

```text
The Acme Picker X2 is a warehouse robot that lifts up to 40 kg. Orbit Logistics uses the Picker X2 in its Chennai warehouse.
```

`reproduce/docs_original/05_investor.txt`

```text
Banyan Capital invested in Acme Robotics in 2019. Ravi Menon, a partner at Banyan Capital, sits on the Acme board.
```

`reproduce/docs_added/06_profile.txt`

```text
# Acme Robotics: Company Profile

Acme Robotics is a warehouse automation company headquartered in Pune, India. It designs and builds mobile robots that move goods inside warehouses. The company sells mainly to logistics operators and large retailers.

## History

Acme Robotics was founded in 2015 by Meera Shah, a hardware engineer who had studied at IIT Bombay.
Before starting Acme, Shah worked at Orbit Logistics as a hardware lead, where she saw how much time warehouse staff spent walking between shelves.
The first prototype was built in a rented garage in Pune during 2016.
In 2017 the company moved to a larger workshop in Hinjewadi and hired its first ten engineers.
By 2019 Acme had shipped robots to four customers and opened a small service office in Chennai.
In 2022 the company signed its largest supply contract so far, with Orbit Logistics.

## Products

The main product is the Acme Picker X2, a wheeled robot that lifts loads of up to 40 kg and carries them to a packing station.
The Picker X2 replaced the original Picker X1, which could lift only 15 kg and needed floor markers to navigate.
The X2 navigates with cameras and a laser scanner, so it does not need floor markers.
Acme also sells Fleet Console, a software dashboard that lets a warehouse manager see where every robot is and assign tasks.
A typical installation uses between 20 and 60 robots together with one Fleet Console licence.
Battery life is about eight hours, and a robot returns to its charging dock on its own when the battery is low.

## Customers

Orbit Logistics is the largest customer and uses the Picker X2 in its Chennai warehouse.
Orbit Logistics also runs warehouses in Mumbai, where a second installation is planned.
Other customers include a grocery chain in Bengaluru and two electronics distributors in Hyderabad.
Customers usually sign a three-year service agreement that covers repairs and software updates.
Most new customers come through referrals from existing ones.

## Funding and Board

Banyan Capital invested in Acme Robotics in 2019, in the company's first outside funding round.
Ravi Menon, a partner at Banyan Capital, joined the Acme board after that investment.
The board also includes Meera Shah and one independent director.
Acme has said it plans to raise a second round to expand into Southeast Asia.
The company employs about 120 people, most of them engineers and service technicians.
```

`reproduce/docs_added/07_review.txt`

```text
Acme Robotics annual review, prepared for the board by the operations team.
The Chennai installation at Orbit Logistics ran for the full year with sixty Picker X2 robots on the warehouse floor.
Average uptime across the fleet was ninety-six percent, slightly below the ninety-eight percent promised in the service agreement.
Most of the downtime came from worn drive wheels, which had to be replaced on forty of the sixty robots during the summer.
The service office in Chennai added two technicians in June so that a failed robot could be repaired within one working day.
Orbit Logistics reported that the time a picker spends walking fell by roughly half compared with the year before the robots arrived.
A software fault in Fleet Console caused a four-hour stoppage in August, and a patch was released the following week.
Orbit Logistics has asked for a written plan to bring uptime back above the agreed level before the contract is renewed.
The engineering team spent most of the year designing the Picker X3, the planned successor to the Picker X2.
The X3 is intended to lift sixty kilograms, which is twenty kilograms more than the X2 can carry today.
Priya Nair, who leads hardware engineering, chose a new motor supplier in Coimbatore after the old supplier missed two deliveries.
The first X3 prototype completed a week of continuous testing in the Hinjewadi workshop in October without a mechanical failure.
Battery life on the prototype is about six hours, shorter than the eight hours of the X2, because the larger motors draw more power.
The team is evaluating a bigger battery pack, but it would add weight and raise the price of each robot by about eight percent.
Fleet Console will need an update so that a warehouse can run X2 and X3 robots side by side in one fleet.
Meera Shah has set a target of shipping the first X3 units to a paying customer in the second half of next year.
Acme Robotics hired thirty-one people during the year, bringing the total to about one hundred and twenty employees.
Most of the new hires were service technicians and software engineers, with a smaller number joining the sales team.
The company opened a sales office in Singapore in September, its first location outside India.
Arjun Rao moved from Pune to lead the Singapore office and has started talks with two logistics operators there.
Banyan Capital has indicated that it would take part in a second funding round to pay for the Southeast Asia expansion.
Ravi Menon, the Banyan Capital partner on the board, asked for a detailed hiring plan before the round is opened.
The board discussed whether to build a small assembly line in Singapore or to keep shipping finished robots from Pune.
No decision was taken, and the operations team will present costs for both options at the next board meeting.
```

### Appendix F. Results of the checker

**[RAN]** `reproduce/scripts/check_expected.py` on the 11 October output:

```text
PASS  resume after force rebuild reuses run 1's marked output (section 13, step 4)
PASS  commit  ->  37ef4a7df28bdd19a5f277d30aff026ddf8cbd50
PASS  run id prefix for a folder named docs  ->  pipeline-46b42b42-
PASS  folder fingerprint, 5 original docs  ->  returned: '70f976b347ba'
PASS  folder fingerprint, after editing 01_acme.txt  ->  corpus fingerprint    : 11e583bd8e55
PASS  parsing output name, original docs  ->  document_parsing/documents-2e1fc5080839.json
PASS  loading output name, original docs  ->  document_loading/documents-76101e2dcda9.json
PASS  parsing output name, edited docs  ->  document_parsing/documents-54cf4641e850.json
PASS  loading output name, edited docs  ->  document_loading/documents-0842cedc0821.json
PASS  name the early check looks for, parsing  ->  key: 'documents-1035b7a62512'
PASS  name the early check looks for, loading  ->  key: 'documents-ac616352a4e7'
PASS  scenario B resumes at loading  ->  path taken      : RESUME  -> start stage = document_loading
PASS  scenario D rewinds to parsing  ->  path taken      : RESUME  -> start stage = document_parsing
PASS  all-stage constructor stops at chunking  ->  CHECKPOINT  7: entering TextChunkingStage.__init__
PASS  force rebuild skips saving  ->  Cache disabled, skipping output save for stage: 'document_parsing'
PASS  expiry rewind  ->  Rewinding resume point from 'document_loading' to 'document_parsing'
PASS  chunking prompt key, default settings  ->  prompt 266920b75e
PASS  chunking prompt key, min 900  ->  prompt 0b6352c8bf
PASS  06_profile pre-chunks  ->  pre-chunks: 2  sizes=[1532, 884]
PASS  07_review single chunk under defaults  ->  chunk 1/1  method=llm      chars=2801
PASS  07_review three chunks with min 900  ->  chunk 3/3  method=llm      chars=904
PASS  merge joins with no separator  ->  renewed.The engineering team
PASS  threshold change keeps gleaning  ->  gleaning              6d3b14e6d688   6d3b14e6d688   yes
PASS  threshold change redoes graph_resolution  ->  graph_resolution      7d5bce1ee591   cc32ecbec5bb   NO - redo

24/24 expected values found
```

### Appendix G. The helper scripts

Small scripts called by `run_all.sh`, followed by scripts run by hand: three stage 3 follow-ups (`overlap_demo.py`, `trace_ai_answers.py`, `trace_oversized.py`, section 8.6) and the stage 4 scripts (`stage4.py`, `lang_format_demo.sh`, section 9.1; `answers_es.json` is shown in section 9.1). Each one's first lines say what it does.

`reproduce/scripts/graph.py`

```python
import ast, pathlib, sys, collections
root = pathlib.Path(sys.argv[1])
pkg = root / "unified_kg_rag"
mods = {}
for p in sorted(pkg.rglob("*.py")):
    name = ".".join(p.relative_to(root).with_suffix("").parts)
    if name.endswith(".__init__"): name = name[:-9]
    mods[name] = p
edges = collections.defaultdict(set)
stats = {}
for name, p in mods.items():
    tree = ast.parse(p.read_text())
    classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
    funcs = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    stats[name] = (len(p.read_text().splitlines()), classes, funcs)
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.level == 0 and n.module.startswith("unified_kg_rag"):
            edges[name].add(n.module)
        elif isinstance(n, ast.ImportFrom) and n.level > 0:
            base = name.split(".")
            if not p.name == "__init__.py": base = base[:-1]
            base = base[: len(base) - (n.level - 1)]
            edges[name].add(".".join(base + ([n.module] if n.module else [])))
layer = lambda m: m.split(".")[1] if "." in m else "root"
lc = collections.Counter()
for a, bs in edges.items():
    for b in bs:
        if layer(a) != layer(b): lc[(layer(a), layer(b))] += 1
print("LAYER EDGES (importer -> imported: count)")
for (a, b), c in sorted(lc.items()): print(f"  {a:14s} -> {b:14s} {c}")
print("\nLINES PER LAYER")
ll = collections.Counter()
for m, (n, _, _) in stats.items(): ll[layer(m)] += n
for k, v in ll.most_common(): print(f"  {k:14s} {v}")
print("\nMODULES (lines | classes | top-level funcs)")
for m, (n, c, f) in stats.items():
    if n > 5: print(f"{m.replace('unified_kg_rag.','')} | {n} | {','.join(c)} | {','.join(f)}")
```

`reproduce/scripts/keys_demo.py`

```python
"""Cache-key names with and without the folder fingerprint (evidence for bug 1).
Usage: python keys_demo.py <folder fingerprint>"""
import logging, sys; logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.shared.utils import stage_cache_key
from unified_kg_rag.domain.models import PipelineStageType as T
c = get_config(); fp = sys.argv[1]
for name, t in (("parsing", T.DOCUMENT_PARSING), ("loading", T.DOCUMENT_LOADING)):
    print(f"{name} key, NO folder fingerprint : {stage_cache_key(c, t, 'documents', None)}")
    print(f"{name} key, with {fp}      : {stage_cache_key(c, t, 'documents', fp)}")
```

`reproduce/scripts/manifest_demo.py`

```python
"""Recompute the folder fingerprint by hand: one line per file = path, size, sha256.
Usage: python manifest_demo.py <docs dir>"""
import hashlib, sys
from pathlib import Path
from unified_kg_rag.shared.utils.common import compute_hash
root = Path(sys.argv[1]).resolve(); entries = []
for p in sorted(root.rglob("*")):
    if p.is_file():
        e = f"{p.relative_to(root).as_posix()}\t{p.stat().st_size}\t{hashlib.sha256(p.read_bytes()).hexdigest()}"
        entries.append(e); print("  ", e[:60] + "...")
print("  fingerprint =", compute_hash("\n".join(entries), length=12))
```

`reproduce/scripts/threshold_demo.py`

```python
"""Which stages' cache fingerprints change when one late setting changes.
Usage: python threshold_demo.py <folder fingerprint>"""
import logging, sys; logging.disable(logging.CRITICAL)
from unified_kg_rag.domain.models import Config, PipelineStageType as T
from unified_kg_rag.shared.utils.cache_keys import stage_input_fingerprint as fp
a = Config(); b = Config(); corpus = sys.argv[1]
print("similarity_threshold default:", a.processing.similarity_threshold)
b.processing.similarity_threshold = round(a.processing.similarity_threshold - 0.05, 2)
print("changed to:", b.processing.similarity_threshold, "\n")
print(f"{'stage':<22}{'before':<15}{'after':<15}still valid?")
for t in T:
    x, y = fp(a, t, corpus), fp(b, t, corpus)
    print(f"{t.value:<22}{x:<15}{y:<15}{'yes' if x==y else 'NO - redo'}")
```

`reproduce/scripts/merge_demo.py`

```python
"""Call the chunker's merge function directly on the three pieces of 07_review.txt.
Usage: python merge_demo.py <path to 07_review.txt>"""
import logging, sys; logging.disable(logging.CRITICAL)
from unified_kg_rag.adapters.ingestion.chunker import ChunkProcessor
text = open(sys.argv[1]).read().rstrip("\n")
lines = text.split("\n")
pieces = ["\n".join(lines[0:8]), "\n".join(lines[8:16]), "\n".join(lines[16:24])]
print("three pieces (lines 1-8, 9-16, 17-24), sizes:", [len(p) for p in pieces])
merged = ChunkProcessor(1000, 8000).merge_small_chunks(list(pieces))
print("after merge_small_chunks (min 1000, max 8000):", [len(m) for m in merged])
i = merged[0].index("The engineering team")
print("text at the first join:", repr(merged[0][i-28:i+24]))
```

`reproduce/scripts/filter_demo.py`

```python
"""Run the real file-filter conditions of DocumentParsingStage._discover_files on a messy folder.
Usage: python filter_demo.py <empty work dir>"""
import logging, sys; logging.disable(logging.CRITICAL)
from pathlib import Path
from unified_kg_rag.application.ingestion.pipeline_stages import DocumentParsingStage as D
from unified_kg_rag.adapters.ingestion.parser import ParserFactory
base = Path(sys.argv[1]); src = base / "src"
for d in ("sub", "cache/run1", "__pycache__"): (src / d).mkdir(parents=True, exist_ok=True)
for f, t in (("a.txt","hi"),("sub/b.txt","hi"),(".secret.txt","hi"),("notes.docx","hi"),("__pycache__/x.pyc","hi"),
             ("__pycache__/y.txt","hi"),("cache/run1/documents.json","{}"),("real.json","{}")): (src / f).write_text(t + "\n")
ext = ParserFactory.get_supported_extensions(); owned = [(src / "cache").resolve()]
print("supported:", ext); print("owned_dirs: [<abs>/src/cache]")
print(f"{'path':<32}{'is_file':<9}{'ext ok':<8}{'excluded':<10}{'in owned':<10}KEPT")
for f in sorted(src.rglob("*")):
    a = f.is_file(); b = f.suffix.lower() in ext; c = D._should_exclude_file(f)
    d = any(f.resolve().is_relative_to(o) for o in owned)
    print(f"{str(f.relative_to(base)):<32}{str(a):<9}{str(b):<8}{str(c):<10}{str(d):<10}{a and b and not c and not d}")
print("\nis_relative_to demo:")
for x in ["/data/src/cache/run1/documents.json", "/data/src/real.json", "/data/src/cache2/x.json"]:
    print(f"  Path({x!r}).is_relative_to('/data/src/cache') ->", Path(x).is_relative_to("/data/src/cache"))
```

`reproduce/scripts/logfilter.py`

```python
"""Print a run-ingestion log in readable form: JSON log events as 'LOG: ...', other lines as-is."""
import json, sys
BOX = set("─│╭╮╰╯ █╗╔╝╚═║")
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    line = line.rstrip("\n")
    s = line.strip()
    if s.startswith("{"):
        try: e = json.loads(s)["event"]
        except Exception: continue
        if set(e) <= set("= "): continue
        print("LOG:", e[:240])
    elif s and "Warning" not in s and "warn(" not in s and not set(s) <= BOX and "█" not in s:
        print(s[:200])
```

`reproduce/scripts/mark_cache.py`

```python
"""Stamp MARKER-FROM-FIRST-RUN into the first document of every saved stage output of a run.
Usage: python mark_cache.py <cache/run-id dir>"""
import json, glob, sys
for f in sorted(glob.glob(sys.argv[1] + "/document_*/*.json")):
    d = json.load(open(f)); d[0]["page_content"] = "MARKER-FROM-FIRST-RUN " + d[0]["page_content"]
    json.dump(d, open(f, "w"), indent=2)
```

`reproduce/scripts/show_cache.py`

```python
"""List a run's saved stage outputs: file, save time, start of document 1's text.
Usage: python show_cache.py <cache/run-id dir>"""
import json, glob, sys, os, time
for f in sorted(glob.glob(sys.argv[1] + "/document_*/*.json")):
    t = time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(f)))
    print(f"   {f} | saved at {t} | doc1 text starts: {json.load(open(f))[0]['page_content'][:28]}")
```

`reproduce/scripts/ttl_tools.py`

```python
"""Usage: python ttl_tools.py show|expire <cache/run-id dir>"""
import json, sys
p = sys.argv[2] + "/cache_index.json"; i = json.load(open(p))
if sys.argv[1] == "show":
    for k, e in i["entries"].items(): print("   entry", k, "| created", e["created_at"][:19], "| expires", e["expires_at"][:19])
else:
    for e in i["entries"].values(): e["expires_at"] = "2000-01-01T00:00:00"
    json.dump(i, open(p, "w"), indent=2); print("   expiry of every entry set to 2000-01-01")
```

`reproduce/scripts/show_prompts.py`

```python
"""Usage: python show_prompts.py [full]  -- list prompts captured by the stand-in model."""
import json, sys, os
if not os.path.exists("prompts.jsonl"): print("   (no prompts captured)"); sys.exit()
for l in open("prompts.jsonl"):
    d = json.loads(l); h = d["messages"][-1]["text"]
    print("   prompt", d["key"], "| model:", d["model_id"], "| reply used:", d["reply_used"], "|", [x for x in h.splitlines() if x.startswith("- Target")][0])
    if len(sys.argv) > 1:
        for m in d["messages"]: print(f"--- {m['role']} message: {len(m['text'])} chars ---")
        print(h[h.index("DOCUMENT TO ANALYZE"):])
```

`reproduce/scripts/check_expected.py`

```python
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
```

`reproduce/scripts/overlap_demo.py`

```python
"""Measure overlap between neighbouring chunks: size-only splitter versus the cuts chosen by the model."""
import logging; logging.disable(logging.CRITICAL)
from unified_kg_rag.domain.models import Config
from unified_kg_rag.adapters.ingestion.chunker import SimpleTextChunker
from unified_kg_rag.adapters.aws.token_counter import estimate_token_count
def overlap(a, b):
    for n in range(min(len(a), len(b)), 0, -1):
        if a[-n:] == b[:n]: return n
    return 0
one = open("docs/07_review.txt").read()
text = "\n".join(f"[copy {c}] {l}" for c in range(1, 6) for l in one.rstrip("\n").split("\n"))
cfg = Config(); ch = cfg.processing.chunking
print("settings: fallback_chunk_size =", ch.fallback_chunk_size, "| chunk_overlap =", ch.chunk_overlap, "| min =", ch.min_chunk_size, "| max =", ch.max_chunk_size)
print("input text:", len(text), "characters")
raw = SimpleTextChunker(cfg, show_progress=False).fallback_splitter.split_text(text)
print("\nsize-only splitter (used by the 'simple' chunker and the fallback path):")
for i, c in enumerate(raw): print(f"  piece {i+1}: {len(c)} chars" + (f" | shares its first {overlap(raw[i-1], c)} chars with the end of piece {i}" if i else ""))
print("\nmodel path, the three chunks of 07_review.txt (lines 1-8, 9-16, 17-24):")
ls = one.rstrip("\n").split("\n"); p = ["\n".join(ls[0:8]), "\n".join(ls[8:16]), "\n".join(ls[16:24])]
for i in (1, 2): print(f"  chunk {i+1} shares {overlap(p[i-1], p[i])} chars with the end of chunk {i}")
print("\ntoken estimate for the middle chunk:", estimate_token_count(p[1]), "| its length in characters:", len(p[1]))
```

`reproduce/scripts/trace_ai_answers.py`

```python
"""Feed different model replies into the real chunker and watch, checkpoint by checkpoint, what it does with each."""
import functools, json, logging, sys
from pathlib import Path
import boto3
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.adapters.providers import Providers
from unified_kg_rag.adapters.ingestion import chunker as C
from unified_kg_rag.adapters.ingestion.parser import ParserFactory
from fake_llm import HandAnsweredFactory, PROMPTS, ANSWERS

KEY = "0b6352c8bf"   # hash of the chunking prompt for 07_review.txt with min_chunk_size=900
X = '<?xml version="1.0" encoding="UTF-8"?>\n<chunk_boundaries>\n%s\n</chunk_boundaries>'
CASES = [
 ("1. sensible reply: lines 9 and 17",                X % "<line_number>9</line_number><line_number>17</line_number>"),
 ("2. a line that does not exist: 9 and 99",          X % "<line_number>9</line_number><line_number>99</line_number>"),
 ("3. forbidden or nonsense numbers: 1, 0, -5, 9",    X % "<line_number>1</line_number><line_number>0</line_number><line_number>-5</line_number><line_number>9</line_number>"),
 ("4. words instead of numbers",                      X % "<line_number>nine</line_number><line_number>seventeen</line_number>"),
 ("5. model writes its own text instead of numbers",  X % "<chunk>Acme Robotics was founded on the Moon in 1850.</chunk><chunk>It has two million employees.</chunk>"),
 ("6. model adds invented text AND a line number",    X % "<summary>Acme was founded on the Moon.</summary><line_number>9</line_number>"),
 ("7. not XML at all",                                "Sure! I would cut it after the part about Chennai, around line 9."),
]

def short(v, n=120):
    s = repr(v); return s if len(s) <= n else s[:n-3] + "..."
def checkpoint(cls, name, show_args=False):
    orig = cls.__dict__[name]; static = isinstance(orig, staticmethod); f = orig.__func__ if static else orig
    @functools.wraps(f)
    def w(*a, **k):
        out = f(*a, **k); args = a if static else a[1:]
        print(f"   CHECKPOINT {cls.__name__}.{name}" + (f"({short(args[-1], 70)})" if show_args else "") + f" -> {short(out)}")
        return out
    setattr(cls, name, staticmethod(w) if static else w)

checkpoint(C.IntelligentTextChunker, "_get_boundary_results")
checkpoint(C.LineBasedBoundaryProcessor, "extract_line_numbers", show_args=True)
checkpoint(C.LineBasedBoundaryProcessor, "convert_line_numbers_to_indices")
checkpoint(C.LineBasedBoundaryProcessor, "validate_error_rate")
checkpoint(C.IntelligentTextChunker, "_create_fallback_chunks")
o = C.IntelligentTextChunker._chunk_with_llm_boundaries
def cwb(self, text, response):
    out = o(self, text, response)
    print("   CHECKPOINT IntelligentTextChunker._chunk_with_llm_boundaries ->", "None (reply rejected)" if out is None else f"{len(out)} piece(s), sizes {[len(x) for x in out]}")
    return out
C.IntelligentTextChunker._chunk_with_llm_boundaries = cwb

config = get_config(); config.processing.chunking.min_chunk_size = 900
providers = Providers(config, boto3.Session(region_name="us-east-1"), llm_factory=HandAnsweredFactory(config))
chunker = C.IntelligentTextChunker(config, providers=providers, show_progress=False)
path = Path("docs/07_review.txt"); original = path.read_text()
doc = ParserFactory.create_parser(path, config).parse_file(path, None)
print("settings: min_chunk_size = 900, max_chunk_size = 8000, max_marker_miss_rate =", config.processing.chunking.max_marker_miss_rate)
print("document: 07_review.txt, 24 lines,", len(original), "bytes\n")
for label, reply in CASES:
    print("=" * 100); print("CASE", label); print("   model reply:", short(reply.replace('<?xml version="1.0" encoding="UTF-8"?>\n', ""), 170))
    ANSWERS.write_text(json.dumps({KEY: reply})); PROMPTS.unlink(missing_ok=True)
    units = chunker._chunk_single_document(doc)
    calls = [json.loads(l) for l in PROMPTS.open()]
    print(f"   model calls made: {len(calls)}  " + str([(c['model_id'].split('.')[-1], c['reply_used']) for c in calls]))
    print("   RESULT:", [(u.attributes["chunking_method"], len(u.text)) for u in units])
    print("   every chunk is an exact piece of the original file:", all(u.text in original for u in units),
          "| any invented words in a chunk:", any(("Moon" in u.text or "million" in u.text) for u in units))
```

`reproduce/scripts/trace_oversized.py`

```python
"""What happens to a long piece of text when the model's reply contains no usable line numbers."""
import json, logging, hashlib
from pathlib import Path
import boto3
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.adapters.providers import Providers
from unified_kg_rag.adapters.ingestion import chunker as C
from unified_kg_rag.adapters.ingestion.parser import ParserFactory
from fake_llm import HandAnsweredFactory, PROMPTS, ANSWERS

one = Path("docs/07_review.txt").read_text().rstrip("\n").split("\n")
long_text = "\n".join(f"[copy {c}] {l}" for c in range(1, 9) for l in one) + "\n"   # 8 copies, no headings
Path("longdoc").mkdir(exist_ok=True); p = Path("longdoc/08_long.txt"); p.write_text(long_text)
config = get_config(); ch = config.processing.chunking
print(f"settings (defaults): min_chunk_size={ch.min_chunk_size}, max_chunk_size={ch.max_chunk_size}, pre_chunk_size={ch.pre_chunk_size}")
print("document: 08_long.txt,", len(long_text), "characters, no headings\n")
providers = Providers(config, boto3.Session(region_name="us-east-1"), llm_factory=HandAnsweredFactory(config))
chunker = C.IntelligentTextChunker(config, providers=providers, show_progress=False)
doc = ParserFactory.create_parser(p, config).parse_file(p, None)
X = '<?xml version="1.0" encoding="UTF-8"?>\n<chunk_boundaries>%s</chunk_boundaries>'
REPLIES = [("model says keep as one chunk", X % "<single_chunk>true</single_chunk>"),
           ("model writes words instead of numbers", X % "<line_number>forty</line_number><line_number>ninety</line_number>"),
           ("model gives usable numbers (lines 49, 97, 145)", X % "<line_number>49</line_number><line_number>97</line_number><line_number>145</line_number>")]
ANSWERS.unlink(missing_ok=True); PROMPTS.unlink(missing_ok=True)
chunker._chunk_single_document(doc)                       # capture pass, to learn the prompt's key
key = json.loads(PROMPTS.open().readline())["key"]
for label, reply in REPLIES:
    ANSWERS.write_text(json.dumps({key: reply})); PROMPTS.unlink(missing_ok=True)
    chunker.stats = C.ChunkingStats()
    units = chunker._chunk_single_document(doc)
    sizes = [len(u.text) for u in units]
    print(f"REPLY: {label}")
    print(f"   chunks: {[(u.attributes['chunking_method'], len(u.text)) for u in units]}")
    print(f"   largest chunk: {max(sizes)} characters | over max_chunk_size ({ch.max_chunk_size}): {max(sizes) > ch.max_chunk_size}")
    print(f"   stats: llm_processing_failures={chunker.stats.llm_processing_failures}, fallback_chunks_used={chunker.stats.fallback_chunks_used}")
    print(f"   quality check: {chunker.quality_validator.validate_chunks([u.text for u in units])['issues']}\n")
```

`reproduce/scripts/stage4.py`

```python
"""Stage 4 (translation) with checkpoints.  Usage: python stage4.py default|es|es-broken"""
import functools, json, logging, sys
from pathlib import Path
import boto3
logging.disable(logging.CRITICAL)
from langchain_core.language_models.chat_models import BaseChatModel
from unified_kg_rag.shared import get_config
from unified_kg_rag.domain.models import PipelineConfig, PipelineStageType as T, LanguageCode
from unified_kg_rag.adapters.providers import Providers
from unified_kg_rag.application.ingestion.pipeline import DataIngestionPipeline as DIP
from unified_kg_rag.application.ingestion import pipeline_stages as PS
from unified_kg_rag.adapters.ingestion import translator as TR
import fake_llm
from fake_llm import HandAnsweredFactory, HandAnsweredModel, PROMPTS, ANSWERS

mode = sys.argv[1]
def short(v, n=110):
    s = repr(v); return s if len(s) <= n else s[:n-3] + "..."
def checkpoint(cls, name, show=lambda out, a: out):
    orig = getattr(cls, name)
    @functools.wraps(orig)
    def w(self, *a, **k):
        print(f"CHECKPOINT -> {cls.__name__}.{name}")
        out = orig(self, *a, **k); print(f"           returned: {short(show(out, a))}"); return out
    setattr(cls, name, w)

class BrokenModel(HandAnsweredModel):
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        raise RuntimeError("simulated model outage")
class BrokenFactory(HandAnsweredFactory):
    def get_model(self, model_id, **kwargs):
        self.requested.append((str(getattr(model_id, "value", model_id)), {}))
        return BrokenModel(model_id=str(getattr(model_id, "value", model_id)))

config = get_config()
if mode != "default": config.processing.translation.target_language = LanguageCode.ES
tc = config.processing.translation
print(f"translation settings: enabled={tc.enabled} | source={tc.source_language.value} | target={tc.target_language.value} | additional={tc.additional_target_languages} | is_noop={tc.is_noop}")
factory = (BrokenFactory if mode == "es-broken" else HandAnsweredFactory)(config)
providers = Providers(config, boto3.Session(region_name="us-east-1"), llm_factory=factory)
pc = PipelineConfig(stages_enabled={t: t in (T.DOCUMENT_PARSING, T.DOCUMENT_LOADING, T.TEXT_CHUNKING, T.TRANSLATION) for t in T},
                    local_directory=Path("cache4"))
p = DIP(config=config, pipeline_config=pc, source_directory=Path("docs5"), providers=providers)
print("stages built:", [s.name for s in p.stages])
print("models asked for while BUILDING the pipeline:", [m for m, _ in factory.requested]); n_before = len(factory.requested)

checkpoint(PS.TranslationStage, "_should_skip")
checkpoint(PS.TranslationStage, "_execute_core")
checkpoint(TR.TextUnitTranslator, "__init__", lambda out, a: "translator built")
checkpoint(TR.TextUnitTranslator, "translate_text_units", lambda out, a: f"{len(out)} units; same list object that went in: {out is a[0]}")
PROMPTS.unlink(missing_ok=True)
ctx = p.run("docs5", pipeline_id=f"stage4-{mode}")
print("\nmodels asked for DURING the run:", [m for m, _ in factory.requested[n_before:]])
calls = [json.loads(l) for l in PROMPTS.open()] if PROMPTS.exists() else []
print("model calls made:", len(calls), [c["reply_used"] for c in calls])
r = [x for x in ctx.stage_results if x.stage_name == "translation"][0]
print("stage result: status =", r.status.value, "| in =", r.input_count, "| out =", r.output_count)
print("stage metrics:", {k: v for k, v in r.metrics.items() if k != "translation_stats"})
if "translation_stats" in r.metrics: print("translation_stats:", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.metrics["translation_stats"].items()})
print("context.text_units:", len(ctx.text_units), "| context.translated_units:", len(ctx.translated_units),
      "| same objects:", bool(ctx.translated_units) and all(a is b for a, b in zip(ctx.text_units, ctx.translated_units)))
for u in ctx.text_units:
    print(f"  {u.attributes['file_name']:<16} text: {short(u.text, 62)}"); print(f"  {'':<16} translated_texts: {short(u.translated_texts, 150)}")
print("cache files:", sorted(str(f.relative_to('cache4')) for f in Path('cache4', f'stage4-{mode}').rglob('*.json')))
```

`reproduce/scripts/lang_format_demo.sh`

```bash
#!/usr/bin/env bash
# How a (str, Enum) value is formatted into a prompt on different Python versions.
# usage: bash lang_format_demo.sh /path/to/unified-kg-rag-on-aws
"$1/.venv/bin/python" - <<'PY'
import sys
from unified_kg_rag.domain.models import LanguageCode
print("repo venv, python", sys.version.split()[0])
print("  LanguageCode.ES.value           ->", repr(LanguageCode.ES.value))
print("  '{x}'.format(x=LanguageCode.ES) ->", repr("{x}".format(x=LanguageCode.ES)))
PY
T='import sys
from enum import Enum
class L(str, Enum):
    ES = "es"
print("stand-alone enum, python", sys.version.split()[0], "->", repr("{x}".format(x=L.ES)))'
for v in 3.10 3.12; do uv run --no-project --python $v python -c "$T" 2>/dev/null | tail -1; done
```

### Appendix H. Self-extraction test

**[RAN]** Every file was extracted from this document by the rules in section 0.5 and compared with the original.

```text
$ python build/extract.py HANDOFF.md extract_test
33 files written
$ diff -r reproduce extract_test/reproduce
(no differences: all 33 files identical, byte for byte)
```
