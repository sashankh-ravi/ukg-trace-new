"""Measure overlap between neighbouring chunks: size-only splitter versus the cuts chosen by the model."""
import logging; logging.disable(logging.CRITICAL)
from unified_kg_rag.domain.models import Config
from unified_kg_rag.adapters.ingestion.chunker import SimpleTextChunker
from unified_kg_rag.adapters.aws.token_counter import estimate_token_count
def overlap(a, b):
    for n in range(min(len(a), len(b)), 0, -1):
        if a[-n:] == b[:n]: return n
    return 0
one = open("docs/07_review.txt").read()
text = "\n".join(f"[copy {c}] {l}" for c in range(1, 6) for l in one.rstrip("\n").split("\n"))
cfg = Config(); ch = cfg.processing.chunking
print("settings: fallback_chunk_size =", ch.fallback_chunk_size, "| chunk_overlap =", ch.chunk_overlap, "| min =", ch.min_chunk_size, "| max =", ch.max_chunk_size)
print("input text:", len(text), "characters")
raw = SimpleTextChunker(cfg, show_progress=False).fallback_splitter.split_text(text)
print("\nsize-only splitter (used by the 'simple' chunker and the fallback path):")
for i, c in enumerate(raw): print(f"  piece {i+1}: {len(c)} chars" + (f" | shares its first {overlap(raw[i-1], c)} chars with the end of piece {i}" if i else ""))
print("\nmodel path, the three chunks of 07_review.txt (lines 1-8, 9-16, 17-24):")
ls = one.rstrip("\n").split("\n"); p = ["\n".join(ls[0:8]), "\n".join(ls[8:16]), "\n".join(ls[16:24])]
for i in (1, 2): print(f"  chunk {i+1} shares {overlap(p[i-1], p[i])} chars with the end of chunk {i}")
print("\ntoken estimate for the middle chunk:", estimate_token_count(p[1]), "| its length in characters:", len(p[1]))
