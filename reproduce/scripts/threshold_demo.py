"""Which stages' cache fingerprints change when one late setting changes.
Usage: python threshold_demo.py <folder fingerprint>"""
import logging, sys; logging.disable(logging.CRITICAL)
from unified_kg_rag.domain.models import Config, PipelineStageType as T
from unified_kg_rag.shared.utils.cache_keys import stage_input_fingerprint as fp
a = Config(); b = Config(); corpus = sys.argv[1]
print("similarity_threshold default:", a.processing.similarity_threshold)
b.processing.similarity_threshold = round(a.processing.similarity_threshold - 0.05, 2)
print("changed to:", b.processing.similarity_threshold, "\n")
print(f"{'stage':<22}{'before':<15}{'after':<15}still valid?")
for t in T:
    x, y = fp(a, t, corpus), fp(b, t, corpus)
    print(f"{t.value:<22}{x:<15}{y:<15}{'yes' if x==y else 'NO - redo'}")
