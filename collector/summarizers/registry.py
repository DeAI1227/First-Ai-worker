from __future__ import annotations

from typing import Any

from collector.summarizers.llm_summarizer import summarize_with_llm
from collector.summarizers.mock_summarizer import summarize_with_mock


def summarize_sources(state: dict[str, Any]) -> dict[str, Any]:
    sources = state.get("filtered_sources", [])
    summarizer_mode = str(state.get("summarizer_mode", "mock")).strip().lower() or "mock"

    if summarizer_mode in {"llm", "auto"}:
        summary = summarize_with_llm(state, sources, provider=state.get("llm_provider"))
    else:
        summary = summarize_with_mock(state, sources)

    state.update(summary)
    return state
