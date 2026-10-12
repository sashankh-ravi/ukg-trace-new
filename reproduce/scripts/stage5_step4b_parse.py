"""Stage 5, step 4b: _parse_extraction_result turns one parsed reply (a dict) into Entity and Relationship
objects. Usage: python stage5_step4b_parse.py PART
  main          the function itself on chunk 01_acme.txt, line by line (the per-item helpers run untraced)
  entity        parse_entity_data and every helper it calls, for the first entity of that reply
  relationship  parse_relationship_data and every helper it calls, for the first relationship of that reply
  edge          parse_entity_data on edited copies of the first entity: a type not in the allowed list, and
                several ways of writing the confidence
Needs answers_stage5.json, and cache5/stage5-answered (from "python stage5.py answered") for the chunk.
"""
import glob, json, logging, sys
import boto3
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.shared.utils import common as C
from unified_kg_rag.shared.utils.langchain import RobustXMLOutputParser
from unified_kg_rag.adapters.providers import Providers
from unified_kg_rag.adapters.ingestion.graph_extractor import GraphExtractor as GX
from unified_kg_rag.domain.ingestion import base_processor as BPm
from unified_kg_rag.domain.ingestion.base_processor import BaseProcessor as B
from unified_kg_rag.domain.models import TextUnit
from fake_llm import HandAnsweredFactory
from linetrace import trace, default_describe

PART = sys.argv[1]
reply = json.load(open("answers_stage5.json"))["481b2e4f4b"]       # 01_acme.txt
parsed = RobustXMLOutputParser().parse(reply)
f = sorted(glob.glob("cache5/stage5-answered/text_chunking/text_units-*.json"))[0]
units = json.load(open(f)); units = units.get("data", units) if isinstance(units, dict) else units
unit = TextUnit.model_validate([u for u in units if u["attributes"]["file_name"] == "01_acme.txt"][0])
config = get_config()
ex = GX(config, providers=Providers(config, boto3.Session(region_name="us-east-1"), llm_factory=HandAnsweredFactory(config)))

def describe(v):
    n = type(v).__name__
    if n == "TextUnit": return f"TextUnit(01_acme.txt, id {v.id[:8]}.., attributes keys {list(v.attributes or {})})"
    if n == "Entity": return f"Entity(name={v.name!r}, type={v.type!r}, confidence={v.confidence}, id={v.id[:8]}..)"
    if n == "Relationship": return f"Relationship({v.source_name!r} -{v.type}-> {v.target_name!r}, weight={v.weight}, id={v.id[:8]}..)"
    if n == "GraphExtractionConfig": return "GraphExtractionConfig"
    if n == "EntityGroundingConfig": return f"EntityGroundingConfig(enabled={v.enabled}, action={v.action!r})"
    if isinstance(v, list) and v and type(v[0]).__name__ in ("Entity", "Relationship"):
        return f"list of {len(v)}: " + ", ".join(repr(getattr(x, 'name', None) or f'{x.source_name}->{x.target_name}') for x in v)
    if isinstance(v, list) and v and isinstance(v[0], dict): return f"list of {len(v)} dicts, first: {json.dumps(v[0])[:90]}..."
    if isinstance(v, dict) and v and all(isinstance(x, str) for x in v.values()) and len(json.dumps(v)) < 200: return json.dumps(v)
    if isinstance(v, dict) and set(v) == {"entities", "relationships"}: return "dict with keys ['entities', 'relationships'] (the parsed reply)"
    if isinstance(v, dict) and len(v) <= 6 and all(isinstance(x, str) and len(x) <= 8 for x in v): return json.dumps(v)
    if isinstance(v, dict) and set(v) <= {"entity", "relationship"}: return f"dict {{'{next(iter(v))}': list of {len(next(iter(v.values())))}}}"
    if n == "Pattern": return f"pattern {v.pattern!r}"
    if n == "datetime": return "datetime (now)"
    return default_describe(v)

if PART == "main":
    funcs = [GX._parse_extraction_result, GX._apply_entity_grounding, GX._drop_relationships_to_dropped_entities,
             GX._apply_relationship_grounding, B.build_entity_key_index, C.ensure_list]
    print("input: the parsed reply for 01_acme.txt;", len(parsed["entities"]["entity"]), "entities,", len(parsed["relationships"]["relationship"]), "relationships\n")
elif PART == "entity":
    funcs = [B.parse_entity_data, BPm.coerce_llm_text, C.clean_display_name, C.entity_key, B._generate_entity_id,
             C.generate_stable_id, B._parse_attributes, B._parse_confidence]
    item = parsed["entities"]["entity"][0]
    print("input:", json.dumps(item, indent=1), "\n")
elif PART == "relationship":
    funcs = [B.parse_relationship_data, BPm.coerce_llm_text, C.clean_display_name, C.entity_key, B._generate_entity_id,
             B._generate_relationship_id, C.generate_stable_id, B._parse_attributes, B._parse_weight]
    item = parsed["relationships"]["relationship"][0]
    index = {C.entity_key(e["name"]): B._generate_entity_id(C.clean_display_name(e["name"])) for e in parsed["entities"]["entity"]}
    print("input:", json.dumps(item, indent=1))
    print("entity_name_to_id (built from this chunk's 5 entities):", {k: v[:8] + ".." for k, v in index.items()}, "\n")

if PART == "edge":
    base = parsed["entities"]["entity"][0]
    print("allowed types in the prompt:", [x.split(":")[0] for x in config.processing.graph_extraction.entity_types])
    for change in [{"type": "COMPANY"}, {"confidence": "10"}, {"confidence": "9"}, {"confidence": "1"}, {"confidence": "1.0"},
                   {"confidence": "0.3"}, {"confidence": "85"}, {"confidence": "high"}, {"confidence": None}]:
        item = dict(base); item.update(change)
        e = ex.parse_entity_data(item, unit)
        print(f"  input {json.dumps(change):<22} -> type={e.type!r:<16} confidence={e.confidence}")
    sys.exit(0)

tracer = trace(funcs, describe)
sys.settrace(tracer)
try:
    if PART == "main": out = ex._parse_extraction_result(parsed, unit)
    elif PART == "entity": out = ex.parse_entity_data(item, unit)
    else: out = ex.parse_relationship_data(item, unit, index)
finally:
    sys.settrace(None)

print("=" * 60)
if PART == "main":
    ents, rels = out
    print(f"RESULT: {len(ents)} entities, {len(rels)} relationships")
    for e in ents: print(f"  {e.name!r:<20} type={e.type!r:<15} confidence={e.confidence}  attributes={e.attributes}")
    for r in rels: print(f"  {r.source_name!r} -{r.type}-> {r.target_name!r}  weight={r.weight}  attributes={r.attributes}")
else:
    d = out.model_dump()
    print("RESULT:", type(out).__name__)
    for k, v in d.items():
        if k in ("created_at", "updated_at"): v = "(time of the run)"
        print(f"  {k:<22}= {v!r}"[:150])
