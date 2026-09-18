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


def measure_chapter(text: str, boiler: dict | None = None, deep: bool = False,
                    matchers: dict | None = None) -> dict:
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
        "open_continuity": classify_open_continuity(ps[0]),
        "close_kind": classify_close_kind(ps[-1]),
        "short_paragraph_share": round(sum(1 for p in ps if words(p) <= 10) / max(1, len(ps)), 3),
        **sentence_stats(ps),
        **dialogue_stats(" ".join(ps), ps),
        **({"profile": paragraph_profile(ps)} if deep else {}),
        **({"craft": craft_measure(" ".join(ps), matchers, w)} if matchers else {}),
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
        "open_continuity_distribution": dist("open_continuity"),
        "close_kind_distribution": dist("close_kind"),
        "short_paragraph_share_median": round(statistics.median(
            [c.get("short_paragraph_share", 0) for c in chapters]), 3),
        "sentences": {
            "median_words": round(statistics.median(
                [c["median_sentence_words"] for c in chapters if "median_sentence_words" in c]), 1),
            "p90_words": int(statistics.median(
                [c["p90_sentence_words"] for c in chapters if "p90_sentence_words" in c])),
            "short_sentence_share": round(statistics.median(
                [c["short_sentence_share"] for c in chapters if "short_sentence_share" in c]), 3),
            "length_stdev": round(statistics.median(
                [c["sentence_length_stdev"] for c in chapters if "sentence_length_stdev" in c]), 1),
        },
        "dialogue": {
            "segments_per_chapter_median": round(statistics.median(
                [c["dialogue_segments"] for c in chapters]), 1),
            "median_segment_words": round(statistics.median(
                [c["median_dialogue_words"] for c in chapters]), 1),
            "share_of_words": round(statistics.median(
                [c["dialogue_word_share"] for c in chapters]), 3),
        },
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


# ---------------------------------------------------------------------------
# Deep per-chapter analysis. Everything here is counts, ratios and positions.
# Proper nouns are tracked in memory to measure introduction rate and how long
# an entity stays relevant; the strings themselves are never written out.
# ---------------------------------------------------------------------------

SENT = re.compile(r"(?<=[.!?…])[\s\"”']+")
DIALOGUE_SEG = re.compile(r"[\"“]([^\"“”]{2,400})[\"”]")
PRONOUN_OPEN = re.compile(r"^\s*(he|she|they|it|his|her|their)\b", re.I)
CAP_TOKEN = re.compile(r"(?<![.!?\"“]\s)(?<!^)\b([A-Z][a-z]{2,})\b", re.M)
COMMON_CAPS = set("""
The A An And But Or So Yet For Nor If When While Then Than That This These Those There Here
He She They It We You I His Her Their Its Our Your My Him Them Us Me Chapter Mr Mrs Miss Ms Dr Sir
No Yes Oh Ah Well Now Never Nothing Something Everything Anything Perhaps Indeed However Although
Even After Before Once Because Since Until Unless Though What Who Why How Where Which
""".split())


def sentence_stats(ps: list[str]) -> dict:
    lens = []
    for p in ps:
        for s in SENT.split(p):
            w = words(s)
            if w:
                lens.append(w)
    if not lens:
        return {}
    return {
        "sentences": len(lens),
        "median_sentence_words": round(statistics.median(lens), 1),
        "p90_sentence_words": int(statistics.quantiles(lens, n=10)[-1]) if len(lens) >= 10 else max(lens),
        "short_sentence_share": round(sum(1 for x in lens if x <= 5) / len(lens), 3),
        "sentence_length_stdev": round(statistics.pstdev(lens), 1),
    }


def dialogue_stats(text: str, ps: list[str]) -> dict:
    segs = [words(m.group(1)) for m in DIALOGUE_SEG.finditer(text)]
    return {
        "dialogue_segments": len(segs),
        "median_dialogue_words": round(statistics.median(segs), 1) if segs else 0,
        "dialogue_word_share": round(sum(segs) / max(1, sum(words(p) for p in ps)), 3),
    }


def paragraph_profile(ps: list[str], buckets: int = 5) -> dict:
    """Where dialogue and short paragraphs sit INSIDE a chapter. This is the
    chapter's internal shape, which chapter-level averages hide completely."""
    if len(ps) < buckets:
        return {}
    size = len(ps) / buckets
    prof_dialogue, prof_words = [], []
    for i in range(buckets):
        chunk = ps[int(i * size):int((i + 1) * size)] or [ps[-1]]
        prof_dialogue.append(round(sum(1 for p in chunk if has_dialogue(p)) / len(chunk), 3))
        prof_words.append(round(statistics.mean([words(p) for p in chunk]), 1))
    return {"dialogue_by_fifth": prof_dialogue, "paragraph_words_by_fifth": prof_words}


