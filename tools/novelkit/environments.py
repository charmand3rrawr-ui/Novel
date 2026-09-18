"""Environment creation.

Same contract as characters: built deep, held dormant, activated only when the
storyline needs a stage it does not already have. A setting that exists but has
never been needed is not a failure — it is inventory.
"""

from __future__ import annotations

import random
from datetime import date

from . import engine, store

PALETTE = store.ENVIRONMENTS / "palette.json"


def registry() -> dict:
    return store.load(store.ENV_REGISTRY, {"environments": []})


def save_registry(reg: dict) -> None:
    store.save(store.ENV_REGISTRY, reg)


def find(reg: dict, eid: str):
    for e in reg["environments"]:
        if e["id"] == eid:
            return e
    return None


def generate(env_type: str, *, need: str, name: str | None = None, seed: int | None = None,
             parent: str = "", notes: str = "") -> dict:
    pal = store.load(PALETTE)
    if env_type not in pal["types"]:
        raise ValueError(f"unknown environment type '{env_type}'. Known: {', '.join(sorted(pal['types']))}")
    spec = pal["types"][env_type]
    seed = seed if seed is not None else random.randrange(1 << 30)
    rng = random.Random(seed)

    name = name or _make_place_name(rng, env_type)
    eid = store.slugify(f"{env_type}-{name}")

    return {
        "id": eid,
        "name": name,
        "type": env_type,
        "scale": spec["scale"],
        "parent": parent,
        "status": "dormant",
        "seed": seed,
        "created": date.today().isoformat(),
        "need_that_licenses": need,
        "function": spec["function"],
        "power_structure": spec["power"],
        "sensory_signature": rng.choice(pal["sensory_signature"]),
        "access_rule": rng.choice(pal["access_rule"]),
        "hazards": spec["default_hazards"],
        "secret": rng.choice(pal["secret"]),
        "change_over_time": rng.choice(pal["change_over_time"]),
        "affordances": rng.sample(pal["affordances"], k=min(3, len(pal["affordances"]))),
        "economy": "undefined — who pays, who is paid, and in what",
        "factions_present": [],
        "resident_characters": [],
        "entry_condition": need,
        "exit_condition": "undefined — what closes this stage for the story",
        "continuity_hooks": [],
        "chapters": [],
        "activated_chapter": None,
        "file": f"environments/dormant/{eid}.md",
        "notes": notes,
    }


PLACE_PARTS = {
    "first": ["Thorn", "Ash", "Grey", "Salt", "Iron", "Cinder", "Wick", "Marrow", "Harrow", "Pale", "Bright", "Hollow", "Stil"],
    "second": ["Ledger", "Gate", "Reach", "Quay", "Verge", "Spire", "Warren", "Hold", "Landing", "Cross", "Mire", "Terrace"],
}


def _make_place_name(rng: random.Random, env_type: str) -> str:
    first = rng.choice(PLACE_PARTS["first"])
    second = rng.choice(PLACE_PARTS["second"])
    if env_type in ("orbital-station", "moon-settlement", "planet-frontier"):
        return f"{first} {second} {rng.choice(['Station', 'Settlement', 'Landing', 'Array'])}"
    return f"{first} {second}"


def dossier_markdown(e: dict) -> str:
    lines = [
        f"# {e['name']}",
        "",
        f"`{e['id']}` · type: **{e['type']}** · scale: {e['scale']} · status: **{e['status']}** · seed: `{e['seed']}`",
        "",
        f"> **Need that licenses it:** {e['need_that_licenses']}",
        "",
        "## What it is for",
        "",
        f"- **Function in the world:** {e['function']}",
        f"- **Power structure:** {e['power_structure']}",
        f"- **Economy:** {e['economy']}",
        f"- **Access rule:** {e['access_rule']}",
        "",
        "## On the page",
        "",
        f"- **Sensory signature:** {e['sensory_signature']}",
        "- **Hazards:**",
    ]
    lines += [f"  - {h}" for h in e["hazards"]]
    lines += ["- **Scene affordances — what this stage makes possible:**"]
    lines += [f"  - {a}" for a in e["affordances"]]
    lines += [
        "",
        "## Under the surface",
        "",
        f"- **Secret:** {e['secret']}",
        f"- **How it changes across the novel:** {e['change_over_time']}",
        f"- **Parent location:** {e['parent'] or '_none recorded_'}",
        "",
        "## Contract",
        "",
        f"- **Entry condition:** {e['entry_condition']}",
        f"- **Exit condition:** {e['exit_condition']}",
        "",
        "## Residents and factions",
        "",
        "_Populate only with characters the story has already needed._",
        "",
        "## Continuity hooks",
        "",
        "_Details established on the page that later chapters must respect._",
        "",
    ]
    if e.get("notes"):
        lines += ["## Notes", "", e["notes"], ""]
    return "\n".join(lines)


def persist(e: dict) -> str:
    reg = registry()
    if find(reg, e["id"]):
        raise ValueError(f"environment id already exists: {e['id']}")
    store.write_text(store.ROOT / e["file"], dossier_markdown(e))
    reg["environments"].append(e)
    save_registry(reg)
    return e["file"]


def activate(eid: str, *, need: str, chapter: int | None = None, override: bool = False) -> dict:
    ctx = engine.context()
    state = ctx["state"]
    chapter = chapter or state["current_chapter"]
    reg = registry()
    e = find(reg, eid)
    if not e:
        raise ValueError(f"unknown environment: {eid}")
    if e["status"] == "active":
        raise ValueError(f"{eid} is already on stage (since chapter {e['activated_chapter']})")

    ok_type, type_reason = engine.licensed_for_arc(ctx, "environment", e["type"])
    ok_budget, budget_reasons = engine.introduction_check(ctx, "environments", chapter)
    problems = ([] if ok_type else [type_reason]) + ([] if ok_budget else budget_reasons)
    if problems and not override:
        raise PermissionError(
            "activation refused:\n  - " + "\n  - ".join(problems)
            + "\n  Re-run with --override and the engine will log the exception."
        )

    old = store.ROOT / e["file"]
    e["status"] = "active"
    e["activated_chapter"] = chapter
    e["entry_condition"] = need
    e["file"] = f"environments/active/{e['id']}.md"
    e.setdefault("chapters", []).append(chapter)
    new = store.ROOT / e["file"]
    text = old.read_text(encoding="utf-8") if old.exists() else dossier_markdown(e)
    text = text.replace("status: **dormant**", f"status: **active** (ch. {chapter})")
    store.write_text(new, text)
    if old.exists() and old != new:
        old.unlink()
    save_registry(reg)

    state["active_environments"] = sorted(set(state.get("active_environments", []) + [e["id"]]))
    state["introductions_this_arc"]["environments"] = state["introductions_this_arc"].get("environments", 0) + 1
    state["introductions_this_chapter"]["environments"] = state["introductions_this_chapter"].get("environments", 0) + 1
    engine.log(state, f"activated environment {e['name']} ({e['type']}) in ch.{chapter}"
                      + (" [OVERRIDE: " + "; ".join(problems) + "]" if problems else "")
                      + f" — need: {need}")
    store.save(store.STATE, state)
    return e
