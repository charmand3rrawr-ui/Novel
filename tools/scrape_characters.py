#!/usr/bin/env python3
"""Mine other novels for character *construction*, not character content.

What it does
------------
Reads source texts you are entitled to analyse, finds the figures in them, and
builds a behavioural fingerprint for each: how they are spoken about, how they
speak, what they do, what adverbs cling to them. It then abstracts those
fingerprints into trait atoms phrased in this project's own language, and —
this is the creative part — *crosses* fingerprints from different sources so
that every promoted atom is a hybrid no single source owns.

What it refuses to do
---------------------
- It never stores source prose. Only counts, classes, and generated phrasing.
- It never emits source names as usable names. Every detected name goes onto an
  avoid-list that the character generator reads and steers around.
- Nothing enters the lexicon automatically. Candidates land in
  `inspiration/mined.json` marked `pending` for you to review, then `--promote`.

Usage
-----
  scrape_characters.py --file drafts/old-novel.txt --label draft-2019
  scrape_characters.py --source pg-1342 --source pg-84      # from sources.json
  scrape_characters.py --url https://... --label something
  scrape_characters.py --review
  scrape_characters.py --promote all
  scrape_characters.py --promote mined-verbal_tic-3,mined-mask-1
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import urllib.request
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from novelkit import store  # noqa: E402

MINED = store.INSPIRATION / "mined.json"
SOURCES = store.INSPIRATION / "sources.json"

# Words that look like names but are not people.
STOP_CAPS = set("""
The A An And But Or So Yet For Nor If When While Then Than That This These Those There Here
He She They It We You I His Her Their Its Our Your My Him Them Us Me
Mr Mrs Miss Ms Dr Sir Madam Lady Lord Captain Colonel Major General Professor Saint St
Chapter Volume Book Part Letter Preface Contents Introduction Appendix Note Notes
Monday Tuesday Wednesday Thursday Friday Saturday Sunday
January February March April May June July August September October November December
God Heaven Hell Lord Providence Nature Fortune Project Gutenberg Ebook EBook
London England France Paris America English French Europe European
No Yes Oh Ah Well Now Never Nothing Something Everything Anything Perhaps Indeed Yet
""".split())

SPEECH_REGISTER = {
    "forceful": {"snapped", "barked", "roared", "shouted", "demanded", "growled", "thundered", "commanded", "retorted", "snarled"},
    "evasive": {"murmured", "mumbled", "muttered", "faltered", "stammered", "whispered", "sighed", "hesitated"},
    "formal": {"declared", "pronounced", "observed", "remarked", "replied", "answered", "responded", "stated", "affirmed", "continued"},
    "warm": {"laughed", "smiled", "teased", "chuckled", "beamed", "cried", "exclaimed", "urged"},
    "cold": {"said", "added", "returned", "resumed", "concluded", "noted", "repeated"},
}
REGISTER_OF = {v: k for k, vs in SPEECH_REGISTER.items() for v in vs}

ADVERB_REGISTER = {
    "controlled": {"quietly", "calmly", "carefully", "slowly", "deliberately", "steadily", "gravely", "coolly"},
    "volatile": {"suddenly", "angrily", "violently", "sharply", "fiercely", "hastily", "abruptly", "bitterly"},
    "performed": {"gaily", "cheerfully", "brightly", "gallantly", "politely", "graciously", "smilingly", "archly"},
    "withheld": {"faintly", "reluctantly", "coldly", "distantly", "vaguely", "absently", "wearily", "softly"},
}
ADVERB_OF = {a: k for k, vs in ADVERB_REGISTER.items() for a in vs}

ACTION_CLASS = {
    "acquisitive": {"took", "seized", "bought", "gathered", "collected", "claimed", "kept", "won", "secured"},
    "protective": {"guarded", "carried", "shielded", "saved", "tended", "nursed", "warned", "held", "covered"},
    "evasive": {"left", "fled", "avoided", "escaped", "withdrew", "hid", "slipped", "turned", "departed"},
    "inquisitive": {"asked", "searched", "watched", "studied", "read", "examined", "followed", "listened", "discovered"},
    "assertive": {"struck", "refused", "forced", "pushed", "ordered", "broke", "seized", "confronted", "challenged"},
    "social": {"wrote", "invited", "visited", "introduced", "danced", "married", "promised", "thanked", "greeted"},
}
ACTION_OF = {v: k for k, vs in ACTION_CLASS.items() for v in vs}

# ---------------------------------------------------------------------------
# Abstraction templates. Output is generated from these, never from the source.
# Each template takes two register labels from DIFFERENT sources: the cross is
# what makes the atom original.
# ---------------------------------------------------------------------------

TEMPLATES = {
    "verbal_tic": {
        ("forceful", "controlled"): "delivers threats at the volume of small talk",
        ("forceful", "volatile"): "escalates a sentence three times before finishing it",
        ("forceful", "performed"): "insults people warmly, and means both halves",
        ("forceful", "withheld"): "states the worst possible reading of events, flatly, and waits",
        ("evasive", "controlled"): "answers the question after the one you asked",
        ("evasive", "volatile"): "trails off mid-sentence, then finishes it an hour later",
        ("evasive", "performed"): "buries a refusal inside a compliment",
        ("evasive", "withheld"): "says less each time a subject is raised, until it is gone",
        ("formal", "controlled"): "speaks in clauses, as if everything might be read back to them",
        ("formal", "volatile"): "keeps perfect grammar while saying something unforgivable",
        ("formal", "performed"): "quotes procedure as a form of affection",
        ("formal", "withheld"): "uses titles for people they are closest to",
        ("warm", "controlled"): "laughs on a one-beat delay, always on purpose",
        ("warm", "volatile"): "gives compliments that land like accusations",
        ("warm", "performed"): "names everyone in the room before making a demand",
        ("warm", "withheld"): "is kindest in the moments they have already decided to leave",
        ("cold", "controlled"): "repeats your own words back, unaltered, until you hear them",
        ("cold", "volatile"): "goes silent for exactly as long as it takes to unnerve",
        ("cold", "performed"): "reports feelings as weather",
        ("cold", "withheld"): "answers in numbers when asked about people",
    },
    "mask": {
        ("acquisitive", "controlled"): "generosity administered like an investment schedule",
        ("acquisitive", "volatile"): "appetite dressed as ambition, and ambition dressed as duty",
        ("acquisitive", "performed"): "collects people the way others collect assurances",
        ("acquisitive", "withheld"): "asks for nothing and keeps a precise record of it",
        ("protective", "controlled"): "competence offered as care, so no one asks what it costs",
        ("protective", "volatile"): "guards others loudly to avoid being guarded",
        ("protective", "performed"): "makes themselves indispensable, then resents the dependence",
        ("protective", "withheld"): "watches over people from a distance they call respect",
        ("evasive", "controlled"): "agreeableness so total it functions as a locked door",
        ("evasive", "volatile"): "changes the subject with a joke sharp enough to leave a mark",
        ("evasive", "performed"): "is always just leaving, and always the last to go",
        ("evasive", "withheld"): "answers biography with anecdote",
        ("inquisitive", "controlled"): "curiosity framed as courtesy, and never reciprocal",
        ("inquisitive", "volatile"): "asks the one question the room agreed not to ask",
        ("inquisitive", "performed"): "flatters by remembering, and remembers everything",
        ("inquisitive", "withheld"): "studies people openly and reports nothing back",
        ("assertive", "controlled"): "reasonableness used as a battering ram",
        ("assertive", "volatile"): "principle invoked at exactly the moment it is convenient",
        ("assertive", "performed"): "makes every disagreement a performance others must watch",
        ("assertive", "withheld"): "refuses once, quietly, and never explains",
        ("social", "controlled"): "hospitality kept as a ledger of who owes an evening",
        ("social", "volatile"): "intimacy offered fast and withdrawn faster",
        ("social", "performed"): "a public warmth that has no private version",
        ("social", "withheld"): "knows everyone and is known by no one",
    },
    "competence": {
        ("acquisitive", "inquisitive"): "can value anything, including people, within a minute of seeing it",
        ("acquisitive", "social"): "turns a conversation into an obligation without raising their voice",
        ("acquisitive", "assertive"): "takes the only remaining option off the table before anyone else reaches",
        ("protective", "inquisitive"): "notices the injury a person is hiding before they admit it",
        ("protective", "assertive"): "puts themselves between two forces and makes both stop",
        ("protective", "social"): "keeps a network alive by remembering what each person cannot do",
        ("evasive", "inquisitive"): "leaves any room without being seen to decide to",
        ("evasive", "social"): "can make an entire group forget who raised a subject",
        ("evasive", "assertive"): "refuses without ever having said no",
        ("inquisitive", "social"): "reconstructs a stranger's whole situation from three questions",
        ("inquisitive", "assertive"): "finds the load-bearing lie in an argument and pulls it",
        ("assertive", "social"): "can move a room's decision without appearing to speak first",
    },
    "arc_shape": {
        ("controlled", "volatile"): "holds, holds, holds, then breaks in one irreversible scene",
        ("controlled", "performed"): "the performance becomes the person; nobody notices the swap",
        ("controlled", "withheld"): "erodes so slowly that the loss is only visible in flashback",
        ("volatile", "performed"): "burns bright, is loved for it, and is left by everyone who saw it up close",
        ("volatile", "withheld"): "spends the novel learning to want something out loud",
        ("performed", "withheld"): "drops the act once, to one person, and cannot take it back",
    },
}


# ---------------------------------------------------------------------------
# reading sources
# ---------------------------------------------------------------------------

def read_url(url: str, timeout: int = 60) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "novel-engine-miner/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return raw.decode("utf-8", errors="replace")


def strip_boilerplate(text: str) -> str:
    """Drop Project Gutenberg headers/footers if present."""
    start = re.search(r"\*\*\* ?START OF (?:THE|THIS) PROJECT GUTENBERG.*?\*\*\*", text, re.I)
    end = re.search(r"\*\*\* ?END OF (?:THE|THIS) PROJECT GUTENBERG.*?\*\*\*", text, re.I)
    if start:
        text = text[start.end():]
    if end:
        idx = text.find("*** END OF")
        if idx > 0:
            text = text[:idx]
    return text


# ---------------------------------------------------------------------------
# detection and profiling
# ---------------------------------------------------------------------------

def detect_names(text: str, top: int = 12) -> list[str]:
    """Capitalised tokens that appear mid-sentence often enough to be people."""
    counts = Counter()
    for m in re.finditer(r"(?<![.!?\"'\n]\s)(?<!^)\b([A-Z][a-z]{2,})\b", text, re.M):
        w = m.group(1)
        if w in STOP_CAPS:
            continue
        counts[w] += 1
    total = sum(counts.values()) or 1
    names = [w for w, c in counts.most_common(80) if c >= 8 and c / total < 0.2]
    return names[:top]


def profile(text: str, name: str, window: int = 90) -> dict:
    """Behavioural fingerprint for one figure. Counts only — no prose kept."""
    speech, adverbs, actions = Counter(), Counter(), Counter()
    pattern = re.compile(rf"\b{re.escape(name)}\b")
    for m in pattern.finditer(text):
        lo = max(0, m.start() - window)
        hi = min(len(text), m.end() + window)
        span = text[lo:hi].lower()
        for word in re.findall(r"[a-z]+", span):
            if word in REGISTER_OF:
                speech[REGISTER_OF[word]] += 1
            if word in ADVERB_OF:
                adverbs[ADVERB_OF[word]] += 1
            if word in ACTION_OF:
                actions[ACTION_OF[word]] += 1
    mentions = sum(1 for _ in pattern.finditer(text))
    return {
        "mentions": mentions,
        "speech": dict(speech),
        "adverb": dict(adverbs),
        "action": dict(actions),
        "dominant_speech": speech.most_common(1)[0][0] if speech else None,
        "dominant_adverb": adverbs.most_common(1)[0][0] if adverbs else None,
        "dominant_action": actions.most_common(1)[0][0] if actions else None,
    }


def mine(text: str, label: str, top: int = 12) -> dict:
    text = strip_boilerplate(text)
    names = detect_names(text, top=top)
    figures = []
    for n in names:
        p = profile(text, n)
        if p["mentions"] < 8:
            continue
        figures.append({"label": label, "profile": p})  # the name is deliberately NOT kept here
    return {"label": label, "names_found": names, "figures": figures}


# ---------------------------------------------------------------------------
# abstraction and crossing
# ---------------------------------------------------------------------------

def cross_atoms(all_figures: list[dict], rng: random.Random, limit: int = 24) -> list[dict]:
    """Hybridise fingerprints from different sources into new trait atoms."""
    by_label = defaultdict(list)
    for f in all_figures:
        by_label[f["label"]].append(f["profile"])
    labels = list(by_label)
    atoms, seen = [], set()

    def add(pool, key_a, key_b, sources):
        text = TEMPLATES[pool].get((key_a, key_b))
        if not text or text in seen:
            return
        seen.add(text)
        atoms.append({
            "pool": pool,
            "text": text,
            "provenance": {
                "method": "cross-source abstraction",
                "registers": [key_a, key_b],
                "sources": sorted(set(sources)),
            },
            "review": "pending",
        })

    pairs = []
    for i, la in enumerate(labels):
        for lb in labels[i:] if len(labels) > 1 else labels:
            for pa in by_label[la]:
                for pb in by_label[lb]:
                    if pa is pb:
                        continue
                    pairs.append((la, pa, lb, pb))
    rng.shuffle(pairs)

    for la, pa, lb, pb in pairs:
        if len(atoms) >= limit:
            break
        if pa["dominant_speech"] and pb["dominant_adverb"]:
            add("verbal_tic", pa["dominant_speech"], pb["dominant_adverb"], [la, lb])
        if pa["dominant_action"] and pb["dominant_adverb"]:
            add("mask", pa["dominant_action"], pb["dominant_adverb"], [la, lb])
        if pa["dominant_action"] and pb["dominant_action"] and pa["dominant_action"] != pb["dominant_action"]:
            add("competence", pa["dominant_action"], pb["dominant_action"], [la, lb])
        if pa["dominant_adverb"] and pb["dominant_adverb"] and pa["dominant_adverb"] != pb["dominant_adverb"]:
            add("arc_shape", pa["dominant_adverb"], pb["dominant_adverb"], [la, lb])
    return atoms[:limit]


# ---------------------------------------------------------------------------
# store
# ---------------------------------------------------------------------------

def load_mined() -> dict:
    return store.load(MINED, {"avoid_names": [], "atoms_added": 0, "sources": [], "candidates": [], "figures": []})


def save_mined(data: dict) -> None:
    store.save(MINED, data)


def promote(ids: list[str]) -> int:
    data = load_mined()
    lex = store.load(store.LEXICON)
    wanted = set(ids)
    promoted = 0
    for cand in data.get("candidates", []):
        if cand["review"] == "promoted":
            continue
        if "all" not in wanted and cand["id"] not in wanted:
            continue
        pool = lex["pools"].setdefault(cand["pool"], [])
        if any(a["text"] == cand["text"] for a in pool):
            cand["review"] = "duplicate"
            continue
        pool.append({
            "id": cand["id"],
            "text": cand["text"],
            "origin": "mined",
            "provenance": cand["provenance"],
        })
        cand["review"] = "promoted"
        promoted += 1
    lex["version"] = lex.get("version", 1) + (1 if promoted else 0)
    store.save(store.LEXICON, lex)
    data["atoms_added"] = data.get("atoms_added", 0) + promoted
    save_mined(data)
    return promoted


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", action="append", default=[], help="local text file to mine")
    ap.add_argument("--url", action="append", default=[], help="URL of a text you are entitled to analyse")
    ap.add_argument("--source", action="append", default=[], help="id from inspiration/sources.json")
    ap.add_argument("--label", help="label for --file/--url inputs (defaults to the filename)")
    ap.add_argument("--top", type=int, default=12, help="how many figures to profile per source")
    ap.add_argument("--limit", type=int, default=24, help="max candidate atoms to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--review", action="store_true", help="list pending candidates")
    ap.add_argument("--promote", help="comma-separated candidate ids, or 'all'")
    args = ap.parse_args(argv)

    data = load_mined()

    if args.review:
        pend = [c for c in data.get("candidates", []) if c["review"] == "pending"]
        if not pend:
            print("No pending candidates. Mine a source first.")
            return 0
        print(f"{len(pend)} pending candidate atom(s):\n")
        for c in pend:
            print(f"  {c['id']}")
            print(f"    pool      : {c['pool']}")
            print(f"    text      : {c['text']}")
            print(f"    crossed   : {' x '.join(c['provenance']['registers'])} "
                  f"from {', '.join(c['provenance']['sources'])}")
        print("\nPromote with: scrape_characters.py --promote all")
        return 0

    if args.promote:
        n = promote([i.strip() for i in args.promote.split(",")])
        print(f"Promoted {n} atom(s) into inspiration/lexicon.json.")
        print("They are now in the generator's pool — `novel.py character new` will draw from them.")
        return 0

    inputs = []
    for f in args.file:
        p = Path(f)
        inputs.append((args.label or p.stem, p.read_text(encoding="utf-8", errors="replace")))
    for u in args.url:
        print(f"fetching {u} ...")
        inputs.append((args.label or re.sub(r"\W+", "-", u)[-24:], read_url(u)))
    if args.source:
        catalog = {s["id"]: s for s in store.load(SOURCES)["sources"]}
        for sid in args.source:
            if sid not in catalog:
                print(f"unknown source id '{sid}'. Known: {', '.join(catalog)}", file=sys.stderr)
                return 1
            s = catalog[sid]
            print(f"fetching {s['title']} ({s['status']}) ...")
            inputs.append((sid, read_url(s["url"])))

    if not inputs:
        ap.print_help()
        return 1

    rng = random.Random(args.seed)
    figures, new_names = [], set()
    for label, text in inputs:
        result = mine(text, label, top=args.top)
        figures.extend(result["figures"])
        new_names.update(result["names_found"])
        print(f"  {label}: {len(result['figures'])} figures profiled from {len(result['names_found'])} candidate names")
        data["sources"] = [s for s in data.get("sources", []) if s.get("label") != label]
        data["sources"].append({"label": label, "mined": date.today().isoformat(), "figures": len(result["figures"])})

    existing_figures = data.get("figures", []) + figures
    atoms = cross_atoms(existing_figures, rng, limit=args.limit)

    counter = defaultdict(int)
    existing_ids = {c["id"] for c in data.get("candidates", [])}
    existing_texts = {c["text"] for c in data.get("candidates", [])}
    fresh = []
    for a in atoms:
        if a["text"] in existing_texts:
            continue
        counter[a["pool"]] += 1
        cid = f"mined-{a['pool']}-{counter[a['pool']]}"
        while cid in existing_ids:
            counter[a["pool"]] += 1
            cid = f"mined-{a['pool']}-{counter[a['pool']]}"
        existing_ids.add(cid)
        fresh.append({"id": cid, **a})

    data["figures"] = existing_figures[-200:]
    data["candidates"] = data.get("candidates", []) + fresh
    data["avoid_names"] = sorted(set(data.get("avoid_names", [])) | new_names)
    save_mined(data)

    print(f"\n{len(fresh)} new candidate atom(s) written to {store.rel(MINED)}.")
    print(f"{len(new_names)} source names added to the avoid-list — the generator will not reuse them.")
    for a in fresh[:8]:
        print(f"  {a['id']:26} [{a['pool']}] {a['text']}")
    print("\nReview:  tools/scrape_characters.py --review")
    print("Promote: tools/scrape_characters.py --promote all")
    return 0


if __name__ == "__main__":
    try:
        import signal
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (AttributeError, ValueError):
        pass
    raise SystemExit(main())
