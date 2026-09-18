"""Continuity: the novel's memory.

`continuity/chapter-index.json` is the answer to "what in the past does this
chapter have to respect?". Every chapter records its *load-bearing* items —
facts, promises, objects, injuries, rules, secrets — with a weight and recall
tags. `lookback` then searches that record so the present can find the exact
earlier chapter it needs, instead of re-reading the whole book.

`continuity/threads.json` tracks planted seeds and their payoffs, and feeds the
engine's rot warnings.
"""

from __future__ import annotations

import re
from datetime import date

from . import store

KINDS = ["fact", "promise", "object", "injury", "rule", "relationship", "secret", "name", "place", "debt"]


def index() -> dict:
    return store.load(store.CHAPTER_INDEX, {"chapters": []})


def save_index(idx: dict) -> None:
    idx["chapters"].sort(key=lambda c: c["chapter"])
    store.save(store.CHAPTER_INDEX, idx)


def threads() -> dict:
    return store.load(store.THREADS, {"threads": []})


def save_threads(t: dict) -> None:
    store.save(store.THREADS, t)


def get_chapter(idx: dict, n: int):
    for c in idx["chapters"]:
        if c["chapter"] == n:
            return c
    return None


def ensure_chapter(idx: dict, n: int, **fields) -> dict:
    ch = get_chapter(idx, n)
    if ch is None:
        ch = {
            "chapter": n,
            "title": "",
            "arc": "",
            "pov": "",
            "beat": "",
            "tension": 0,
            "kind": "",
            "summary": "",
            "characters": [],
            "environments": [],
            "load_bearing": [],
            "seeds_planted": [],
            "seeds_paid": [],
            "callbacks_to": [],
            "recorded": date.today().isoformat(),
        }
        idx["chapters"].append(ch)
    for k, v in fields.items():
        if v not in (None, "", [], {}):
            ch[k] = v
    return ch


def add_point(chapter: int, kind: str, text: str, *, weight: int = 3, tags=None,
              must_respect: bool = True, lock: str = "") -> dict:
    if kind not in KINDS:
        raise ValueError(f"kind must be one of: {', '.join(KINDS)}")
    idx = index()
    ch = ensure_chapter(idx, chapter)
    pid = f"lb-{chapter}-{len(ch['load_bearing']) + 1}"
    point = {
        "id": pid,
        "kind": kind,
        "text": text,
        "weight": max(1, min(5, int(weight))),
        "tags": sorted({t.strip().lower() for t in (tags or []) if t.strip()}),
        "must_respect": must_respect,
        "lock": lock,
    }
    ch["load_bearing"].append(point)
    save_index(idx)
    return point


def plant(tid: str, summary: str, chapter: int, *, kind: str = "seed", owner: str = "") -> dict:
    t = threads()
    if any(x["id"] == tid for x in t["threads"]):
        raise ValueError(f"thread id already exists: {tid}")
    th = {
        "id": tid,
        "summary": summary,
        "kind": kind,
        "owner": owner,
        "planted_chapter": chapter,
        "status": "open",
        "payoff_chapter": None,
        "notes": "",
    }
    t["threads"].append(th)
    save_threads(t)
    idx = index()
    ch = ensure_chapter(idx, chapter)
    if tid not in ch["seeds_planted"]:
        ch["seeds_planted"].append(tid)
    save_index(idx)
    return th


def pay(tid: str, chapter: int, note: str = "", status: str = "paid") -> dict:
    t = threads()
    for th in t["threads"]:
        if th["id"] == tid:
            th["status"] = status
            th["payoff_chapter"] = chapter
            th["notes"] = note
            save_threads(t)
            idx = index()
            ch = ensure_chapter(idx, chapter)
            if tid not in ch["seeds_paid"]:
                ch["seeds_paid"].append(tid)
            planted = th["planted_chapter"]
            if planted not in ch["callbacks_to"]:
                ch["callbacks_to"].append(planted)
            save_index(idx)
            return th
    raise ValueError(f"unknown thread: {tid}")


# --------------------------------------------------------------------------
# lookback - the point of the whole file
# --------------------------------------------------------------------------

