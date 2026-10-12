"""Cache-key names with and without the folder fingerprint (evidence for bug 1).
Usage: python keys_demo.py <folder fingerprint>"""
import logging, sys; logging.disable(logging.CRITICAL)
from unified_kg_rag.shared import get_config
from unified_kg_rag.shared.utils import stage_cache_key
from unified_kg_rag.domain.models import PipelineStageType as T
c = get_config(); fp = sys.argv[1]
for name, t in (("parsing", T.DOCUMENT_PARSING), ("loading", T.DOCUMENT_LOADING)):
    print(f"{name} key, NO folder fingerprint : {stage_cache_key(c, t, 'documents', None)}")
    print(f"{name} key, with {fp}      : {stage_cache_key(c, t, 'documents', fp)}")
