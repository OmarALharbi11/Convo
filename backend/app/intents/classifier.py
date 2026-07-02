"""
Hybrid intent classifier — rules engine + optional LLM fallback.

Tier 1: RulesClassifier (always runs — fast, deterministic, free)
Tier 2: LLM parser (optional, runs when rules confidence < threshold)

The hybrid approach means the system works reliably without any paid API
while gaining richer phrase understanding when an OpenAI key is configured.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.intents.models import ClassifiedIntent, Intent
from app.intents.rules_engine import RulesClassifier

# Confidence threshold below which we escalate to LLM
_LLM_THRESHOLD = 0.6


class HybridIntentClassifier:
    def __init__(
        self,
        rules: RulesClassifier,
        llm_parser: Any | None = None,  # LLMIntentParser | None
    ) -> None:
        self._rules = rules
        self._llm = llm_parser
        self._last_debug: dict[str, Any] = {}
        self.supported_intents = [i.value for i in Intent]

    async def classify(self, text: str) -> ClassifiedIntent:
        # Always run rules engine first
        rules_result = self._rules.classify(text)

        self._last_debug = {
            "input": text,
            "rules_intent": rules_result.intent.value,
            "rules_confidence": rules_result.confidence,
            "rules_pattern": rules_result.matched_pattern,
            "llm_used": False,
        }

        # Check if LLM should be consulted
        if (
            self._llm is not None
            and rules_result.confidence < _LLM_THRESHOLD
            and rules_result.intent == Intent.UNKNOWN
        ):
            try:
                llm_result = await self._llm.parse(text)
                if llm_result and llm_result.confidence > rules_result.confidence:
                    self._last_debug["llm_used"] = True
                    self._last_debug["llm_intent"] = llm_result.intent.value
                    self._last_debug["llm_confidence"] = llm_result.confidence
                    return llm_result
            except Exception as exc:
                self._last_debug["llm_error"] = str(exc)

        return rules_result

    def get_last_debug_info(self) -> dict[str, Any]:
        return dict(self._last_debug)


@lru_cache(maxsize=1)
def get_classifier() -> HybridIntentClassifier:
    """Return the singleton classifier instance."""
    from app.core.config import get_settings
    settings = get_settings()

    rules = RulesClassifier()
    llm_parser = None

    if settings.USE_LLM_INTENT and settings.OPENAI_API_KEY:
        try:
            from app.intents.llm_parser import LLMIntentParser  # noqa: PLC0415
            llm_parser = LLMIntentParser(api_key=settings.OPENAI_API_KEY)
        except Exception:
            pass  # LLM unavailable — rules engine is sufficient

    return HybridIntentClassifier(rules=rules, llm_parser=llm_parser)
