"""Character creation.

Two rules run this module:

1. Depth is generated up front. A character exists in full — wound, lie, mask,
   offstage life, exit condition — before a single line of them is written.
2. Nobody walks on stage without a need. Generation puts a character in
   `characters/dormant/`. Only `introduce` moves them into the live cast, and
   only with a stated narrative need, an arc-licensed role, and budget left.
"""

from __future__ import annotations

import random
from datetime import date

from . import engine, store

SYLLABLES = {
    "ledger": {
        "given": ["Kes", "Vor", "Mal", "Ter", "Sil", "Ona", "Bree", "Cal", "Dros", "Ifa", "Hal", "Rhen", "Ysa", "Pell"],
        "mid": ["", "", "tra", "ven", "mi", "dor", "sa", "li"],
        "family": ["Vane", "Corr", "Halloway", "Strand", "Meer", "Quill", "Ashet", "Bram", "Follet", "Orne", "Wray"],
    },
    "outer": {
        "given": ["Zev", "Nia", "Okan", "Ru", "Ilm", "Tash", "Eno", "Sabe", "Varr", "Ido", "Neku", "Ammi"],
        "mid": ["", "", "ra", "no", "ku", "sha"],
        "family": ["Oduya", "Saal", "Ventris", "Nakamo", "Ilesh", "Bonnaire", "Tarek", "Osgard", "Maren"],
    },
    "frontier": {
        "given": ["Bly", "Coen", "Junip", "Stell", "Ward", "Ash", "Rook", "Tam", "Wren", "Ode"],
        "mid": ["", "", "er", "ia"],
        "family": ["Hollis", "Pike", "Danner", "Vesper", "Kettle", "Thorne", "Marsh", "Creed", "Alder"],
    },
}

ROLE_FUNCTIONS = {
    "rival": "mirrors the MC's method with a different wound; proves the method is not destiny",
    "mentor": "hands over a tool and a blind spot in the same gesture",
    "institution-face": "the system with a pulse; makes policy personal",
    "peer-ally": "keeps the MC legible as a person; the cost track made visible",
    "patron": "converts competence into obligation",
    "handler": "operationalizes the patron's will; the daily face of the terms",
    "dependent": "makes the stakes concrete and unignorable",
    "antagonist": "wants something coherent that the MC's want forecloses",
    "foil-from-outside": "shows what the MC looks like to people who owe them nothing",
    "the-discarded": "the MC's future if the lie holds",
    "the-one-who-stays": "disproves the lie by refusing to leave",
    "successor": "receives what the MC could not keep",
}


def registry() -> dict:
    return store.load(store.CHAR_REGISTRY, {"characters": []})


def save_registry(reg: dict) -> None:
    store.save(store.CHAR_REGISTRY, reg)


def find(reg: dict, cid: str):
    for c in reg["characters"]:
        if c["id"] == cid:
            return c
    return None


def _taken_names(reg: dict) -> set[str]:
    names = set()
    for c in reg["characters"]:
        names.add(c["name"].lower())
        for part in c["name"].split():
            names.add(part.lower())
    return names


def _banned_names() -> set[str]:
    """Names harvested from mined sources are recorded only so the generator can
    avoid them. Originality guard, not a name bank."""
    mined = store.load(store.INSPIRATION / "mined.json", {"avoid_names": []})
    return {n.lower() for n in mined.get("avoid_names", [])}


def make_name(rng: random.Random, culture: str, reg: dict) -> str:
    pool = SYLLABLES.get(culture, SYLLABLES["ledger"])
    blocked = _taken_names(reg) | _banned_names()
    def too_close(word: str) -> bool:
        """Exact matches are not enough: 'Kes' beside 'Kestrel' reads as a typo,
        not a second character. Reject anything that prefixes, or is prefixed
        by, a name already in play."""
        w = word.lower()
        for taken in blocked:
            if len(w) >= 3 and len(taken) >= 3 and (w.startswith(taken[:3]) and (w in taken or taken in w)):
                return True
            if w == taken:
                return True
        return False

    for _ in range(300):
        given = rng.choice(pool["given"]) + rng.choice(pool["mid"])
        family = rng.choice(pool["family"])
        name = f"{given.capitalize()} {family}"
        if not too_close(given) and not too_close(family):
            return name
    return f"{rng.choice(pool['given'])}{rng.randrange(100)} {rng.choice(pool['family'])}"


def _pick(rng, lex, pool, exclude_axis=None):
    items = lex["pools"][pool]
    if exclude_axis:
        filtered = [i for i in items if i.get("axis") != exclude_axis]
        items = filtered or items
    return rng.choice(items)


