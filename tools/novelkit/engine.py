"""The novel engine: tempo, arc position, chapter obligations, and the gates
that ration main-character progression.

The engine never writes prose. It answers one question well: given where the
story is, what does the next chapter owe the reader, and what is it forbidden
to spend?
"""

from __future__ import annotations

from datetime import date

from . import store


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------

def context():
    return {
        "tempo": store.load(store.TEMPO),
        "arcs": store.load(store.ARCS),
        "progression": store.load(store.PROGRESSION),
        "state": store.load(store.STATE),
        "threads": store.load(store.THREADS, {"threads": []}),
        "chapter_index": store.load(store.CHAPTER_INDEX, {"chapters": []}),
    }


# --------------------------------------------------------------------------
# arc position
# --------------------------------------------------------------------------

def arc_for_chapter(arcs: dict, chapter: int) -> dict:
    for arc in arcs["arcs"]:
        lo, hi = arc["chapters"]
        if lo <= chapter <= hi:
            return arc
    return arcs["arcs"][-1]


def act_for_arc(arcs: dict, arc_id: str) -> str:
    for act in arcs["acts"]:
        if arc_id in act["arcs"]:
            return act["id"]
    return "ACT?"


def arc_progress(arc: dict, chapter: int) -> float:
    lo, hi = arc["chapters"]
    span = max(1, hi - lo)
    return min(1.0, max(0.0, (chapter - lo) / span))


# --------------------------------------------------------------------------
# tempo
# --------------------------------------------------------------------------

def beat_for_chapter(tempo: dict, chapter: int) -> str:
    cycle = tempo["beat_cycle"]
    return cycle[(chapter - 1) % len(cycle)]


def is_rest_chapter(tempo: dict, chapter: int) -> bool:
    every = tempo["cadence_rules"]["rest_chapter_every"]
    return every > 0 and chapter % every == 0


def is_revelation_due(tempo: dict, state: dict) -> bool:
    return state.get("chapters_since_revelation", 0) >= tempo["cadence_rules"]["revelation_every"] - 1


def tension_target(tempo: dict, arc: dict, chapter: int) -> int:
    """Sawtooth: rise toward the arc peak at three-quarter depth, settle to the
    arc close, then cut on rest chapters so the reader can breathe."""
    t = arc["tension"]
    p = arc_progress(arc, chapter)
    if p <= 0.75:
        base = t["open"] + (t["peak"] - t["open"]) * (p / 0.75)
    else:
        base = t["peak"] + (t["close"] - t["peak"]) * ((p - 0.75) / 0.25)
    if is_rest_chapter(tempo, chapter):
        base -= tempo["tension_curve"]["release_depth"]
    curve = tempo["tension_curve"]
    return int(max(curve["arc_floor"], min(curve["arc_ceiling"], round(base))))


# --------------------------------------------------------------------------
# introduction budgets - the just-in-time casting rule
# --------------------------------------------------------------------------

def introduction_check(ctx: dict, kind: str, chapter: int | None = None) -> tuple[bool, list[str]]:
    """kind is 'characters' or 'environments'. Returns (allowed, reasons)."""
    tempo, state = ctx["tempo"], ctx["state"]
    chapter = chapter or state["current_chapter"]
    budget = tempo["introduction_budget"]
    per_arc = budget["named_characters_per_arc"] if kind == "characters" else budget["environments_per_arc"]
    per_ch = budget["named_characters_per_chapter"] if kind == "characters" else budget["environments_per_chapter"]

    reasons = []
    used_arc = state["introductions_this_arc"].get(kind, 0)
    used_ch = state["introductions_this_chapter"].get(kind, 0)
    if used_arc >= per_arc:
        reasons.append(f"arc budget spent: {used_arc}/{per_arc} {kind} already introduced in {state['current_arc']}")
    if used_ch >= per_ch:
        reasons.append(f"chapter budget spent: {used_ch}/{per_ch} {kind} already introduced in chapter {chapter}")
    if chapter < state.get("cooldown_until_chapter", 0):
        reasons.append(f"cooldown active until chapter {state['cooldown_until_chapter']} after a major introduction")
    return (not reasons), reasons