def classify_open_continuity(p: str) -> str:
    """Cold open, or continuing the previous scene? 'named_subject' requires a
    real proper noun — a capitalised first word alone would also match "The
    morning was cold", which is scene-setting, not a named subject."""
    s = p.strip()
    if has_dialogue(s[:80]):
        return "cold_dialogue"
    if PRONOUN_OPEN.match(s):
        return "continuation"
    m = re.match(r"^\s*([A-Z][a-z]{2,})\b", s)
    if m and m.group(1) not in COMMON_CAPS:
        return "named_subject"
    return "scene_setting"


def classify_close_kind(p: str) -> str:
    s = p.strip()
    if has_dialogue(s[-120:]):
        return "on_dialogue"
    if s.endswith("?"):
        return "on_question"
    if re.search(r"\b(would|will|was going to|about to)\b", s.lower()[-160:]):
        return "on_intent"
    if re.search(r"\b(suddenly|at that moment|just then|before)\b", s.lower()[-160:]):
        return "mid_action"
    return "on_statement"


def proper_nouns(text: str) -> set:
    return {m.group(1) for m in CAP_TOKEN.finditer(text)} - COMMON_CAPS


def entity_dynamics(docs_tokens: list[set]) -> dict:
    """Introduction rate and persistence, from proper-noun first/last appearance.
    Names live in memory only; nothing but counts is returned."""
    first, last = {}, {}
    new_per_chapter = []
    for i, toks in enumerate(docs_tokens):
        new = 0
        for tok in toks:
            if tok not in first:
                first[tok] = i
                new += 1
            last[tok] = i
        new_per_chapter.append(new)
    spans = [last[k] - first[k] for k in first]
    one_shot = sum(1 for s in spans if s == 0)
    return {
        "distinct_entities": len(first),
        "new_entities_per_chapter_median": round(statistics.median(new_per_chapter), 1),
        "new_entities_per_chapter_p90": int(statistics.quantiles(new_per_chapter, n=10)[-1])
            if len(new_per_chapter) >= 10 else max(new_per_chapter),
        "single_chapter_entity_share": round(one_shot / max(1, len(spans)), 3),
        "median_entity_span_chapters": int(statistics.median(spans)),
        "p90_entity_span_chapters": int(statistics.quantiles(spans, n=10)[-1]) if len(spans) >= 10 else max(spans),
        "note": "Span = chapters between an entity's first and last appearance. A high single-chapter share "
                "means most named things are local colour and are allowed to leave."
    }


def changepoints(series: list[int], block: int = 50, threshold: float = 0.15) -> list[dict]:
    """Structural shifts in chapter length — a proxy for volume or arc borders,
    found without reading a word of plot."""
    if len(series) < block * 3:
        return []
    blocks = []
    for i in range(0, len(series) - block + 1, block):
        blocks.append((i + 1, statistics.median(series[i:i + block])))
    shifts = []
    for (s0, m0), (s1, m1) in zip(blocks, blocks[1:]):
        if m0 and abs(m1 - m0) / m0 >= threshold:
            shifts.append({"at_chapter": s1, "median_before": int(m0), "median_after": int(m1),
                           "change": f"{(m1 - m0) / m0 * 100:+.0f}%"})
    return shifts


# ---------------------------------------------------------------------------
# Craft texture: the emotional and intentional weather of the prose, measured
# with generic English word lists. Counts and rates only.
# ---------------------------------------------------------------------------

CRAFT_LEXICON = Path(__file__).resolve().parent / "novelkit" / "craft_lexicon.json"


def craft_lexicon() -> dict:
    return store.load(CRAFT_LEXICON)


def _build_matchers(lex: dict) -> dict:
    out = {}
    for group in ("categories", "registers"):
        for name, terms in lex[group].items():
            singles = sorted({w for w in terms if " " not in w})
            phrases = sorted({w for w in terms if " " in w})
            pat = r"\b(" + "|".join(re.escape(w) for w in singles) + r")\b"
            if phrases:
                pat += r"|(" + "|".join(re.escape(w) for w in phrases) + r")"
            out[name] = (group, re.compile(pat, re.I))
    return out


