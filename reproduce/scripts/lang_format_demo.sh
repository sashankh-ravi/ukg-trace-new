#!/usr/bin/env bash
# How a (str, Enum) value is formatted into a prompt on different Python versions.
# usage: bash lang_format_demo.sh /path/to/unified-kg-rag-on-aws
"$1/.venv/bin/python" - <<'PY'
import sys
from unified_kg_rag.domain.models import LanguageCode
print("repo venv, python", sys.version.split()[0])
print("  LanguageCode.ES.value           ->", repr(LanguageCode.ES.value))
print("  '{x}'.format(x=LanguageCode.ES) ->", repr("{x}".format(x=LanguageCode.ES)))
PY
T='import sys
from enum import Enum
class L(str, Enum):
    ES = "es"
print("stand-alone enum, python", sys.version.split()[0], "->", repr("{x}".format(x=L.ES)))'
for v in 3.10 3.12; do uv run --no-project --python $v python -c "$T" 2>/dev/null | tail -1; done
