"""Paths and persistence. Everything on disk is JSON or Markdown, by design:
the author must be able to edit any of it by hand without the tools present.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BIBLE = ROOT / "bible"
ENGINE = ROOT / "engine"
CHARACTERS = ROOT / "characters"
ENVIRONMENTS = ROOT / "environments"
CONTINUITY = ROOT / "continuity"
INSPIRATION = ROOT / "inspiration"
CHAPTERS = ROOT / "chapters"

TEMPO = ENGINE / "tempo.json"
PROGRESSION = ENGINE / "progression.json"
ARCS = ENGINE / "arcs.json"
STATE = ENGINE / "state.json"
CANON = BIBLE / "canon-locks.json"

CHAR_REGISTRY = CHARACTERS / "registry.json"
ENV_REGISTRY = ENVIRONMENTS / "registry.json"
CHAPTER_INDEX = CONTINUITY / "chapter-index.json"
THREADS = CONTINUITY / "threads.json"
LEXICON = INSPIRATION / "lexicon.json"


def load(path: Path, default=None):
    path = Path(path)
    if not path.exists():
        if default is None:
            raise FileNotFoundError(f"missing required file: {rel(path)}")
        return default
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def save(path: Path, data) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)


def write_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rel(path) -> str:
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", str(text).lower()).strip()
    return re.sub(r"[\s_]+", "-", text) or "unnamed"
