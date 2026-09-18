"""Consistency checks across the bible, the engine, and the registries.

Errors are contradictions the novel cannot survive. Warnings are debts.
"""

from __future__ import annotations

from . import characters, continuity, engine, environments, store


def run() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    ctx = engine.context()
    state, prog, arcs, tempo = ctx["state"], ctx["progression"], ctx["arcs"], ctx["tempo"]
    chapter = state["current_chapter"]

    # --- files and registries agree -------------------------------------
    creg = characters.registry()
    ereg = environments.registry()
    for c in creg["characters"]:
        if not (store.ROOT / c["file"]).exists():
            errors.append(f"character '{c['id']}' registry points at missing file {c['file']}")
        expected_dir = "cast" if c["status"] == "active" else "dormant"
        if f"/{expected_dir}/" not in c["file"]:
            errors.append(f"character '{c['id']}' is {c['status']} but filed under {c['file']}")
    for e in ereg["environments"]:
        if not (store.ROOT / e["file"]).exists():
            errors.append(f"environment '{e['id']}' registry points at missing file {e['file']}")
        expected_dir = "active" if e["status"] == "active" else "dormant"
        if f"/{expected_dir}/" not in e["file"]:
            errors.append(f"environment '{e['id']}' is {e['status']} but filed under {e['file']}")

    names = {}
    for c in creg["characters"]:
        key = c["name"].lower()
        if key in names:
            errors.append(f"duplicate character name '{c['name']}' ({names[key]} and {c['id']})")
        names[key] = c["id"]

    # --- state agrees with registries -----------------------------------
    active_ids = {c["id"] for c in creg["characters"] if c["status"] == "active"}
    for cid in state.get("active_characters", []):
        if cid not in active_ids:
            errors.append(f"state lists '{cid}' as active, registry does not")
    for cid in active_ids - set(state.get("active_characters", [])):
        warnings.append(f"registry marks '{cid}' active but state does not list them on stage")

    active_envs = {e["id"] for e in ereg["environments"] if e["status"] == "active"}
    for eid in state.get("active_environments", []):
        if eid not in active_envs:
            errors.append(f"state lists environment '{eid}' as active, registry does not")

    # --- progression discipline ------------------------------------------
    for name, track in prog["tracks"]["capability"].items():
        ceiling = engine.capability_ceiling(chapter, arcs, state["current_arc"], track.get("start", 0))
        if track["value"] > ceiling:
            errors.append(
                f"capability '{name}' is {track['value']} but the ceiling at chapter {chapter} is {ceiling} "
                "(rule: growth may not exceed start + chapter/6 before Act III)"
            )
        if track["value"] > track.get("ceiling", 10):
            errors.append(f"capability '{name}' exceeds its own ceiling")
    lie = prog["tracks"]["internal"]["lie_grip"]["value"]
    sk = prog["tracks"]["internal"]["self_knowledge"]["value"]
    if lie + sk != 10:
        errors.append(f"mirror rule broken: lie_grip {lie} + self_knowledge {sk} must equal 10")

    for gid in state.get("gates_passed", []):
        if not any(g["id"] == gid for g in prog["gates"]):
            errors.append(f"state records passing unknown gate '{gid}'")

    # --- continuity -------------------------------------------------------
    ts = engine.thread_status(ctx, chapter)
    for th, age in ts["rotting"]:
        errors.append(f"thread '{th['id']}' has been open {age} chapters "
                      f"(hard max {tempo['seed_policy']['payoff_window_chapters']['hard_max']}): {th['summary']}")
    if ts["overfull"]:
        warnings.append(f"{len(ts['open'])} open threads exceeds max_open_seeds {tempo['seed_policy']['max_open_seeds']}")

    idx = continuity.index()
    recorded = {c["chapter"] for c in idx["chapters"]}
    for n in range(1, chapter):
        if n not in recorded:
            warnings.append(f"chapter {n} is written but has no continuity record (`novel.py chapter record {n}`)")

    locks = {l["id"] for l in store.load(store.CANON, {"locks": []})["locks"]}
    for ch in idx["chapters"]:
        for p in ch.get("load_bearing", []):
            if p.get("lock") and p["lock"] not in locks:
                errors.append(f"chapter {ch['chapter']} point {p['id']} cites unknown canon lock '{p['lock']}'")

    thread_ids = {th["id"] for th in continuity.threads()["threads"]}
    for ch in idx["chapters"]:
        for tid in ch.get("seeds_planted", []) + ch.get("seeds_paid", []):
            if tid not in thread_ids:
                errors.append(f"chapter {ch['chapter']} references unknown thread '{tid}'")

    # --- arc licensing ----------------------------------------------------
    arc = engine.arc_for_chapter(arcs, chapter)
    for e in ereg["environments"]:
        if e["status"] == "active" and e["type"] not in arc.get("licensed_environments", []):
            warnings.append(f"environment '{e['id']}' ({e['type']}) is on stage but arc {arc['id']} "
                            f"licenses {arc.get('licensed_environments', [])} — intentional carry-over?")

    # --- dormant inventory health ----------------------------------------
    dormant_chars = [c for c in creg["characters"] if c["status"] == "dormant"]
    if len(dormant_chars) > 25:
        warnings.append(f"{len(dormant_chars)} dormant characters: the bench is bigger than the book")

    return errors, warnings
