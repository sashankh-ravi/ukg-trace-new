"""Stage 5 (graph extraction) with checkpoints.  Usage: python stage5.py <run name>

Runs stages 1 to 5 on the folder docs5 with the stand-in model (fake_llm.py).
Replies come from answers.json if present, otherwise the stand-in's placeholder.
Settings can be changed with environment variables, for the experiments:
  GROUNDING=on        switch on the hallucination guard (off by default)
  THRESHOLD=0.7       entity confidence threshold (0.0 by default)
"""
import functools, json, logging, os, sys
from pathlib import Path
import boto3
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.domain.models import PipelineConfig, PipelineStageType as T
from unified_kg_rag.adapters.providers import Providers
from unified_kg_rag.application.ingestion.pipeline import DataIngestionPipeline as DIP
from unified_kg_rag.application.ingestion import pipeline_stages as PS
from unified_kg_rag.adapters.ingestion import graph_extractor as GX
from fake_llm import HandAnsweredFactory, PROMPTS

run = sys.argv[1]
def short(v, n=110):
    s = repr(v); return s if len(s) <= n else s[:n-3] + "..."
def checkpoint(cls, name, show=lambda out, a: out):
    orig = getattr(cls, name)
    @functools.wraps(orig)
    def w(self, *a, **k):
        print(f"CHECKPOINT -> {cls.__name__}.{name}")
        out = orig(self, *a, **k); print(f"           returned: {short(show(out, a))}"); return out
    setattr(cls, name, w)

config = get_config()
gx = config.processing.graph_extraction
if os.environ.get("GROUNDING") == "on": gx.entity_grounding.enabled = True
if os.environ.get("THRESHOLD"): gx.entity_confidence_threshold = float(os.environ["THRESHOLD"])
print(f"settings: max_entities_per_chunk={gx.max_entities_per_chunk} | max_relationships_per_chunk={gx.max_relationships_per_chunk}"
      f" | entity_confidence_threshold={gx.entity_confidence_threshold} | grounding enabled={gx.entity_grounding.enabled}"
      f" action={gx.entity_grounding.action} | ignore_errors={config.processing.ignore_errors}")
factory = HandAnsweredFactory(config)
providers = Providers(config, boto3.Session(region_name="us-east-1"), llm_factory=factory)
on = (T.DOCUMENT_PARSING, T.DOCUMENT_LOADING, T.TEXT_CHUNKING, T.TRANSLATION, T.GRAPH_EXTRACTION)
pc = PipelineConfig(stages_enabled={t: t in on for t in T}, local_directory=Path("cache5"))
p = DIP(config=config, pipeline_config=pc, source_directory=Path("docs5"), providers=providers)
print("stages built:", [s.name for s in p.stages])

n = lambda out, a: f"{len(out)} items"
checkpoint(PS.GraphExtractionStage, "_execute_core")
checkpoint(GX.GraphExtractor, "extract_from_text_units", lambda out, a: f"{len(out[0])} entities, {len(out[1])} relationships")
checkpoint(GX.GraphExtractor, "_prepare_extraction_inputs", lambda out, a: f"{len(out)} prompt inputs, keys {sorted(out[0])}")
checkpoint(GX.GraphExtractor, "_process_extraction_results", lambda out, a: f"{len(out[0])} entities, {len(out[1])} relationships")
checkpoint(GX.GraphExtractor, "_parse_extraction_result", lambda out, a: f"chunk {a[1].attributes.get('file_name')}: {len(out[0])} entities, {len(out[1])} relationships")
checkpoint(GX.GraphExtractor, "_merge_entities", lambda out, a: f"{len(a[0])} in -> {len(out)} out")
checkpoint(GX.GraphExtractor, "_merge_relationships", lambda out, a: f"{len(a[0])} in -> {len(out)} out")
checkpoint(GX.GraphExtractor, "_materialize_relationship_endpoints", lambda out, a: f"{len(a[0])} in -> {len(out)} out")
checkpoint(GX.GraphExtractor, "_filter_entities_by_confidence", lambda out, a: f"{len(out[0])} kept, {out[1]} removed")

PROMPTS.unlink(missing_ok=True)
ctx = p.run("docs5", pipeline_id=f"stage5-{run}")
calls = [json.loads(l) for l in PROMPTS.open()] if PROMPTS.exists() else []
print("\nmodel calls made:", len(calls), [c["reply_used"] for c in calls])
r = [x for x in ctx.stage_results if x.stage_name == "graph_extraction"][0]
print("stage result: status =", r.status.value, "| in =", r.input_count, "| out =", r.output_count)
if r.error_message: print("stage error_message:", r.error_message)
print("stages run:", [(x.stage_name, x.status.value) for x in ctx.stage_results])
print("stage metrics:", {k: v for k, v in r.metrics.items() if k != "extraction_stats"})
print("extraction_stats:", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in (r.metrics.get("extraction_stats") or {}).items() if k != "total_processing_time"})
print("failed_text_unit_ids:", ctx.failed_text_unit_ids.get("graph_extraction"))
unit_file = {u.id: u.attributes["file_name"] for u in ctx.text_units}
print(f"\nENTITIES ({len(ctx.entities)})")
for e in ctx.entities:
    print(f"  {e.name:<26} type={e.type:<13} conf={e.confidence} freq={e.frequency} from={sorted(unit_file.get(i, i[:8]) for i in e.text_unit_ids)}")
    if e.description: print(f"  {'':<26} description: {short(e.description, 120)}")
print(f"\nRELATIONSHIPS ({len(ctx.relationships)})")
for x in ctx.relationships:
    print(f"  {x.source_name} --{x.type}--> {x.target_name}  weight={x.weight} from={sorted(unit_file.get(i, i[:8]) for i in x.text_unit_ids)}")
print("\ncache files:", sorted(str(f.relative_to('cache5')) for f in Path('cache5', f'stage5-{run}').rglob('*.json')))
