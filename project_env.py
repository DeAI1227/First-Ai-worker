from __future__ import annotations

import os
from pathlib import Path
from threading import Lock
from typing import Iterable

_LOCK = Lock()
_LOADED = False


def load_project_env(start: Path | None = None, *, override: bool = False) -> Path | None:
    """Load the repository-level .env into the current process once.

    The loader is intentionally lightweight so the project does not depend on an
    extra dotenv package for the MVP. Existing environment variables win unless
    override=True is passed.
    """

    global _LOADED
    with _LOCK:
        if _LOADED and not override:
            return _find_env_file(start or Path(__file__).resolve())

        env_path = _find_env_file(start or Path(__file__).resolve())
        if env_path is None:
            _LOADED = True
            return None

        _apply_env_file(env_path, override=override)
        _LOADED = True
        return env_path


def _find_env_file(start: Path) -> Path | None:
    current = start.resolve()
    search_roots: Iterable[Path] = (current, *current.parents)
    for root in search_roots:
        candidate = root / ".env"
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _apply_env_file(path: Path, *, override: bool) -> None:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_inline_comment(value.strip())
        value = _unquote(value)
        if not key:
            continue
        if override or key not in os.environ or os.environ.get(key, "") == "":
            os.environ[key] = value


def _strip_inline_comment(value: str) -> str:
    if not value:
        return value
    if value.startswith(("'", '"')):
        return value
    if " #" in value:
        return value.split(" #", 1)[0].rstrip()
    return value


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value

