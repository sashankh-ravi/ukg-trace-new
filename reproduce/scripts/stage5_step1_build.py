"""Stage 5, step 1: what is built when the graph extraction stage is constructed.
No chunk is processed and no model is called. Usage: python stage5_step1_build.py"""
import functools, logging
import boto3
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.adapters.providers import Providers
from unified_kg_rag.application.ingestion import pipeline_stages as PS
from unified_kg_rag.adapters.ingestion import graph_extractor as GX
from unified_kg_rag.domain.prompts import GraphExtractionPrompt
from fake_llm import HandAnsweredFactory

def checkpoint(owner, name, label):
    orig = getattr(owner, name)
    @functools.wraps(orig)
    def w(*a, **k):
        shown = {kk: (getattr(v, "__name__", None) or type(v).__name__ if not isinstance(v, (str, int, float, bool, type(None))) else v) for kk, v in k.items()}
        print(f"CHECKPOINT -> {label}  called with {shown}")
        out = orig(*a, **k)
        print(f"           returned: {type(out).__name__}")
        return out
    setattr(owner, name, w)

config = get_config()
gx = config.processing.graph_extraction
print("settings read by the constructor:")
print("  config.processing.ignore_errors             =", config.processing.ignore_errors)
print("  config.fixing.enabled                       =", config.fixing.enabled)
print("  config.fixing.fixing_model_id               =", config.fixing.fixing_model_id)
print("  graph_extraction.extraction_model_id        =", gx.extraction_model_id)
print("  GraphExtractionPrompt.min_output_tokens     =", GraphExtractionPrompt.min_output_tokens)
print("  config.custom_prompts                       =", config.custom_prompts)
print()
factory = HandAnsweredFactory(config)
checkpoint(factory, "get_model", "factory.get_model")
checkpoint(GX, "create_robust_xml_output_parser", "create_robust_xml_output_parser")
checkpoint(GX, "setup_chain", "setup_chain")
providers = Providers(config, boto3.Session(region_name="us-east-1"), llm_factory=factory)

print(">>> GraphExtractionStage(config, providers=providers)")
stage = PS.GraphExtractionStage(config, providers=providers)
x = stage.extractor
print()
print("after construction:")
print("  stage.name                 =", stage.name)
print("  stage.extractor            =", type(x).__name__)
print("  extractor.ignore_errors    =", x.ignore_errors)
print("  extractor.factory          =", type(x.factory).__name__, "(the stand-in; normally the Bedrock factory)")
print("  extractor.batch_processor  =", type(x.batch_processor).__name__)
print("  extractor.stats            =", x.stats)
print("  extractor.graph_extractor  =", type(x.graph_extractor).__name__, "named", repr(x.graph_extractor.config.get("run_name")))
steps = x.graph_extractor.bound.steps
for i, s in enumerate(steps, 1):
    print(f"     step {i}: {type(s).__name__}")
print("  prompt messages            =", [type(m).__name__ for m in steps[0].messages])
print("  prompt variables to fill   =", sorted(steps[0].input_variables))
print("  models asked for           =", factory.requested)