def generate(role: str, *, need: str, culture: str = "ledger", seed: int | None = None,
             name: str | None = None, notes: str = "") -> dict:
    """Build a full dossier. Contradiction is the engine of interest: the mask
    is chosen so it cannot protect the competence, and the loyalty shape is
    chosen so it guarantees the fear arrives."""
    lex = store.load(store.LEXICON)
    reg = registry()
    seed = seed if seed is not None else random.randrange(1 << 30)
    rng = random.Random(seed)

    wound = _pick(rng, lex, "wound")
    lie = _pick(rng, lex, "lie")
    mask = _pick(rng, lex, "mask")
    competence = _pick(rng, lex, "competence")
    second_competence = _pick(rng, lex, "competence")
    while second_competence["id"] == competence["id"]:
        second_competence = _pick(rng, lex, "competence")
    hole = _pick(rng, lex, "incompetence")
    tic = _pick(rng, lex, "verbal_tic")
    signature = _pick(rng, lex, "physical_signature")
    loyalty = _pick(rng, lex, "loyalty_shape")
    fear = _pick(rng, lex, "fear")
    axis = _pick(rng, lex, "moral_axis")
    offstage = _pick(rng, lex, "offstage_life")
    shape = _pick(rng, lex, "arc_shape")
    pretext = _pick(rng, lex, "entry_pretext")

    name = name or make_name(rng, culture, reg)
    cid = f"{store.slugify(name)}"

    return {
        "id": cid,
        "name": name,
        "role": role,
        "culture": culture,
        "status": "dormant",
        "seed": seed,
        "created": date.today().isoformat(),
        "need_that_licenses": need,
        "story_function": ROLE_FUNCTIONS.get(role, "to be defined before introduction"),
        "core": {
            "wound": wound["text"],
            "lie": lie["text"],
            "want": f"to secure a position where they can never again be {fear['text']}",
            "need": f"to be met on the axis of {axis['text']} and survive the answer",
            "fear": fear["text"],
            "moral_axis": axis["text"],
        },
        "surface": {
            "mask": mask["text"],
            "verbal_tic": tic["text"],
            "physical_signature": signature["text"],
        },
        "capability": {
            "spike": competence["text"],
            "secondary": second_competence["text"],
            "hole": hole["text"],
        },
        "bonds": {
            "loyalty_shape": loyalty["text"],
            "to_protagonist": "undefined — set on first shared scene",
            "leverage_over_them": f"knowledge that they {offstage['text']}",
            "leverage_they_hold": "undefined",
        },
        "offstage_life": offstage["text"],
        "trajectory": {
            "arc_shape": shape["text"],
            "break_point": "undefined — name the scene that cracks them",
            "exit_condition": "undefined — how they leave the novel, on or off the page",
        },
        "contract": {
            "entry_pretext": pretext["text"],
            "first_appearance_conditions": [
                "The scene must need them for a reason the reader already feels.",
                "They arrive mid-action, doing their own business, not waiting to be met.",
                "One concrete detail from `surface` lands in the first three lines.",
            ],
            "do_not_reveal_before": "the wound; it is earned, never introduced",
        },
        "contradictions": [
            f"The mask ({mask['text']}) cannot protect the spike ({competence['text']}) when it is tested in public.",
            f"Their loyalty ({loyalty['text']}) guarantees they will meet the thing they fear: {fear['text']}.",
            f"The lie — {lie['text']} — will look true for most of their time on the page.",
        ],
        "notes": notes,
        "chapters": [],
        "introduced_chapter": None,
        "file": f"characters/dormant/{cid}.md",
    }


