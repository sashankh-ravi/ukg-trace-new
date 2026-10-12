"""Stage 5, step 4a: how a model reply is read (the third station of the chain).
Usage: python stage5_step4a_reader.py PART    (answers_stage5.json must be present)
  real      our hand-written reply for 01_acme.txt, read by RobustXMLOutputParser, traced line by line
  cut       the same reply cut off in the middle of the relationships section, read the same way, then
            passed to _parse_extraction_result (needs cache5/stage5-answered from "python stage5.py answered")
  prose     stages 1 to 5 run for real; the reply for 05_investor.txt is a sentence with no tags, so the
            repair ("fixing") model is called. All prompts are recorded; the repair prompt is printed in full.
"""
import json, logging, sys
from pathlib import Path
import boto3
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.adapters.providers import Providers
from unified_kg_rag.shared.utils.langchain import RobustXMLOutputParser as R
from linetrace import trace, default_describe
from fake_llm import HandAnsweredFactory, PROMPTS, ANSWERS

PART = sys.argv[1]
ALL = json.load(open("answers_stage5.json"))
REPLY = ALL["481b2e4f4b"]   # the reply for 01_acme.txt

def describe(v):
    if isinstance(v, (bytes, str)) and len(v) > 100:
        s = v.decode() if isinstance(v, bytes) else v
        return f"{type(v).__name__} of {len(v)} chars: {s[:45]!r}...{s[-30:]!r}"
    if isinstance(v, set): return f"set of {len(v)}: {sorted(v)}"
    if isinstance(v, dict):
        out = {}
        for k, x in v.items():
            if isinstance(x, dict) and len(x) == 1 and isinstance(next(iter(x.values())), list):
                ik = next(iter(x)); out[k] = f"{{'{ik}': list of {len(x[ik])}}}"
            elif isinstance(x, dict): out[k] = f"dict with keys {list(x)}"
            elif isinstance(x, list): out[k] = f"list of {len(x)}"
            else: out[k] = x if not isinstance(x, str) or len(x) < 40 else x[:37] + "..."
        return f"dict {out}"
    if isinstance(v, list) and v and isinstance(v[0], tuple): return f"list of {len(v)} (tag, content) pairs, tags {[t for t, _ in v][:8]}{'...' if len(v) > 8 else ''}"
    return default_describe(v)

tracer = trace([R.parse, R._sections_preserved, R._extract_xml_fallback], describe)

def read(text):
    parser = R()
    sys.settrace(tracer)
    try: out = parser.parse(text)
    finally: sys.settrace(None)
    ents = out.get("entities", {}).get("entity", []) if isinstance(out.get("entities"), dict) else []
    rels = out.get("relationships", {}).get("relationship", []) if isinstance(out.get("relationships"), dict) else []
    print("\nRESULT: top-level keys", list(out), "| entities:", len(ents if isinstance(ents, list) else [ents]),
          "| relationships:", len(rels if isinstance(rels, list) else [rels]))
    return out

if PART == "real":
    print(f"reply: {len(REPLY)} characters, two top-level sections <entities> and <relationships>\n")
    read(REPLY)

elif PART == "cut":
    cut = REPLY[: REPLY.index("<relationship>", REPLY.index("<relationship>") + 1) + 60]
    print(f"reply cut to {len(cut)} of {len(REPLY)} characters; it ends:\n{cut[-160:]}\n")
    out = read(cut)
    rels = out.get("relationships", {}).get("relationship") if isinstance(out.get("relationships"), dict) else None
    print("relationships kept:", json.dumps(rels, indent=1)[:900] if rels else rels)
    # What the extractor's next step does with this dict (step 4b covers that function line by line).
    import glob
    from unified_kg_rag.domain.models import TextUnit
    from unified_kg_rag.adapters.ingestion.graph_extractor import GraphExtractor
    from fake_llm import HandAnsweredFactory
    f = sorted(glob.glob("cache5/stage5-answered/text_chunking/text_units-*.json"))[0]
    data = json.load(open(f)); data = data.get("data", data) if isinstance(data, dict) else data
    unit = TextUnit.model_validate([u for u in data if u["attributes"]["file_name"] == "01_acme.txt"][0])
    config = get_config()
    ex = GraphExtractor(config, providers=Providers(config, boto3.Session(region_name="us-east-1"), llm_factory=HandAnsweredFactory(config)))
    ents, rels = ex._parse_extraction_result(out, unit)
    print("\n_parse_extraction_result on this dict (", f, "):")
    print("  raised an error: no")
    print("  entities:", [e.name for e in ents])
    print("  relationships:", [(r.source_name, r.type, r.target_name) for r in rels])

elif PART == "prose":
    from unified_kg_rag.domain.models import PipelineConfig, PipelineStageType as T
    from unified_kg_rag.application.ingestion.pipeline import DataIngestionPipeline as DIP
    answers = dict(ALL); answers["e5a610dbad"] = "I could not find any entities in this text."   # 05_investor.txt
    ANSWERS.write_text(json.dumps(answers)); PROMPTS.unlink(missing_ok=True)
    print("reply for 05_investor.txt set to:", repr(answers["e5a610dbad"]))
    config = get_config()
    providers = Providers(config, boto3.Session(region_name="us-east-1"), llm_factory=HandAnsweredFactory(config))
    on = (T.DOCUMENT_PARSING, T.DOCUMENT_LOADING, T.TEXT_CHUNKING, T.TRANSLATION, T.GRAPH_EXTRACTION)
    p = DIP(config=config, pipeline_config=PipelineConfig(stages_enabled={t: t in on for t in T}, local_directory=Path("cache5")),
            source_directory=Path("docs5"), providers=providers)
    sys.settrace(None)
    ctx = p.run("docs5", pipeline_id="stage5-step4a-prose")
    calls = [json.loads(l) for l in PROMPTS.open()]
    print(f"\nmodel calls recorded: {len(calls)}")
    for i, c in enumerate(calls, 1):
        last = c["messages"][-1]["text"]
        kind = "EXTRACTION prompt" if "Extract entities and relationships" in last else "OTHER prompt"
        print(f"  call {i}: {kind}, roles {[m['role'] for m in c['messages']]}, reply used: {c['reply_used']}")
    fix = [c for c in calls if "Extract entities and relationships" not in c["messages"][-1]["text"]]
    for c in fix:
        print("\n=== the repair prompt, in full (", len(c["messages"][-1]["text"]), "characters ) ===")
        print(c["messages"][-1]["text"])
        print("=== end ===")
        print("does it contain the chunk's text ('Banyan Capital invested in Acme Robotics in 2019')?",
              "Banyan Capital invested in Acme Robotics in 2019" in c["messages"][-1]["text"])
        print("does it contain the extraction instructions ('Entity Categories')?", "Entity Categories" in c["messages"][-1]["text"])
    r = [x for x in ctx.stage_results if x.stage_name == "graph_extraction"][0]
    unit_file = {u.id: u.attributes["file_name"] for u in ctx.text_units}
    print("\nstage 5:", r.status.value, "| failed_units:", r.metrics.get("failed_units"), "| entities:", len(ctx.entities),
          "| failed chunks:", [unit_file[i] for i in ctx.failed_text_unit_ids.get("graph_extraction", [])])
