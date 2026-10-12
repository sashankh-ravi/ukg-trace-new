"""Stage 5, step 3b: the batch processor's failure paths. Usage: python stage5_step3b_failures.py MODE

Only the chunk from 05_investor.txt misbehaves; the other four get their normal hand-written answers.
  throttle-once    AWS-style ThrottlingException on the first call for that chunk, then a normal reply
  denied-always    AWS-style AccessDeniedException on every call for that chunk
  throttle-always  AWS-style ThrottlingException on every call for that chunk
  (set IGNORE_ERRORS=on to switch processing.ignore_errors on)
  hang-once        the first call for that chunk sleeps 4 s; the group time limit is set to 2 s

Changes made by THIS SCRIPT (not by the repo), so the runs finish quickly:
  batch_processor.retry_multiplier = 1.0, retry_max_wait = 2   (repo: 30.0 and 120 seconds)
  hang-once only: batch_processor.call_timeout_seconds = 2     (repo: 300 seconds)
These are fields of the BatchProcessor object; the config file cannot set them (step 3a).
"""
import collections, json, logging, sys, threading, time
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.domain.models import PipelineConfig, PipelineStageType as T
from unified_kg_rag.adapters.providers import Providers
from unified_kg_rag.application.ingestion.pipeline import DataIngestionPipeline as DIP
from unified_kg_rag.application.ingestion import pipeline_stages as PS
from unified_kg_rag.shared.utils.langchain import BatchProcessor as BP, BATCH_ITEM_FAILED
import fake_llm
from fake_llm import HandAnsweredFactory, HandAnsweredModel, PROMPTS
from linetrace import trace, inner_code, default_describe

MODE = sys.argv[1]
CALLS = collections.Counter(); LOCK = threading.Lock()
EVENTS = []   # (seconds since start, what happened), printed at the end

class TroubledModel(HandAnsweredModel):
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        text = messages[-1].content
        if "Banyan Capital invested" in text:
            with LOCK: CALLS["05"] += 1; n = CALLS["05"]
            EVENTS.append((round(time.monotonic() - T0, 2), f"model called for chunk 05, call #{n}"))
            if MODE == "throttle-once" and n == 1 or MODE == "throttle-always":
                raise ClientError({"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}}, "Converse")
            if MODE == "denied-always":
                raise ClientError({"Error": {"Code": "AccessDeniedException", "Message": "not allowed"}}, "Converse")
            if MODE == "hang-once" and n == 1:
                time.sleep(4)
                EVENTS.append((round(time.monotonic() - T0, 2), "chunk 05 call #1 finally finished sleeping (in the abandoned thread)"))
        else:
            with LOCK: CALLS["others"] += 1
        return super()._generate(messages, stop, run_manager, **kwargs)

class TroubledFactory(HandAnsweredFactory):
    def get_model(self, model_id, **kwargs):
        return TroubledModel(model_id=str(getattr(model_id, "value", model_id)))

def describe(v):
    n = type(v).__name__
    if v is BATCH_ITEM_FAILED: return "BATCH_ITEM_FAILED"
    if isinstance(v, BaseException): return f"{n}: {str(v)[:70]}"
    if n == "TextUnit": return f"TextUnit({v.attributes.get('file_name')})"
    if isinstance(v, dict) and "input_text" in v: return f"prompt-input for {v['input_text'][:22]!r}..."
    if isinstance(v, dict) and "entities" in v: return "parsed reply dict"
    if isinstance(v, list) and v and all(isinstance(x, dict) and "input_text" in x for x in v): return f"list of {len(v)} prompt-inputs"
    if isinstance(v, list) and v and type(v[0]).__name__ == "TextUnit": return f"list of {len(v)} TextUnit"
    if isinstance(v, list): return "[" + ", ".join(describe(x) for x in v) + "]"
    if isinstance(v, dict) and v and all(isinstance(k, int) for k in v): return "{" + ", ".join(f"{k}: {describe(x)}" for k, x in v.items()) + "}"
    if callable(v) and hasattr(v, "__qualname__"): return f"function {v.__qualname__.split('.')[-1]}"
    return default_describe(v)

EWF = BP.execute_with_fallback
tracer = trace([inner_code(EWF, "process_chunk"), inner_code(EWF, "timed_sequential_func"),
                BP._failed_indices, BP._log_partial_failure, BP._process_sequentially_with_fallback,
                BP._splice_retried, BP._is_retryable, inner_code(BP._create_retry_log_callback, "log_retry")], describe)

orig_exec = PS.GraphExtractionStage._execute_core
def exec_traced(self, ctx):
    bp = self.extractor.batch_processor
    bp.retry_multiplier, bp.retry_max_wait = 1.0, 2
    if MODE == "hang-once": bp.call_timeout_seconds = 2
    print("batch processor timing used for this run:", {k: getattr(bp, k) for k in ("retry_multiplier", "retry_max_wait", "call_timeout_seconds", "max_attempts")})
    sys.settrace(tracer); threading.settrace(tracer)
    try: return orig_exec(self, ctx)
    finally: sys.settrace(None); threading.settrace(None)
PS.GraphExtractionStage._execute_core = exec_traced

config = get_config()
import os
if os.environ.get("IGNORE_ERRORS") == "on": config.processing.ignore_errors = True
print("config.processing.ignore_errors =", config.processing.ignore_errors)
factory = TroubledFactory(config)
providers = Providers(config, boto3.Session(region_name="us-east-1"), llm_factory=factory)
on = (T.DOCUMENT_PARSING, T.DOCUMENT_LOADING, T.TEXT_CHUNKING, T.TRANSLATION, T.GRAPH_EXTRACTION)
pc = PipelineConfig(stages_enabled={t: t in on for t in T}, local_directory=Path("cache5"))
p = DIP(config=config, pipeline_config=pc, source_directory=Path("docs5"), providers=providers)
T0 = time.monotonic()
ctx = p.run("docs5", pipeline_id=f"stage5-step3b-{MODE}")
time.sleep(5 if MODE == "hang-once" else 0)   # let an abandoned call finish, so it is counted
print("\n========== SUMMARY ==========")
print("model calls for chunk 05:", CALLS["05"], "| model calls for the other four chunks:", CALLS["others"])
for t, e in EVENTS: print(f"  t={t:>5}s  {e}")
r = [x for x in ctx.stage_results if x.stage_name == "graph_extraction"][0]
print("stage 5 status:", r.status.value, "| failed_units:", r.metrics.get("failed_units"),
      "| entities:", len(ctx.entities), "| relationships:", len(ctx.relationships))
unit_file = {u.id: u.attributes["file_name"] for u in ctx.text_units}
print("failed chunks:", [unit_file[i] for i in ctx.failed_text_unit_ids.get("graph_extraction", [])])
