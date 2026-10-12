"""Stage 5, step 3a: inside the batch processor on the normal path (every model call succeeds).
Runs stages 1 to 5 on docs5 with the stand-in model and traces BatchProcessor.execute_with_fallback
line by line, including the helpers defined inside it. The call to the chain itself runs in a worker
thread; the tracer is installed for new threads too (threading.settrace) so those lines show as well.
_prepare_extraction_inputs is not traced again (step 2); only what it returns is shown.
Usage: python stage5_step3a_batch.py   (answers.json with the stage 5 answers must be present)"""
import logging, sys, threading
from pathlib import Path
import boto3
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.domain.models import PipelineConfig, PipelineStageType as T
from unified_kg_rag.adapters.providers import Providers
from unified_kg_rag.application.ingestion.pipeline import DataIngestionPipeline as DIP
from unified_kg_rag.application.ingestion import pipeline_stages as PS
from unified_kg_rag.shared.utils.langchain import BatchProcessor as BP
from fake_llm import HandAnsweredFactory
from linetrace import trace, inner_code, default_describe

def describe(v):
    n = type(v).__name__
    if n == "TextUnit": return f"TextUnit({v.attributes.get('file_name')})"
    if isinstance(v, dict) and "input_text" in v: return f"prompt-input dict for {v['input_text'][:30]!r}..."
    if isinstance(v, dict) and set(v) >= {"entities"}: return f"parsed reply dict, keys {list(v)}"
    if isinstance(v, list) and v and isinstance(v[0], dict) and "input_text" in v[0]: return f"list of {len(v)} prompt-input dicts"
    if isinstance(v, list) and v and isinstance(v[0], dict) and "entities" in v[0]: return f"list of {len(v)} parsed reply dicts (keys {list(v[0])})"
    if isinstance(v, list) and v and type(v[0]).__name__ == "TextUnit": return f"list of {len(v)} TextUnit: {[x.attributes.get('file_name') for x in v]}"
    if isinstance(v, list) and v and isinstance(v[0], tuple) and len(v[0]) == 2 and isinstance(v[0][1], list):
        return f"list of {len(v)} (chunk number, items) pairs: " + str([(a, len(b)) for a, b in v]) + "  <- (number, how many chunks of text)"
    if isinstance(v, dict) and v and all(isinstance(k, int) for k in v): return "{" + ", ".join(f"{k}: {describe(x)}" for k, x in v.items()) + "}"
    if n == "dict" and "max_concurrency" in v:
        return "processing settings: " + str({k: v[k] for k in ("max_concurrency", "batch_size", "chunk_concurrency", "max_attempts")}) + f" + {len(v) - 4} other keys"
    if n == "RunnableConfig" or (isinstance(v, dict) and "max_concurrency" in v): return f"{v}"
    if isinstance(v, dict) and "return_exceptions" in v: return str(v)
    if callable(v) and hasattr(v, "__qualname__"): return f"function {v.__qualname__}"
    return default_describe(v)

EWF = BP.execute_with_fallback
tracer = trace([EWF, inner_code(EWF, "timed_sequential_func"), inner_code(EWF, "process_chunk"),
                inner_code(inner_code(EWF, "process_chunk"), "run_batch"),
                BP._create_batch_func, inner_code(BP._create_batch_func, "_batch_func"),
                BP._batch_kwargs, BP._run_with_timeout, BP._failed_indices], describe)

orig_exec = PS.GraphExtractionStage._execute_core
def exec_traced(self, ctx):
    print("BatchProcessor fields before the call:", {k: getattr(self.extractor.batch_processor, k) for k in
          ("max_concurrency", "batch_size", "chunk_concurrency", "max_attempts", "retry_multiplier", "retry_max_wait", "call_timeout_seconds")})
    sys.settrace(tracer); threading.settrace(tracer)
    try: return orig_exec(self, ctx)
    finally: sys.settrace(None); threading.settrace(None)
PS.GraphExtractionStage._execute_core = exec_traced

config = get_config()
factory = HandAnsweredFactory(config)
providers = Providers(config, boto3.Session(region_name="us-east-1"), llm_factory=factory)
on = (T.DOCUMENT_PARSING, T.DOCUMENT_LOADING, T.TEXT_CHUNKING, T.TRANSLATION, T.GRAPH_EXTRACTION)
pc = PipelineConfig(stages_enabled={t: t in on for t in T}, local_directory=Path("cache5"))
p = DIP(config=config, pipeline_config=pc, source_directory=Path("docs5"), providers=providers)
ctx = p.run("docs5", pipeline_id="stage5-step3a")
r = [x for x in ctx.stage_results if x.stage_name == "graph_extraction"][0]
print("stage 5 status:", r.status.value, "| entities:", len(ctx.entities), "| relationships:", len(ctx.relationships))
