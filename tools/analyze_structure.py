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
import html
import re
import statistics
import sys
import zipfile
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


def measure_chapter(text: str, boiler: dict | None = None) -> dict:
    ps = paragraphs(text)
    if boiler:
        ps = strip_boilerplate(ps, boiler)
    w = sum(words(p) for p in ps)
    return {
        "words": w,
        "paragraphs": len(ps),
        "avg_paragraph_words": round(w / max(1, len(ps)), 1),
        "dialogue_ratio": round(sum(1 for p in ps if has_dialogue(p)) / max(1, len(ps)), 3),
        "scene_breaks": scene_breaks(text),
        "opening": classify_opening(ps[0]),
        "closing": classify_closing(ps[-1]),
    }


def trend(chapters: list[dict], buckets: int = 10) -> list[dict]:
    """How the architecture drifts across a long run. The interesting question
    for a 3,000-chapter serial is not its average but its slope."""
    if len(chapters) < buckets * 2:
        return []
    size = len(chapters) // buckets
    rows = []
    for i in range(buckets):
        chunk = chapters[i * size:(i + 1) * size] if i < buckets - 1 else chapters[i * size:]
        if not chunk:
            continue
        closings = {}
        for c in chunk:
            closings[c["closing"]] = closings.get(c["closing"], 0) + 1
        rows.append({
            "decile": i + 1,
            "chapters": f"{i * size + 1}-{i * size + len(chunk)}",
            "median_words": int(statistics.median([c["words"] for c in chunk])),
            "dialogue_ratio": round(statistics.median([c["dialogue_ratio"] for c in chunk]), 3),
            "hook_share": round(closings.get("hook", 0) / len(chunk), 3),
        })
    return rows


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
        "trend_by_decile": trend(chapters),
    }


# ---------------------------------------------------------------------------
# EPUB reading. Text is extracted in memory, measured, and discarded — nothing
# is written to disk except the numbers.
# ---------------------------------------------------------------------------

BLOCK_END = re.compile(r"</(p|div|h[1-6]|li|br)\s*>", re.I)
TAG = re.compile(r"<[^>]+>")
DROP = re.compile(r"<(script|style)\b.*?</\1>", re.I | re.S)


