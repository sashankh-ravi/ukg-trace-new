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
