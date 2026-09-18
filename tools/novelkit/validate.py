"""Consistency checks across the bible, the engine, and the registries.

Errors are contradictions the novel cannot survive. Warnings are debts.
"""

from __future__ import annotations

from . import characters, continuity, engine, environments, store, system


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

    # --- the protagonist's system ---------------------------------------
    try:
        scfg, sst = system.config(), system.status()
    except FileNotFoundError:
        scfg = sst = None
    if sst:
        if sst["owner"] != prog.get("protagonist"):
            errors.append(f"system owner '{sst['owner']}' is not progression.json's protagonist "
                          f"'{prog.get('protagonist')}'")
        pts = sst["points"]
        if pts["lifetime_earned"] != pts["spent"] + pts["unspent"]:
            errors.append(f"point accounting broken: {pts['lifetime_earned']} earned != "
                          f"{pts['spent']} spent + {pts['unspent']} unspent")
        expected = system.residue_state(scfg, sst["residue"]["value"])
        if sst["residue"]["state"] != expected:
            errors.append(f"residue is {sst['residue']['value']} but state says "
                          f"'{sst['residue']['state']}' (should be '{expected}')")
        if sst["residue"]["value"] >= 75:
            warnings.append(f"residue {sst['residue']['value']}: a deviation event is due on the page")

        gap = system.realm_gap(scfg, sst, sst["realm"]["n"])
        if gap:
            warnings.append(f"current realm {sst['realm']['name']} is held without meeting "
                            + ", ".join(gap) + " (an override, or the numbers drifted)")
        realm = next((r for r in scfg["realms"] if r["n"] == sst["realm"]["n"]), None)
        if realm and sst["realm"]["stage"] not in realm["stages"]:
            errors.append(f"realm stage '{sst['realm']['stage']}' is not a stage of {realm['name']} "
                          f"({', '.join(realm['stages'])})")

        known_traits = {tr["id"] for tr in scfg["traits"]}
        for rec in sst["traits"]:
            if rec["id"] not in known_traits:
                errors.append(f"status carries unknown trait '{rec['id']}'")
            if rec["state"] not in scfg["trait_states"]:
                errors.append(f"trait '{rec['id']}' has invalid state '{rec['state']}'")
        for disc, rating in sst["talents"].items():
            if disc not in scfg["talents"]["disciplines"]:
                errors.append(f"talent recorded for unknown discipline '{disc}'")
            if rating not in scfg["talents"]["scale"]:
                errors.append(f"talent '{disc}' has invalid rating '{rating}'")
        for name, rec in sst["professions"].items():
            if name not in scfg["professions"]["disciplines"]:
                errors.append(f"unknown profession '{name}' in status")
                continue
            if rec.get("build_credits_taken", 0) > rec["proficiency"] // 10:
                errors.append(f"profession '{name}' has taken {rec['build_credits_taken']} build credits "
                              f"but only earned {rec['proficiency'] // 10}")
            expected_rank = system.rank_for(scfg, rec["proficiency"])["rank"]
            if rec.get("rank", 0) != expected_rank:
                errors.append(f"profession '{name}' is rank {rec.get('rank')} at "
                              f"{rec['proficiency']} proficiency (should be {expected_rank})")
        for tq in sst["techniques"]:
            if not 0 <= tq["proficiency"] <= 100:
                errors.append(f"technique '{tq['name']}' proficiency {tq['proficiency']} is outside 0-100")

        caps = scfg["absorption_rules"]["caps"]
        if sst["per_chapter"]["points"] > caps["points_per_chapter_hard"]:
            warnings.append(f"chapter {sst['per_chapter']['chapter']} absorbed "
                            f"{sst['per_chapter']['points']} points, over the hard cap "
                            f"{caps['points_per_chapter_hard']} (overridden)")
        if sst["per_arc"]["points"] > caps["points_per_arc_hard"]:
            warnings.append(f"arc {sst['per_arc']['arc']} absorbed {sst['per_arc']['points']} points, "
                            f"over the hard cap {caps['points_per_arc_hard']} (overridden)")
        for e in sst["absorption_log"]:
            if not e.get("who_paid"):
                errors.append(f"absorption in chapter {e['chapter']} names nobody who paid (LK-MOTE-COSTS)")
            if not e.get("scene"):
                errors.append(f"absorption in chapter {e['chapter']} has no scene (witness rule)")
        unwritten = [e for e in sst["absorption_log"] if e["chapter"] > chapter]
        if unwritten:
            warnings.append(f"{len(unwritten)} absorption(s) logged for chapters not yet written")

    return errors, warnings