def xhtml_to_text(raw: str) -> str:
    raw = DROP.sub(" ", raw)
    raw = BLOCK_END.sub("\n\n", raw)
    raw = TAG.sub("", raw)
    text = html.unescape(raw)
    text = re.sub(r"[ \t\xa0]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def epub_documents(path: Path) -> list[tuple[str, str]]:
    """Spine-ordered (name, text) pairs. Falls back to sorted filenames when the
    OPF cannot be parsed."""
    out = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        opf = next((n for n in names if n.lower().endswith(".opf")), None)
        order = []
        if opf:
            try:
                meta = z.read(opf).decode("utf-8", "replace")
                ids = dict(re.findall(r'<item\b[^>]*id="([^"]+)"[^>]*href="([^"]+)"', meta))
                ids.update({i: h for h, i in re.findall(r'<item\b[^>]*href="([^"]+)"[^>]*id="([^"]+)"', meta)})
                base = opf.rsplit("/", 1)[0] + "/" if "/" in opf else ""
                for idref in re.findall(r'<itemref\b[^>]*idref="([^"]+)"', meta):
                    href = ids.get(idref)
                    if not href:
                        continue
                    full = base + href.split("#")[0]
                    if full in names:
                        order.append(full)
            except Exception:
                order = []
        if not order:
            order = sorted(n for n in names if n.lower().endswith((".xhtml", ".html", ".htm")))
        for n in order:
            try:
                text = xhtml_to_text(z.read(n).decode("utf-8", "replace"))
            except KeyError:
                continue
            out.append((n.rsplit("/", 1)[-1], text))
    return out


# ---------------------------------------------------------------------------
# Boilerplate. Aggregated ebooks repeat a heading at the top of every chapter
# and a credit or navigation line at the bottom. Classifying those as prose
# silently produces impossible statistics — 100% of anything is a bug report,
# not a finding — so they are detected across the corpus and stripped.
# ---------------------------------------------------------------------------

HEADING = re.compile(r"^\s*(chapter|ch\.?|episode|part)\s*[\divxlc]+\b", re.I)


def _norm(p: str) -> str:
    return re.sub(r"\d+", "#", re.sub(r"\s+", " ", p.strip().lower()))[:120]


def detect_boilerplate(docs: list[tuple[str, str]], threshold: float = 0.1) -> dict:
    """Normalised first/last paragraphs that repeat across the corpus."""
    from collections import Counter
    firsts, lasts = Counter(), Counter()
    n = 0
    for _, text in docs:
        ps = paragraphs(text)
        if not ps:
            continue
        n += 1
        firsts[_norm(ps[0])] += 1
        lasts[_norm(ps[-1])] += 1
    cut = max(2, int(n * threshold))
    return {
        "documents": n,
        "leading": {k: v for k, v in firsts.items() if v >= cut},
        "trailing": {k: v for k, v in lasts.items() if v >= cut},
    }


def strip_boilerplate(ps: list[str], boiler: dict) -> list[str]:
    out = list(ps)
    while out and (HEADING.match(out[0]) or _norm(out[0]) in boiler.get("leading", {})):
        out.pop(0)
    while out and _norm(out[-1]) in boiler.get("trailing", {}):
        out.pop()
    return out or ps


def load_metrics() -> dict:
    return store.load(METRICS, {"description": "Aggregate structural measurements. Numbers only — no prose is ever stored here.",
                                "sets": {}})


def collect(args) -> list[tuple[str, str]]:
    out = []
    if args.epub:
        docs = epub_documents(Path(args.epub))
        kept = [(n, x) for n, x in docs if words(x) >= args.min_words]
        skipped = len(docs) - len(kept)
        print(f"  {len(docs)} documents in spine; {len(kept)} measured, "
              f"{skipped} skipped under {args.min_words} words (front matter, covers, notices)")
        out.extend(kept)
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
    ap.add_argument("--epub", help="an .epub — each spine document is treated as a chapter")
    ap.add_argument("--min-words", type=int, default=300, dest="min_words",
                    help="skip documents shorter than this (front matter, covers)")
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
    boiler = detect_boilerplate(inputs)
    if boiler["leading"] or boiler["trailing"]:
        print(f"  boilerplate detected across {boiler['documents']} documents: "
              f"{len(boiler['leading'])} repeated leading line(s), "
              f"{len(boiler['trailing'])} repeated trailing line(s) — stripped before measuring")
    chapters = [measure_chapter(text, boiler) for _, text in inputs]
    summary = summarise(chapters)
    summary["boilerplate_stripped"] = {"leading_patterns": len(boiler["leading"]),
                                       "trailing_patterns": len(boiler["trailing"])}
    entry = {"measured": date.today().isoformat(), "summary": summary}
    if len(chapters) <= 400:
        entry["per_chapter"] = chapters
    else:
        entry["per_chapter_note"] = (f"{len(chapters)} chapters measured; per-chapter detail omitted to keep "
                                     "this file small. Word series retained for trend analysis.")
        entry["word_series"] = [c["words"] for c in chapters]
    metrics["sets"][label] = entry
    store.save(METRICS, metrics)
    print(f"Measured {len(chapters)} chapter(s) as '{label}'. Numbers only — no prose stored.\n")
    for k, v in summary.items():
        if k == "trend_by_decile":
            continue
        print(f"  {k}: {v}")
    for key in ("opening_move_distribution", "closing_move_distribution"):
        top = max(summary[key].values()) if summary[key] else 0
        if top >= 0.95:
            print(f"\n  WARNING: {key} is {int(top * 100)}% a single value. That is almost always a "
                  "parsing artifact, not a property of the text. Inspect before trusting it.")
    if summary.get("trend_by_decile"):
        print("\n  trend by decile (chapters, median words, dialogue ratio, hook share):")
        for r in summary["trend_by_decile"]:
            print(f"    {r['decile']:>2}  {r['chapters']:<14} {r['median_words']:>6}  "
                  f"{r['dialogue_ratio']:>6}  {r['hook_share']:>6}")
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