def licensed_for_arc(ctx: dict, kind: str, value: str) -> tuple[bool, str]:
    """Is this environment type / character role licensed by the current arc?"""
    arc = arc_for_chapter(ctx["arcs"], ctx["state"]["current_chapter"])
    key = "licensed_environments" if kind == "environment" else "licensed_character_roles"
    allowed = arc.get(key, [])
    if not allowed or value in allowed:
        return True, ""
    return False, f"arc {arc['id']} licenses {allowed}; '{value}' is outside it"


# --------------------------------------------------------------------------
# seeds and threads
# --------------------------------------------------------------------------

def thread_status(ctx: dict, chapter: int | None = None) -> dict:
    tempo = ctx["tempo"]
    chapter = chapter or ctx["state"]["current_chapter"]
    window = tempo["seed_policy"]["payoff_window_chapters"]
    open_threads, ripe, rotting, overfull = [], [], [], False
    for th in ctx["threads"].get("threads", []):
        if th.get("status") != "open":
            continue
        open_threads.append(th)
        age = chapter - int(th.get("planted_chapter", chapter))
        if age >= window["hard_max"]:
            rotting.append((th, age))
        elif age >= window["soft_max"]:
            ripe.append((th, age))
        elif age >= window["min"]:
            ripe.append((th, age))
    overfull = len(open_threads) > tempo["seed_policy"]["max_open_seeds"]
    return {"open": open_threads, "payable": ripe, "rotting": rotting, "overfull": overfull}


# --------------------------------------------------------------------------
# progression gates
# --------------------------------------------------------------------------

def track_value(prog: dict, name: str):
    for group in prog["tracks"].values():
        if name in group:
            return group[name]["value"]
    return None


def capability_ceiling(chapter: int, arcs: dict, arc_id: str, start: int = 0) -> int:
    """Growth is rationed against the page count. A track may sit at its starting
    value forever, but it may not climb faster than the story earns it."""
    if act_for_arc(arcs, arc_id) in ("ACT3", "V6", "M4"):
        return 10
    return min(10, start + int(chapter / 34) + 1)


def gate_report(ctx: dict) -> dict:
    prog, state = ctx["progression"], ctx["state"]
    passed = set(state.get("gates_passed", []))
    ready, blocked, done = [], [], []
    for gate in prog["gates"]:
        if gate["id"] in passed:
            done.append(gate)
            continue
        missing = []
        for req, need in gate.get("requires", {}).items():
            if req.endswith("_at_most"):
                have = track_value(prog, req[: -len("_at_most")])
                if have is None or have > need:
                    missing.append(f"{req[:-len('_at_most')]} {have} > {need}")
            else:
                have = track_value(prog, req)
                if have is None or have < need:
                    missing.append(f"{req} {have}/{need}")
        (ready if not missing else blocked).append({**gate, "missing": missing})
    return {"ready": ready, "blocked": blocked, "passed": done}


# --------------------------------------------------------------------------
# the chapter plan
# --------------------------------------------------------------------------

