"""Stage 5, step 1b: step line by line through create_robust_xml_output_parser and setup_chain,
as they run when the graph extractor is built, then show what the finished reader does with one reply.
Uses Python's line tracer: every executed line of those two functions is printed with its line number,
followed by any local variable that was created or changed by it.
Usage: python stage5_step1b_inside_setup.py   (answers.json with the stage 5 answers must be present)"""
import json, linecache, logging, sys
import boto3
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.adapters.providers import Providers
from unified_kg_rag.adapters.aws import chain_factory as CF
from unified_kg_rag.adapters.ingestion.graph_extractor import GraphExtractor
from fake_llm import HandAnsweredFactory

WATCH = {CF.create_robust_xml_output_parser.__code__, CF.setup_chain.__code__}

def show(v):
    if isinstance(v, (str, int, float, bool, type(None))):
        r = repr(v); return r if len(r) < 90 else r[:87] + "..."
    name = type(v).__name__
    if name == "ResolvedPrompt":
        return f"ResolvedPrompt(system_prompt_template: {len(v.system_prompt_template)} chars, human_prompt_template: {len(v.human_prompt_template)} chars)"
    if name == "ChatPromptTemplate":
        return f"ChatPromptTemplate(messages={[type(m).__name__ for m in v.messages]}, input_variables={sorted(v.input_variables)})"
    if name == "OutputFixingParser":
        return f"OutputFixingParser(parser={type(v.parser).__name__}, max_retries={v.max_retries}, retry_chain=prompt|{type(v.retry_chain.steps[1]).__name__}|...)"
    if name == "RunnableBinding":
        return f"RunnableBinding(bound={' | '.join(type(s).__name__ for s in v.bound.steps)}, config={v.config})"
    if name in ("RunnableSequence",):
        return " | ".join(type(s).__name__ for s in v.steps)
    if hasattr(v, "__name__"): return v.__name__
    return name

def tracer(frame, event, arg):
    if frame.f_code not in WATCH: return None
    seen = {}
    fname = frame.f_code.co_name
    def local(frame, event, arg):
        if event in ("line", "return"):
            for k, v in frame.f_locals.items():
                if k not in seen or seen[k] is not v:
                    seen[k] = v; print(f"{'':10}{k} = {show(v)}")
        if event == "line":
            src = linecache.getline(frame.f_code.co_filename, frame.f_lineno).rstrip()
            print(f"  {fname[:8]}:{frame.f_lineno:<4}{src}")
        elif event == "return":
            print(f"  {fname} RETURNS {show(arg)}\n")
        return local
    print(f"\n>>> ENTER {fname}  ({frame.f_code.co_filename.split('unified_kg_rag/')[1]})")
    return local(frame, "call", arg)

config = get_config()
factory = HandAnsweredFactory(config)
providers = Providers(config, boto3.Session(region_name="us-east-1"), llm_factory=factory)
sys.settrace(tracer)
extractor = GraphExtractor(config, providers=providers)
sys.settrace(None)

print("=" * 70)
print("WHY THE READER IS NEEDED: one chunk through the finished chain, one step at a time")
chain = extractor.graph_extractor.bound
prompt, model, reader = chain.steps
inputs = extractor._prepare_extraction_inputs(
    [type("U", (), {"translated_texts": None, "text": open("docs5/01_acme.txt").read().strip(), "id": "x"})()])[0]
messages = prompt.invoke(inputs)
print("step 1, prompt template -> returns", type(messages).__name__, "with", len(messages.to_messages()), "messages")
raw = model.invoke(messages)
print("step 2, model           -> returns", type(raw).__name__, "; its .content is a", type(raw.content).__name__, "of", len(raw.content), "characters, starting:")
print("    " + raw.content[:160].replace("\n", "\n    "))
parsed = reader.invoke(raw)
print("step 3, reader          -> returns", type(parsed).__name__, "with keys", list(parsed))
print("    parsed['entities']['entity'] is a", type(parsed["entities"]["entity"]).__name__, "of", len(parsed["entities"]["entity"]))
print("    first entity:", json.dumps(parsed["entities"]["entity"][0]))
print("    parsed['relationships']['relationship'][0]:", json.dumps(parsed["relationships"]["relationship"][0]))
