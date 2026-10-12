"""Feed different model replies into the real chunker and watch, checkpoint by checkpoint, what it does with each."""
import functools, json, logging, sys
from pathlib import Path
import boto3
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.adapters.providers import Providers
from unified_kg_rag.adapters.ingestion import chunker as C
from unified_kg_rag.adapters.ingestion.parser import ParserFactory
from fake_llm import HandAnsweredFactory, PROMPTS, ANSWERS

KEY = "0b6352c8bf"   # hash of the chunking prompt for 07_review.txt with min_chunk_size=900
X = '<?xml version="1.0" encoding="UTF-8"?>\n<chunk_boundaries>\n%s\n</chunk_boundaries>'
CASES = [
 ("1. sensible reply: lines 9 and 17",                X % "<line_number>9</line_number><line_number>17</line_number>"),
 ("2. a line that does not exist: 9 and 99",          X % "<line_number>9</line_number><line_number>99</line_number>"),
 ("3. forbidden or nonsense numbers: 1, 0, -5, 9",    X % "<line_number>1</line_number><line_number>0</line_number><line_number>-5</line_number><line_number>9</line_number>"),
 ("4. words instead of numbers",                      X % "<line_number>nine</line_number><line_number>seventeen</line_number>"),
 ("5. model writes its own text instead of numbers",  X % "<chunk>Acme Robotics was founded on the Moon in 1850.</chunk><chunk>It has two million employees.</chunk>"),
 ("6. model adds invented text AND a line number",    X % "<summary>Acme was founded on the Moon.</summary><line_number>9</line_number>"),
 ("7. not XML at all",                                "Sure! I would cut it after the part about Chennai, around line 9."),
]

def short(v, n=120):
    s = repr(v); return s if len(s) <= n else s[:n-3] + "..."
def checkpoint(cls, name, show_args=False):
    orig = cls.__dict__[name]; static = isinstance(orig, staticmethod); f = orig.__func__ if static else orig
    @functools.wraps(f)
    def w(*a, **k):
        out = f(*a, **k); args = a if static else a[1:]
        print(f"   CHECKPOINT {cls.__name__}.{name}" + (f"({short(args[-1], 70)})" if show_args else "") + f" -> {short(out)}")
        return out
    setattr(cls, name, staticmethod(w) if static else w)

checkpoint(C.IntelligentTextChunker, "_get_boundary_results")
checkpoint(C.LineBasedBoundaryProcessor, "extract_line_numbers", show_args=True)
checkpoint(C.LineBasedBoundaryProcessor, "convert_line_numbers_to_indices")
checkpoint(C.LineBasedBoundaryProcessor, "validate_error_rate")
checkpoint(C.IntelligentTextChunker, "_create_fallback_chunks")
o = C.IntelligentTextChunker._chunk_with_llm_boundaries
def cwb(self, text, response):
    out = o(self, text, response)
    print("   CHECKPOINT IntelligentTextChunker._chunk_with_llm_boundaries ->", "None (reply rejected)" if out is None else f"{len(out)} piece(s), sizes {[len(x) for x in out]}")
    return out
C.IntelligentTextChunker._chunk_with_llm_boundaries = cwb

config = get_config(); config.processing.chunking.min_chunk_size = 900
providers = Providers(config, boto3.Session(region_name="us-east-1"), llm_factory=HandAnsweredFactory(config))
chunker = C.IntelligentTextChunker(config, providers=providers, show_progress=False)
path = Path("docs/07_review.txt"); original = path.read_text()
doc = ParserFactory.create_parser(path, config).parse_file(path, None)
print("settings: min_chunk_size = 900, max_chunk_size = 8000, max_marker_miss_rate =", config.processing.chunking.max_marker_miss_rate)
print("document: 07_review.txt, 24 lines,", len(original), "bytes\n")
for label, reply in CASES:
    print("=" * 100); print("CASE", label); print("   model reply:", short(reply.replace('<?xml version="1.0" encoding="UTF-8"?>\n', ""), 170))
    ANSWERS.write_text(json.dumps({KEY: reply})); PROMPTS.unlink(missing_ok=True)
    units = chunker._chunk_single_document(doc)
    calls = [json.loads(l) for l in PROMPTS.open()]
    print(f"   model calls made: {len(calls)}  " + str([(c['model_id'].split('.')[-1], c['reply_used']) for c in calls]))
    print("   RESULT:", [(u.attributes["chunking_method"], len(u.text)) for u in units])
    print("   every chunk is an exact piece of the original file:", all(u.text in original for u in units),
          "| any invented words in a chunk:", any(("Moon" in u.text or "million" in u.text) for u in units))