def plan(ctx: dict, chapter: int | None = None) -> dict:
    tempo, state, arcs = ctx["tempo"], ctx["state"], ctx["arcs"]
    chapter = chapter or state["current_chapter"]
    arc = arc_for_chapter(arcs, chapter)
    beat = beat_for_chapter(tempo, chapter)
    rest = is_rest_chapter(tempo, chapter)
    threads = thread_status(ctx, chapter)
    gates = gate_report(ctx)

    obligations = []
    obligations.append(f"Beat: {beat} — {tempo['beat_definitions'][beat]}")
    obligations.append(f"Tension target: {tension_target(tempo, arc, chapter)}/10")
    if rest:
        obligations.append("REST chapter: no capability track may rise. Recover intimacy or body by at most 1.")
    if is_revelation_due(tempo, state):
        obligations.append(
            f"REVELATION DUE: {state['chapters_since_revelation']} chapters since the last one "
            f"(cadence {tempo['cadence_rules']['revelation_every']}). It must cash a seed at least "
            f"{tempo['seed_policy']['payoff_window_chapters']['min']} chapters old."
        )
    obligations.append(
        f"Plant at least {tempo['seed_policy']['min_seeds_planted_per_chapter']} seed(s): "
        "record with `novel.py seed plant`."
    )
    if threads["rotting"]:
        for th, age in threads["rotting"]:
            obligations.append(f"ROT: thread '{th['id']}' open {age} chapters — pay, repurpose, or retire it on the page.")
    if threads["overfull"]:
        obligations.append(
            f"{len(threads['open'])} open threads exceeds max_open_seeds "
            f"({tempo['seed_policy']['max_open_seeds']}). Close before planting."
        )
    if state.get("consecutive_action_chapters", 0) >= tempo["cadence_rules"]["max_consecutive_action_chapters"]:
        obligations.append("Action saturation reached: this chapter must be consequence or quiet.")
    if state.get("consecutive_low_tension_chapters", 0) >= tempo["cadence_rules"]["max_consecutive_low_tension_chapters"]:
        obligations.append("Two quiet chapters have run: raise the floor or lose the reader.")

    ch_ok, ch_reasons = introduction_check(ctx, "characters", chapter)
    env_ok, env_reasons = introduction_check(ctx, "environments", chapter)

    return {
        "chapter": chapter,
        "act": act_for_arc(arcs, arc["id"]),
        "arc": arc["id"],
        "arc_name": arc["name"],
        "central_question": arc["central_question"],
        "pressure_source": arc["pressure_source"],
        "beat": beat,
        "rest": rest,
        "tension_target": tension_target(tempo, arc, chapter),
        "word_target": tempo["chapter_target_words"]["ideal"],
        "obligations": obligations,
        "payable_threads": [{"id": t["id"], "age": a, "summary": t.get("summary", "")} for t, a in threads["payable"]],
        "open_thread_count": len(threads["open"]),
        "may_introduce_character": ch_ok,
        "character_block_reasons": ch_reasons,
        "may_introduce_environment": env_ok,
        "environment_block_reasons": env_reasons,
        "licensed_roles": arc.get("licensed_character_roles", []),
        "licensed_environments": arc.get("licensed_environments", []),
        "capability_ceiling": {
            name: capability_ceiling(chapter, arcs, arc["id"], tr.get("start", 0))
            for name, tr in ctx["progression"]["tracks"]["capability"].items()
        },
        "gates_ready": [{"id": g["id"], "name": g["name"]} for g in gates["ready"] if g.get("arc") == arc["id"]],
        "gates_blocked": [
            {"id": g["id"], "name": g["name"], "missing": g["missing"]}
            for g in gates["blocked"] if g.get("arc") == arc["id"]
        ],
        "active_characters": state.get("active_characters", []),
        "active_environments": state.get("active_environments", []),
    }


# --------------------------------------------------------------------------
# state mutation
# --------------------------------------------------------------------------

def log(state: dict, message: str) -> None:
    state.setdefault("log", []).append({"date": date.today().isoformat(), "chapter": state["current_chapter"], "event": message})
    state["log"] = state["log"][-400:]


def close_chapter(ctx: dict, *, tension: int, kind: str, revelation: bool) -> dict:
    """Advance the metronome by one chapter."""
    tempo, state, arcs = ctx["tempo"], ctx["state"], ctx["arcs"]
    chapter = state["current_chapter"]
    old_arc = state["current_arc"]

    state["last_tension"] = tension
    state["chapters_since_rest"] = 0 if is_rest_chapter(tempo, chapter) else state.get("chapters_since_rest", 0) + 1
    state["chapters_since_revelation"] = 0 if revelation else state.get("chapters_since_revelation", 0) + 1
    state["consecutive_action_chapters"] = state.get("consecutive_action_chapters", 0) + 1 if kind == "conflict" else 0
    state["consecutive_low_tension_chapters"] = state.get("consecutive_low_tension_chapters", 0) + 1 if tension <= 3 else 0

    state["current_chapter"] = chapter + 1
    new_arc = arc_for_chapter(arcs, state["current_chapter"])
    state["current_arc"] = new_arc["id"]
    state["introductions_this_chapter"] = {"characters": 0, "environments": 0}
    if new_arc["id"] != old_arc:
        state["introductions_this_arc"] = {"characters": 0, "environments": 0}
        log(state, f"arc transition {old_arc} -> {new_arc['id']} ({new_arc['name']}); introduction budgets reset")
    log(state, f"closed chapter {chapter} (tension {tension}, kind {kind}, revelation={revelation})")
    store.save(store.STATE, state)
    return state
