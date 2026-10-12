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
