"""Stage 5, step 2: from the start of the stage up to the moment the chunks are handed to the batch
processor. Runs stages 1 to 5 on docs5 with the stand-in model. Line tracing is switched on when the
stage 5 work starts and switched off at the hand-over (step 3 onward runs untraced). Afterwards the
prompt filled in for the first chunk is printed in full.
Usage: python stage5_step2_inputs.py   (answers.json with the stage 5 answers should be present)"""
import logging, sys
from pathlib import Path
import boto3
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.domain.models import PipelineConfig, PipelineStageType as T
from unified_kg_rag.domain.ingestion.base_processor import BaseProcessor
from unified_kg_rag.adapters.providers import Providers
from unified_kg_rag.application.ingestion.pipeline import DataIngestionPipeline as DIP
from unified_kg_rag.application.ingestion import pipeline_stages as PS
from unified_kg_rag.adapters.ingestion.graph_extractor import GraphExtractor
from unified_kg_rag.shared.utils.langchain import BatchProcessor
from fake_llm import HandAnsweredFactory
from linetrace import trace, default_describe

def describe(v):
    n = type(v).__name__
    if n == "TextUnit":
        return f"TextUnit(id={v.id[:8]}.., file={v.attributes.get('file_name')}, text={v.text[:40]!r}..., translated_texts={v.translated_texts})"
    if n == "PipelineContext":
        return f"PipelineContext(text_units: {len(v.text_units)}, translated_units: {len(v.translated_units)}, entities: {len(v.entities)})"
    if n == "GraphExtractionConfig":
        return f"GraphExtractionConfig(max_entities_per_chunk={v.max_entities_per_chunk}, max_relationships_per_chunk={v.max_relationships_per_chunk}, entity_types: {len(v.entity_types)} items, ...)"
    if n == "ExtractionStats":
        return f"ExtractionStats(num_total_units={v.num_total_units}, other counters all 0)"
    if isinstance(v, dict) and "input_text" in v:
        return "{" + ", ".join(f"{k}: {default_describe(x)}" for k, x in v.items()) + "}"
    if isinstance(v, list) and v and isinstance(v[0], dict) and "input_text" in v[0]:
        return f"list of {len(v)} prompt-input dicts"
    if isinstance(v, list) and v and type(v[0]).__name__ == "TextUnit":
        return f"list of {len(v)} TextUnit"
    if isinstance(v, float) and v > 1e9:
        return f"{v:.3f} (clock time, seconds)"
    return default_describe(v)

tracer = trace([PS.GraphExtractionStage._execute_core, GraphExtractor.extract_from_text_units,
                GraphExtractor._prepare_extraction_inputs, GraphExtractor._format_entity_types,
                BaseProcessor.get_text_for_processing], describe)

orig_exec = PS.GraphExtractionStage._execute_core
def exec_traced(self, ctx):
    sys.settrace(tracer)
    try: return orig_exec(self, ctx)
    finally: sys.settrace(None)
PS.GraphExtractionStage._execute_core = exec_traced

orig_batch = BatchProcessor.execute_with_fallback
def handover(self, **k):
    sys.settrace(None)     # step 2 ends here
    print("\n  ========== HAND-OVER TO THE BATCH PROCESSOR: step 3 starts here; tracing stops ==========")
    for key, val in k.items():
        shown = getattr(val, "__qualname__", None) or describe(val)
        if key == "run_config": shown = f"dict with {len(val)} keys"
        print(f"      {key} = {shown}")
    return orig_batch(self, **k)
BatchProcessor.execute_with_fallback = handover

config = get_config()
factory = HandAnsweredFactory(config)
providers = Providers(config, boto3.Session(region_name="us-east-1"), llm_factory=factory)
on = (T.DOCUMENT_PARSING, T.DOCUMENT_LOADING, T.TEXT_CHUNKING, T.TRANSLATION, T.GRAPH_EXTRACTION)
pc = PipelineConfig(stages_enabled={t: t in on for t in T}, local_directory=Path("cache5"))
p = DIP(config=config, pipeline_config=pc, source_directory=Path("docs5"), providers=providers)
ctx = p.run("docs5", pipeline_id="stage5-step2")
print("\n(stage 5 finished untraced; status:", [r.status.value for r in ctx.stage_results if r.stage_name == "graph_extraction"][0], ")")

ex = [s for s in p.stages if s.name == "graph_extraction"][0].extractor
print("\n" + "=" * 70)
print("_prepare_extraction_inputs, traced on its own with the same 5 chunks.")
print("(In the run it is not called by extract_from_text_units; it is passed to the batch processor, which calls it: step 3.)")
sys.settrace(tracer)
prepared = ex._prepare_extraction_inputs(ctx.text_units)
sys.settrace(None)
print("\n" + "=" * 70)
print("THE PROMPT AS FILLED IN FOR THE FIRST CHUNK")
unit = ctx.text_units[0]
inputs = ex._prepare_extraction_inputs([unit])[0]
msgs = ex.graph_extractor.bound.steps[0].invoke(inputs).to_messages()
sysmsg, human = msgs[0].content, msgs[1].content
a = sysmsg.index("## Entity Categories"); b = sysmsg.index("## Entity Naming")
print(f"--- system message: {len(sysmsg)} characters; the part where {{entity_types}} was filled in:")
print(sysmsg[a:b].rstrip())
print(f"--- human message: {len(human)} characters, in full:")
print(human)
