from __future__ import annotations

from collector.constants import PROHIBITED_TERMS


def clamp_text(text: str, max_chars: int = 500) -> str:
    normalized = " ".join((text or "").split())
    return normalized[:max_chars]


def contains_prohibited_terms(value: object) -> list[str]:
    text = str(value)
    return [term for term in PROHIBITED_TERMS if term in text]
