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
