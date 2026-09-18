#!/usr/bin/env python3
"""Measure the structural architecture of chapters — and nothing else.

Point it at text you have the right to analyse: your own drafts, public-domain
works, or material you are licensed to read. It reads the prose, counts
structure, and writes ONLY aggregate numbers to
`inspiration/structure-metrics.json`.

What it records
---------------
Chapter length, paragraph length, dialogue ratio, scene-break count, and a
classification of how each chapter opens and closes. Distributions and medians.

What it never records
---------------------
No prose. No sentences. No names, places, or plot. Nothing that could
reconstruct a line of the source. The output is a table of numbers, which is
what "architecture" actually means.

Usage
-----
  analyze_structure.py --dir drafts/my-novel --label my-draft
  analyze_structure.py --file wholebook.txt --split "^Chapter \\d+" --label draft-2
  analyze_structure.py --report
  analyze_structure.py --compare          # measurements vs engine/genre-priors.json
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from novelkit import store  # noqa: E402

METRICS = store.INSPIRATION / "structure-metrics.json"
PRIORS = store.ENGINE / "genre-priors.json"

QUOTES = '"“”«»'
MOTION_VERBS = set("""
walked ran stepped moved turned opened closed pushed pulled struck threw caught climbed
entered left crossed lifted dropped drew swung rose stood knelt reached grabbed shoved
sprinted lunged ducked spun slammed kicked hurled leapt dove crawled
""".split())
STATE_MARKERS = ["had become", "was now", "no longer", "for the first time", "never again",
                 "from now on", "it was done", "was over"]
HOOK_MARKERS = ["would", "tomorrow", "coming", "waiting", "about to", "before he could",
                "before she could", "then he saw", "then she saw", "too late"]


ARTIFACT = re.compile(r"^\s*[\[\(](illustration|footnote|image|figure|plate|note)\b", re.I)


def is_artifact(p: str) -> bool:
    """Editorial furniture from a scanned or annotated edition: illustration
    captions, footnote markers, plate references. Classifying these as prose
    silently poisons every opening/closing statistic."""
    s = p.strip()
    if ARTIFACT.match(s):
        return True
    if s.startswith("[") and s.endswith("]") and words(s) < 25:
        return True
    if words(s) < 3:
        return True
    return False


def paragraphs(text: str, *, clean: bool = True) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if clean:
        kept = [p for p in parts if not is_artifact(p)]
        parts = kept or parts
    return parts or [text.strip()]


def words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9'’\-]+", text))


def has_dialogue(p: str) -> bool:
    return any(q in p for q in QUOTES)


def classify_opening(p: str) -> str:
    low = p.lower()
    if has_dialogue(p[:240]):
        return "dialogue"
    if set(re.findall(r"[a-z]+", low[:400])) & MOTION_VERBS:
        return "in_motion"
    if re.search(r"\b(had been|there was|there were|it was a)\b", low[:240]):
        return "description"
    if re.search(r"\b(was|were|stood|lay|sat|felt|thought|knew|remembered)\b", low[:240]):
        return "situation"
    return "situation"


def classify_closing(p: str) -> str:
    stripped = p.strip()
    low = stripped.lower()
    sentences = [s for s in re.split(r"(?<=[.!?…])\s+", stripped) if s.strip()]
    last = sentences[-1] if sentences else stripped
    if stripped.endswith("?") or stripped.endswith("…") or stripped.endswith("..."):
        return "hook"
    if any(m in low[-260:] for m in HOOK_MARKERS):
        return "hook"
    if words(last) <= 8 and len(sentences) > 1:
        return "hook"
    if any(m in low[-260:] for m in STATE_MARKERS):
        return "state_change"
    return "quiet"


def scene_breaks(text: str) -> int:
    return len(re.findall(r"^\s*([*#\-–—]\s*){3,}\s*$", text, re.M))


def measure_chapter(text: str) -> dict:
    ps = paragraphs(text)
    w = words(text)
    return {
        "words": w,
        "paragraphs": len(ps),
        "avg_paragraph_words": round(w / max(1, len(ps)), 1),
        "dialogue_ratio": round(sum(1 for p in ps if has_dialogue(p)) / max(1, len(ps)), 3),
        "scene_breaks": scene_breaks(text),
        "opening": classify_opening(ps[0]),
        "closing": classify_closing(ps[-1]),
    }


def summarise(chapters: list[dict]) -> dict:
    if not chapters:
        return {}
    def dist(key):
        counts = {}
        for c in chapters:
            counts[c[key]] = counts.get(c[key], 0) + 1
        return {k: round(v / len(chapters), 3) for k, v in sorted(counts.items(), key=lambda kv: -kv[1])}
    ws = [c["words"] for c in chapters]
    return {
        "chapters_measured": len(chapters),
        "words": {
            "median": int(statistics.median(ws)),
            "mean": int(statistics.mean(ws)),
            "p10": int(statistics.quantiles(ws, n=10)[0]) if len(ws) >= 10 else min(ws),
            "p90": int(statistics.quantiles(ws, n=10)[-1]) if len(ws) >= 10 else max(ws),
        },
        "avg_paragraph_words": round(statistics.median([c["avg_paragraph_words"] for c in chapters]), 1),
        "dialogue_ratio_median": round(statistics.median([c["dialogue_ratio"] for c in chapters]), 3),
        "scene_breaks_median": statistics.median([c["scene_breaks"] for c in chapters]),
        "opening_move_distribution": dist("opening"),
        "closing_move_distribution": dist("closing"),
    }


def load_metrics() -> dict:
    return store.load(METRICS, {"description": "Aggregate structural measurements. Numbers only — no prose is ever stored here.",
                                "sets": {}})


def collect(args) -> list[tuple[str, str]]:
    out = []
    if args.dir:
        d = Path(args.dir)
        files = sorted(p for p in d.rglob("*") if p.suffix.lower() in (".txt", ".md") and p.is_file())
        if not files:
            raise SystemExit(f"no .txt or .md files under {d}")
        for p in files:
            out.append((p.stem, p.read_text(encoding="utf-8", errors="replace")))
    if args.file:
        p = Path(args.file)
        text = p.read_text(encoding="utf-8", errors="replace")
        if args.split:
            parts = re.split(args.split, text, flags=re.M)
            parts = [x for x in parts if words(x) > 200]
            for i, part in enumerate(parts, 1):
                out.append((f"{p.stem}-{i:04d}", part))
        else:
            out.append((p.stem, text))
    return out


def cmd_compare():
    from novelkit import calibrate
    for line in calibrate.report():
        print(line)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", help="directory of chapter files (.txt/.md)")
    ap.add_argument("--file", help="a single file")
    ap.add_argument("--split", help="regex that starts each chapter, for a single-file book")
    ap.add_argument("--label", help="name for this measurement set")
    ap.add_argument("--report", action="store_true", help="print stored measurements")
    ap.add_argument("--compare", action="store_true", help="compare tempo.json against priors and measurements")
    args = ap.parse_args(argv)

    if args.compare:
        return cmd_compare()

    metrics = load_metrics()
    if args.report:
        if not metrics["sets"]:
            print("No measurements stored.")
            return 0
        for label, s in metrics["sets"].items():
            print(f"\n{label}  ({s['measured']}, {s['summary']['chapters_measured']} chapters)")
            for k, v in s["summary"].items():
                print(f"  {k}: {v}")
        return 0

    inputs = collect(args)
    if not inputs:
        ap.print_help()
        return 1
    label = args.label or "unlabelled"
    chapters = [measure_chapter(text) for _, text in inputs]
    summary = summarise(chapters)
    metrics["sets"][label] = {"measured": date.today().isoformat(), "summary": summary,
                              "per_chapter": chapters}
    store.save(METRICS, metrics)
    print(f"Measured {len(chapters)} chapter(s) as '{label}'. Numbers only — no prose stored.\n")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print(f"\nWritten to {store.rel(METRICS)}")
    print("Compare against the engine: tools/analyze_structure.py --compare")
    return 0


if __name__ == "__main__":
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (AttributeError, ValueError):
        pass
    raise SystemExit(main())
