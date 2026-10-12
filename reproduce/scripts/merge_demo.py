"""Call the chunker's merge function directly on the three pieces of 07_review.txt.
Usage: python merge_demo.py <path to 07_review.txt>"""
import logging, sys; logging.disable(logging.CRITICAL)
from unified_kg_rag.adapters.ingestion.chunker import ChunkProcessor
text = open(sys.argv[1]).read().rstrip("\n")
lines = text.split("\n")
pieces = ["\n".join(lines[0:8]), "\n".join(lines[8:16]), "\n".join(lines[16:24])]
print("three pieces (lines 1-8, 9-16, 17-24), sizes:", [len(p) for p in pieces])
merged = ChunkProcessor(1000, 8000).merge_small_chunks(list(pieces))
print("after merge_small_chunks (min 1000, max 8000):", [len(m) for m in merged])
i = merged[0].index("The engineering team")
print("text at the first join:", repr(merged[0][i-28:i+24]))