def _terms(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9']+", text.lower()) if len(w) > 2}


def lookback(query: str = "", *, tags=None, kinds=None, before: int | None = None,
             min_weight: int = 1, limit: int = 20) -> list[dict]:
    """Rank past load-bearing items against a query. Returns hits with chapter
    citations so the author can go straight to the source scene."""
    idx = index()
    qterms = _terms(query)
    want_tags = {t.lower() for t in (tags or [])}
    want_kinds = {k.lower() for k in (kinds or [])}
    hits = []
    max_ch = max([c["chapter"] for c in idx["chapters"]], default=0)
    for ch in idx["chapters"]:
        if before is not None and ch["chapter"] >= before:
            continue
        for p in ch["load_bearing"]:
            if p["weight"] < min_weight:
                continue
            if want_kinds and p["kind"] not in want_kinds:
                continue
            tag_hits = want_tags & set(p["tags"])
            if want_tags and not tag_hits:
                continue
            overlap = qterms & (_terms(p["text"]) | set(p["tags"]))
            if qterms and not overlap and not tag_hits:
                continue
            recency = 1.0 - ((max_ch - ch["chapter"]) / (max_ch or 1)) * 0.4
            score = (p["weight"] * 2) + (len(overlap) * 3) + (len(tag_hits) * 4)
            score *= recency
            score += 2 if p.get("must_respect") else 0
            hits.append({
                "score": round(score, 2),
                "chapter": ch["chapter"],
                "chapter_title": ch.get("title", ""),
                "id": p["id"],
                "kind": p["kind"],
                "text": p["text"],
                "weight": p["weight"],
                "tags": p["tags"],
                "must_respect": p.get("must_respect", True),
            })
    hits.sort(key=lambda h: (-h["score"], h["chapter"]))
    return hits[:limit]


def brief(chapter: int, *, limit: int = 12) -> dict:
    """Everything chapter N must not contradict, assembled from the past."""
    idx = index()
    past = [c for c in idx["chapters"] if c["chapter"] < chapter]
    binding = []
    for ch in past:
        for p in ch["load_bearing"]:
            if p.get("must_respect") and p["weight"] >= 3:
                binding.append({**p, "chapter": ch["chapter"]})
    binding.sort(key=lambda p: (-p["weight"], -p["chapter"]))

    t = threads()
    unpaid = [th for th in t["threads"] if th["status"] == "open" and th["planted_chapter"] < chapter]
    recent = [c for c in past if c["chapter"] >= chapter - 3]
    return {
        "chapter": chapter,
        "binding_facts": binding[:limit],
        "unpaid_threads": sorted(unpaid, key=lambda th: th["planted_chapter"]),
        "recent_chapters": [
            {"chapter": c["chapter"], "title": c.get("title", ""), "summary": c.get("summary", ""),
             "characters": c.get("characters", []), "environments": c.get("environments", [])}
            for c in recent
        ],
        "cast_last_seen": _last_seen(past, "characters"),
        "stage_last_seen": _last_seen(past, "environments"),
    }


def _last_seen(chapters, key) -> dict:
    seen = {}
    for ch in chapters:
        for item in ch.get(key, []):
            seen[item] = ch["chapter"]
    return dict(sorted(seen.items(), key=lambda kv: -kv[1]))


# --------------------------------------------------------------------------
# human-readable mirror
# --------------------------------------------------------------------------

def render_reference_map() -> str:
    idx = index()
    t = threads()
    out = [
        "# Reference Map",
        "",
        "_Generated by `novel.py continuity sync`. Machine source: "
        "`continuity/chapter-index.json` and `continuity/threads.json`._",
        "",
        "This is the file the present looks back through. Each chapter lists only what is "
        "**load-bearing** — the material later chapters are not allowed to contradict.",
        "",
        "## Chapters",
        "",
    ]
    if not idx["chapters"]:
        out += ["_No chapters recorded yet._", ""]
    for ch in idx["chapters"]:
        out.append(f"### Chapter {ch['chapter']}{' — ' + ch['title'] if ch.get('title') else ''}")
        meta = [x for x in [ch.get("arc"), ch.get("beat"), f"tension {ch.get('tension')}" if ch.get("tension") else "",
                            f"POV {ch.get('pov')}" if ch.get("pov") else ""] if x]
        if meta:
            out.append("`" + "` · `".join(meta) + "`")
        out.append("")
        if ch.get("summary"):
            out += [ch["summary"], ""]
        if ch.get("characters") or ch.get("environments"):
            out.append(f"- On stage: {', '.join(ch.get('characters', [])) or '—'} @ "
                       f"{', '.join(ch.get('environments', [])) or '—'}")
        for p in ch.get("load_bearing", []):
            star = "!" if p.get("must_respect") else " "
            out.append(f"- `{p['id']}` **{p['kind']}** (w{p['weight']}{star}) {p['text']}"
                       + (f"  _lock: {p['lock']}_" if p.get("lock") else "")
                       + (f"  _tags: {', '.join(p['tags'])}_" if p["tags"] else ""))
        if ch.get("seeds_planted"):
            out.append(f"- Seeds planted: {', '.join(ch['seeds_planted'])}")
        if ch.get("seeds_paid"):
            out.append(f"- Seeds paid: {', '.join(ch['seeds_paid'])}")
        if ch.get("callbacks_to"):
            out.append(f"- Looks back to: {', '.join('ch.' + str(c) for c in ch['callbacks_to'])}")
        out.append("")
    out += ["## Threads", ""]
    if not t["threads"]:
        out += ["_No threads recorded yet._", ""]
    for th in t["threads"]:
        state = th["status"]
        tail = f" → paid ch.{th['payoff_chapter']}" if th.get("payoff_chapter") else ""
        out.append(f"- `{th['id']}` **{state}** planted ch.{th['planted_chapter']}{tail} — {th['summary']}")
    out.append("")
    return "\n".join(out)