def dossier_markdown(c: dict) -> str:
    def block(title, pairs):
        lines = [f"## {title}", ""]
        for k, v in pairs:
            lines.append(f"- **{k}:** {v}")
        lines.append("")
        return "\n".join(lines)

    out = [
        f"# {c['name']}",
        "",
        f"`{c['id']}` · role: **{c['role']}** · culture: {c['culture']} · status: **{c['status']}** · seed: `{c['seed']}`",
        "",
        f"> **Need that licenses them:** {c['need_that_licenses']}",
        f"> **Story function:** {c['story_function']}",
        "",
        block("Core", [
            ("Wound", c["core"]["wound"]),
            ("Lie", c["core"]["lie"]),
            ("Want (conscious)", c["core"]["want"]),
            ("Need (unconscious)", c["core"]["need"]),
            ("Fear", c["core"]["fear"]),
            ("Moral axis", c["core"]["moral_axis"]),
        ]),
        block("Surface — what the reader meets first", [
            ("Mask", c["surface"]["mask"]),
            ("Verbal tic", c["surface"]["verbal_tic"]),
            ("Physical signature", c["surface"]["physical_signature"]),
        ]),
        block("Capability", [
            ("Spike", c["capability"]["spike"]),
            ("Secondary", c["capability"]["secondary"]),
            ("Hole", c["capability"]["hole"]),
        ]),
        block("Bonds", [
            ("Loyalty shape", c["bonds"]["loyalty_shape"]),
            ("To the protagonist", c["bonds"]["to_protagonist"]),
            ("Leverage over them", c["bonds"]["leverage_over_them"]),
            ("Leverage they hold", c["bonds"]["leverage_they_hold"]),
        ]),
        block("Offstage life — what they are doing in chapters they do not appear in", [
            ("Ongoing", c["offstage_life"]),
        ]),
        block("Trajectory", [
            ("Arc shape", c["trajectory"]["arc_shape"]),
            ("Break point", c["trajectory"]["break_point"]),
            ("Exit condition", c["trajectory"]["exit_condition"]),
        ]),
        "## Introduction contract",
        "",
        f"- **Entry pretext:** {c['contract']['entry_pretext']}",
        "- **First appearance must satisfy:**",
    ]
    for cond in c["contract"]["first_appearance_conditions"]:
        out.append(f"  - {cond}")
    out += [
        f"- **Do not reveal before earned:** {c['contract']['do_not_reveal_before']}",
        "",
        "## Contradictions to play",
        "",
    ]
    out += [f"{i}. {t}" for i, t in enumerate(c["contradictions"], 1)]
    out += ["", "## Voice sample", "", "_Write three lines of their dialogue here before their first scene._", "",
            "## Appearances", "", "_Updated by `novel.py character touch`._", ""]
    if c.get("notes"):
        out += ["## Notes", "", c["notes"], ""]
    return "\n".join(out)


def persist(c: dict) -> str:
    reg = registry()
    if find(reg, c["id"]):
        raise ValueError(f"character id already exists: {c['id']}")
    store.write_text(store.ROOT / c["file"], dossier_markdown(c))
    reg["characters"].append(c)
    save_registry(reg)
    return c["file"]


def introduce(cid: str, *, need: str, chapter: int | None = None, override: bool = False) -> dict:
    ctx = engine.context()
    state = ctx["state"]
    chapter = chapter or state["current_chapter"]
    reg = registry()
    c = find(reg, cid)
    if not c:
        raise ValueError(f"unknown character: {cid}")
    if c["status"] == "active":
        raise ValueError(f"{cid} is already in the live cast (chapter {c['introduced_chapter']})")

    ok_role, role_reason = engine.licensed_for_arc(ctx, "character", c["role"])
    ok_budget, budget_reasons = engine.introduction_check(ctx, "characters", chapter)
    problems = ([] if ok_role else [role_reason]) + ([] if ok_budget else budget_reasons)
    if problems and not override:
        raise PermissionError(
            "introduction refused:\n  - " + "\n  - ".join(problems)
            + "\n  Re-run with --override and the engine will log the exception."
        )

    old = store.ROOT / c["file"]
    c["status"] = "active"
    c["introduced_chapter"] = chapter
    c["need_that_licenses"] = need
    c["file"] = f"characters/cast/{c['id']}.md"
    c.setdefault("chapters", []).append(chapter)
    new = store.ROOT / c["file"]
    text = old.read_text(encoding="utf-8") if old.exists() else dossier_markdown(c)
    text = text.replace("status: **dormant**", f"status: **active** (ch. {chapter})")
    store.write_text(new, text)
    if old.exists() and old != new:
        old.unlink()
    save_registry(reg)

    state["active_characters"] = sorted(set(state.get("active_characters", []) + [c["id"]]))
    state["introductions_this_arc"]["characters"] = state["introductions_this_arc"].get("characters", 0) + 1
    state["introductions_this_chapter"]["characters"] = state["introductions_this_chapter"].get("characters", 0) + 1
    if c["role"] in ("patron", "antagonist", "mentor", "the-one-who-stays"):
        cooldown = ctx["tempo"]["introduction_budget"]["cooldown_chapters_after_major_introduction"]
        state["cooldown_until_chapter"] = chapter + cooldown
    engine.log(state, f"introduced {c['name']} ({c['role']}) in ch.{chapter}"
                      + (" [OVERRIDE: " + "; ".join(problems) + "]" if problems else "")
                      + f" — need: {need}")
    store.save(store.STATE, state)
    return c
