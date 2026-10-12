"""Stand-in model: records every prompt; replies from answers.json (written by hand)."""
import hashlib, json
from pathlib import Path
from typing import Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

PROMPTS = Path("prompts.jsonl"); ANSWERS = Path("answers.json")
PLACEHOLDER = '<?xml version="1.0" encoding="UTF-8"?>\n<chunk_boundaries><single_chunk>true</single_chunk></chunk_boundaries>'

class HandAnsweredModel(BaseChatModel):
    model_id: str = "hand-answered"
    @property
    def _llm_type(self) -> str: return "hand-answered"
    def _generate(self, messages, stop=None, run_manager=None, **kwargs: Any) -> ChatResult:
        parts = [{"role": m.type, "text": m.content if isinstance(m.content, str) else json.dumps(m.content)} for m in messages]
        key = hashlib.sha256(parts[-1]["text"].encode()).hexdigest()[:10]
        answers = json.loads(ANSWERS.read_text()) if ANSWERS.exists() else {}
        reply = answers.get(key); used = "hand-written answer" if reply else "PLACEHOLDER"
        with PROMPTS.open("a") as f:
            f.write(json.dumps({"key": key, "model_id": self.model_id, "messages": parts, "reply_used": used}) + "\n")
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=reply or PLACEHOLDER))])

class HandAnsweredFactory:
    def __init__(self, config): self.config = config; self.requested = []
    def get_model(self, model_id, **kwargs):
        self.requested.append((str(getattr(model_id, "value", model_id)), {k: str(v) for k, v in kwargs.items()}))
        return HandAnsweredModel(model_id=str(getattr(model_id, "value", model_id)))
    def get_model_info(self, model_id): return None
