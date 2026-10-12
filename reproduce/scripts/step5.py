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