def craft_measure(text: str, matchers: dict, total_words: int) -> dict:
    """Raw hit counts, not per-chapter rates. These counts are sparse at ~1,000
    words a chapter, so the median of per-chapter rates collapses to zero and
    says nothing. Rates are computed at corpus level instead."""
    low = text.lower()
    out = {"_words": total_words}
    for name, (group, rx) in matchers.items():
        out[name] = len(rx.findall(low))
    return out


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
    ap.add_argument("--craft", action="store_true",
                    help="emotional and intentional texture: emotion categories, interiority, goal statements, "
                         "progression and stakes vocabulary, per 1000 words")
    ap.add_argument("--deep", action="store_true",
                    help="per-chapter internal profile, entity dynamics, and structural changepoints")
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
    matchers = _build_matchers(craft_lexicon()) if args.craft else None
    if matchers:
        print("  measuring emotional and intentional texture ...")
    chapters = [measure_chapter(text, boiler, deep=args.deep, matchers=matchers) for _, text in inputs]
    summary = summarise(chapters)
    if args.deep:
        profs = [c["profile"] for c in chapters if c.get("profile")]
        if profs:
            fifths = len(profs[0]["dialogue_by_fifth"])
            summary["average_chapter_profile"] = {
                "dialogue_by_fifth": [round(statistics.mean([p["dialogue_by_fifth"][i] for p in profs]), 3)
                                      for i in range(fifths)],
                "paragraph_words_by_fifth": [round(statistics.mean([p["paragraph_words_by_fifth"][i] for p in profs]), 1)
                                             for i in range(fifths)],
                "note": "The internal shape of the average chapter, in fifths. Chapter-level averages hide this.",
            }
        print("  computing entity dynamics ...")
        summary["entity_dynamics"] = entity_dynamics([proper_nouns(x) for _, x in inputs])
        summary["structural_changepoints"] = changepoints([c["words"] for c in chapters])
        for c in chapters:
            c.pop("profile", None)
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
    if args.craft:
        names = sorted(k for k in chapters[0]["craft"] if k != "_words")

        def rate(chs, name):
            w = sum(c["craft"]["_words"] for c in chs)
            h = sum(c["craft"][name] for c in chs)
            return round(h * 1000 / max(1, w), 2)

        def presence(chs, name):
            return round(sum(1 for c in chs if c["craft"][name] > 0) / max(1, len(chs)), 3)

        tenth = max(1, len(chapters) // 10)
        summary["craft_rates_per_1000_words"] = {n: rate(chapters, n) for n in names}
        summary["craft_chapter_presence"] = {n: presence(chapters, n) for n in names}
        summary["craft_drift_first_vs_last_decile"] = {
            n: {"first": rate(chapters[:tenth], n), "last": rate(chapters[-tenth:], n)} for n in names}
        print("\n  craft texture — corpus rate per 1000 words, share of chapters containing it,")
        print("  and drift from the first decile to the last:")
        for n in names:
            d0 = summary["craft_drift_first_vs_last_decile"][n]
            delta = d0["last"] - d0["first"]
            arrow = "  " if abs(delta) < 0.05 else ("UP" if delta > 0 else "dn")
            print(f"    {n:<16} {summary['craft_rates_per_1000_words'][n]:>6}/1k   "
                  f"in {summary['craft_chapter_presence'][n] * 100:>5.1f}% of chapters   "
                  f"{d0['first']:>6} -> {d0['last']:>6}  {arrow}")
        for c in chapters:
            c.pop("craft", None)
    if summary.get("average_chapter_profile"):
        ap_ = summary["average_chapter_profile"]
        print("\n  average chapter internal shape (fifths, start -> end):")
        print(f"    dialogue density   {ap_['dialogue_by_fifth']}")
        print(f"    paragraph words    {ap_['paragraph_words_by_fifth']}")
    if summary.get("entity_dynamics"):
        e = summary["entity_dynamics"]
        print("\n  entity dynamics:")
        for k in ("distinct_entities", "new_entities_per_chapter_median", "new_entities_per_chapter_p90",
                  "single_chapter_entity_share", "median_entity_span_chapters", "p90_entity_span_chapters"):
            print(f"    {k}: {e[k]}")
    if summary.get("structural_changepoints"):
        print(f"\n  structural changepoints ({len(summary['structural_changepoints'])} shifts of >=15% "
              "in median chapter length):")
        for s in summary["structural_changepoints"][:12]:
            print(f"    ch.{s['at_chapter']:<6} {s['median_before']} -> {s['median_after']} words  {s['change']}")
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
