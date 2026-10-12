"""What happens to a long piece of text when the model's reply contains no usable line numbers."""
import json, logging, hashlib
from pathlib import Path
import boto3
logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.adapters.providers import Providers
from unified_kg_rag.adapters.ingestion import chunker as C
from unified_kg_rag.adapters.ingestion.parser import ParserFactory
from fake_llm import HandAnsweredFactory, PROMPTS, ANSWERS

one = Path("docs/07_review.txt").read_text().rstrip("\n").split("\n")
long_text = "\n".join(f"[copy {c}] {l}" for c in range(1, 9) for l in one) + "\n"   # 8 copies, no headings
Path("longdoc").mkdir(exist_ok=True); p = Path("longdoc/08_long.txt"); p.write_text(long_text)
config = get_config(); ch = config.processing.chunking
print(f"settings (defaults): min_chunk_size={ch.min_chunk_size}, max_chunk_size={ch.max_chunk_size}, pre_chunk_size={ch.pre_chunk_size}")
print("document: 08_long.txt,", len(long_text), "characters, no headings\n")
providers = Providers(config, boto3.Session(region_name="us-east-1"), llm_factory=HandAnsweredFactory(config))
chunker = C.IntelligentTextChunker(config, providers=providers, show_progress=False)
doc = ParserFactory.create_parser(p, config).parse_file(p, None)
X = '<?xml version="1.0" encoding="UTF-8"?>\n<chunk_boundaries>%s</chunk_boundaries>'
REPLIES = [("model says keep as one chunk", X % "<single_chunk>true</single_chunk>"),
           ("model writes words instead of numbers", X % "<line_number>forty</line_number><line_number>ninety</line_number>"),
           ("model gives usable numbers (lines 49, 97, 145)", X % "<line_number>49</line_number><line_number>97</line_number><line_number>145</line_number>")]
ANSWERS.unlink(missing_ok=True); PROMPTS.unlink(missing_ok=True)
chunker._chunk_single_document(doc)                       # capture pass, to learn the prompt's key
key = json.loads(PROMPTS.open().readline())["key"]
for label, reply in REPLIES:
    ANSWERS.write_text(json.dumps({key: reply})); PROMPTS.unlink(missing_ok=True)
    chunker.stats = C.ChunkingStats()
    units = chunker._chunk_single_document(doc)
    sizes = [len(u.text) for u in units]
    print(f"REPLY: {label}")
    print(f"   chunks: {[(u.attributes['chunking_method'], len(u.text)) for u in units]}")
    print(f"   largest chunk: {max(sizes)} characters | over max_chunk_size ({ch.max_chunk_size}): {max(sizes) > ch.max_chunk_size}")
    print(f"   stats: llm_processing_failures={chunker.stats.llm_processing_failures}, fallback_chunks_used={chunker.stats.fallback_chunks_used}")
    print(f"   quality check: {chunker.quality_validator.validate_chunks([u.text for u in units])['issues']}\n")
