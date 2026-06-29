from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_TRAILING_DOTS_AND_SPACES = re.compile(r"[. ]+$")
_RESERVED_WINDOWS_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sanitize_path_segment(value: Any, *, fallback: str = "unknown") -> str:
    text = str(value or "").strip()
    text = _INVALID_FILENAME_CHARS.sub("_", text)
    text = _TRAILING_DOTS_AND_SPACES.sub("", text)
    if not text or not any(ch.isalnum() for ch in text):
        text = fallback
    if text.lower() in _RESERVED_WINDOWS_NAMES:
        text = f"_{text}_"
    return text


def write_json(path: Path, payload: dict[str, Any]) -> str:
    ensure_dir(path.parent)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return str(path)


def next_sequence(directory: Path, prefix: str) -> int:
    ensure_dir(directory)
    return len(list(directory.glob(f"{prefix}_*.json"))) + 1
