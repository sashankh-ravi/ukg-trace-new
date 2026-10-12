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
