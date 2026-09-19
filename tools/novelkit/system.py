"""The protagonist's system: attributes, absorption, realms, traits, professions.

Two files back this module:

- `engine/system.json`        — how the system works (rules, rarely changes)
- `engine/system-status.json` — where the protagonist is (state and log)

The rules that matter are the ones that refuse: familiarity decay so grinding
one source stops paying, per-chapter and per-arc point caps so power cannot
outrun the page count, residue so tainted sources carry a bill, and the witness
rule — nothing is absorbed that did not happen in a scene, and nothing is
absorbed without naming who paid for it (LK-MOTE-COSTS).
"""

from __future__ import annotations

from datetime import date

from . import engine, store

CONFIG = store.ENGINE / "system.json"
STATUS = store.ENGINE / "system-status.json"
SHEET = store.ENGINE / "system-status.md"

PHYSICAL = ("strength", "agility", "reflex", "constitution")
MENTAL = ("perception", "comprehension", "will", "spirit")
RARE = ("fortune", "affinity")


def config() -> dict:
    return store.load(CONFIG)


def status() -> dict:
    return store.load(STATUS)


def save_status(s: dict) -> None:
    store.save(STATUS, s)


# --------------------------------------------------------------------------
# arithmetic
# --------------------------------------------------------------------------

def raise_cost(cfg: dict, attribute: str, frm: int, to: int) -> int:
    """Cost to raise an attribute from one value to another. Cheap early,
    punishing later: 1 + floor(v / 10) per step."""
    mult = cfg["raise_cost_rule"]["rare_multiplier"] if attribute in RARE else 1
    return sum((1 + v // 10) * mult for v in range(frm, to))


def totals(s: dict) -> dict:
    a = s["attributes"]
    return {
        "physical_total": sum(a.get(k, 0) for k in PHYSICAL),
        "mental_total": sum(a.get(k, 0) for k in MENTAL),
        **{k: a.get(k, 0) for k in a},
    }


def residue_state(cfg: dict, value: int) -> str:
    state = "clear"
    for t in cfg["absorption_rules"]["residue"]["thresholds"]:
        if value >= t["at"]:
            state = t["state"]
    return state


def residue_effect(cfg: dict, value: int) -> str:
    effect = ""
    for t in cfg["absorption_rules"]["residue"]["thresholds"]:
        if value >= t["at"]:
            effect = t["effect"]
    return effect


def band_for(cfg: dict, proficiency: int) -> str:
    for b in cfg["proficiency"]["bands"]:
        lo, hi = b["range"]
        if lo <= proficiency <= hi:
            return b["name"]
    return "rote"


def rank_for(cfg: dict, proficiency: int) -> dict:
    current = {"rank": 0, "name": "unranked", "proficiency": 0}
    for r in cfg["professions"]["ranks"]:
        if proficiency >= r["proficiency"]:
            current = r
    return current


def realm_by_n(cfg: dict, n: int) -> dict:
    for r in cfg["realms"]:
        if r["n"] == n:
            return r
    raise ValueError(f"no realm {n}")


# --------------------------------------------------------------------------
# chapter / arc accounting
# --------------------------------------------------------------------------

def _sync_period(s: dict) -> dict:
    """Roll the per-chapter and per-arc counters when the engine has moved on."""
    st = store.load(store.STATE)
    chapter, arc = st["current_chapter"], st["current_arc"]
    if s["per_chapter"].get("chapter") != chapter:
        s["per_chapter"] = {"chapter": chapter, "points": 0}
    if s["per_arc"].get("arc") != arc:
        s["per_arc"] = {"arc": arc, "points": 0}
    return st


# --------------------------------------------------------------------------
# absorption
# --------------------------------------------------------------------------

def absorb(source_class: str, *, scene: str, who_paid: str, tier: int | None = None,
           points: int | None = None, note: str = "", override: bool = False) -> dict:
    cfg, s = config(), status()
    st = _sync_period(s)
    chapter = st["current_chapter"]

    if source_class not in cfg["source_classes"]:
        raise ValueError(f"unknown source class '{source_class}'. Known: {', '.join(cfg['source_classes'])}")
    if not scene.strip():
        raise ValueError("the witness rule: an absorption needs a --scene. If it did not happen on the page, it did not happen.")
    if not who_paid.strip():
        raise ValueError("LK-MOTE-COSTS: name who or what paid for this. Nothing sheds essence without losing it.")

    sc = cfg["source_classes"][source_class]
    tiers = sc["tiers"]
    tier = tier if tier is not None else tiers[len(tiers) // 2]
    if tier not in tiers:
        raise ValueError(f"source class '{source_class}' sheds tiers {tiers}, not {tier}")

    spec = next(t for t in cfg["mote_tiers"] if t["tier"] == tier)
    if tier == 6:
        raise ValueError("tier 6 (sovereign) motes grant a trait state, a talent step, or a technique at Origin band — "
                         "never raw points. Use `system trait`, `system talent`, or `system technique` instead.")

    lo, hi = spec["points"]
    base = points if points is not None else (lo + hi) // 2

    decay_cfg = cfg["absorption_rules"]["familiarity_decay"]
    seen = s["familiarity"].get(source_class, 0)
    mult = 1.0
    if decay_cfg["enabled"]:
        mult = max(decay_cfg["floor"], sc["decay"] ** seen)
    gained = max(1, round(base * mult))

    caps = cfg["absorption_rules"]["caps"]
    ch_points = s["per_chapter"]["points"] + gained
    arc_points = s["per_arc"]["points"] + gained
    problems = []
    if ch_points > caps["points_per_chapter_hard"]:
        problems.append(f"chapter hard cap: {ch_points} > {caps['points_per_chapter_hard']} points in chapter {chapter}")
    if arc_points > caps["points_per_arc_hard"]:
        problems.append(f"arc hard cap: {arc_points} > {caps['points_per_arc_hard']} points in {s['per_arc']['arc']}")
    if problems and not override:
        raise PermissionError(
            "absorption refused:\n  - " + "\n  - ".join(problems)
            + "\n  This is the anti-inflation rail. Re-run with --override and the engine will log the exception."
        )

    taint = sc.get("taint", 0.0)
    residue = round(gained * taint)
    s["residue"]["value"] += residue
    s["residue"]["state"] = residue_state(cfg, s["residue"]["value"])

    s["points"]["unspent"] += gained
    s["points"]["lifetime_earned"] += gained
    s["familiarity"][source_class] = seen + 1
    s["per_chapter"]["points"] = ch_points
    s["per_arc"]["points"] = arc_points
    entry = {
        "chapter": chapter,
        "date": date.today().isoformat(),
        "source_class": source_class,
        "tier": tier,
        "tier_name": spec["name"],
        "base_points": base,
        "decay_multiplier": round(mult, 3),
        "points": gained,
        "residue": residue,
        "scene": scene,
        "who_paid": who_paid,
        "note": note,
        "override": bool(problems),
    }
    s["absorption_log"].append(entry)
    save_status(s)
    return {"entry": entry, "status": s, "soft_cap_hit": ch_points > caps["points_per_chapter_soft"],
            "soft_cap": caps["points_per_chapter_soft"], "warnings": problems}


# --------------------------------------------------------------------------
# spending
# --------------------------------------------------------------------------

def spend(attribute: str, amount: int, *, override: bool = False) -> dict:
    cfg, s = config(), status()
    if attribute not in s["attributes"]:
        raise ValueError(f"unknown attribute '{attribute}'. Known: {', '.join(s['attributes'])}")
    if attribute == "fortune" and not override:
        raise PermissionError(
            "refused: fortune is not bought. It rises almost never, and when it does someone nearby pays for it "
            "(LK-ESSENCE-FINITE, and the Thousand-Coin toll).\n  Use --override if this is that scene."
        )
    frm = s["attributes"][attribute]
    cost = raise_cost(cfg, attribute, frm, frm + amount)
    if cost > s["points"]["unspent"] and not override:
        raise PermissionError(
            f"refused: raising {attribute} {frm} -> {frm + amount} costs {cost} points, "
            f"and {s['points']['unspent']} are unspent."
        )
    s["attributes"][attribute] = frm + amount
    s["points"]["unspent"] -= cost
    s["points"]["spent"] += cost
    save_status(s)
    return {"attribute": attribute, "from": frm, "to": frm + amount, "cost": cost,
            "remaining": s["points"]["unspent"]}


def train(attribute: str, amount: int, *, scene: str, note: str = "") -> dict:
    """Attributes earned by work rather than absorption.

    The system grants these directly — ENDURANCE for carrying, COMPREHENSION for
    argument, a Tempering gate for thirty-one hours at load. They cost no points
    because nothing died for them, which is the whole thematic point: everything
    he earns honestly is slow, and everything he takes is fast.
    """
    cfg, s = config(), status()
    if attribute not in s["attributes"]:
        raise ValueError(f"unknown attribute '{attribute}'. Known: {', '.join(s['attributes'])}")
    if not scene.strip():
        raise ValueError("the witness rule applies to earned gains too: give --scene, or it did not happen")
    st = store.load(store.STATE)
    before = s["attributes"][attribute]
    s["attributes"][attribute] = before + amount
    s["events"].append({"chapter": st["current_chapter"], "kind": "earned",
                        "text": f"{attribute} {before} -> {before + amount} by work", "scene": scene,
                        "note": note})
    save_status(s)
    return {"attribute": attribute, "from": before, "to": before + amount, "scene": scene}


def technique(name: str, *, amount: int = 0, grade: str = "common", spend_points: bool = False,
              scene: str = "") -> dict:
    cfg, s = config(), status()
    tech = next((t for t in s["techniques"] if t["name"].lower() == name.lower()), None)
    if tech is None:
        tech = {"name": name, "grade": grade, "proficiency": 0, "band": "rote"}
        s["techniques"].append(tech)
    before = tech["proficiency"]
    after = max(0, min(100, before + amount))
    cost = 0
    if spend_points and amount > 0:
        cost = amount * cfg["proficiency"]["point_cost_per_step"]
        if cost > s["points"]["unspent"]:
            raise PermissionError(f"refused: {amount} proficiency costs {cost} points, {s['points']['unspent']} unspent.")
        s["points"]["unspent"] -= cost
        s["points"]["spent"] += cost
    before_band, after_band = band_for(cfg, before), band_for(cfg, after)
    tech["proficiency"] = after
    tech["band"] = after_band
    save_status(s)
    return {"name": name, "from": before, "to": after, "cost": cost,
            "band_change": (before_band, after_band) if before_band != after_band else None,
            "earned_band": after_band in ("mastery", "origin") and before_band != after_band,
            "scene": scene}


def profession(discipline: str, *, amount: int = 0, take_build: str = "") -> dict:
    cfg, s = config(), status()
    disciplines = cfg["professions"]["disciplines"]
    if discipline not in disciplines:
        raise ValueError(f"unknown profession '{discipline}'. Known: {', '.join(disciplines)}")
    rec = s["professions"].setdefault(discipline, {"proficiency": 0, "rank": 0, "build_credits_taken": 0})
    before = rec["proficiency"]
    rec["proficiency"] = max(0, min(100, before + amount))
    before_rank, after_rank = rank_for(cfg, before), rank_for(cfg, rec["proficiency"])
    rec["rank"] = after_rank["rank"]

    credits_earned = rec["proficiency"] // 10
    credits_available = credits_earned - rec["build_credits_taken"]
    build_applied = None
    if take_build:
        builds = disciplines[discipline]["builds"]
        if take_build not in builds:
            raise ValueError(f"{discipline} builds {builds}, not '{take_build}'")
        if credits_available < 1:
            raise PermissionError(f"refused: no build credits available ({credits_earned} earned, "
                                  f"{rec['build_credits_taken']} taken). 1 credit per 10 proficiency.")
        s["attributes"][take_build] = s["attributes"].get(take_build, 0) + 1
        rec["build_credits_taken"] += 1
        credits_available -= 1
        build_applied = take_build
    save_status(s)
    return {"discipline": discipline, "from": before, "to": rec["proficiency"],
            "rank": after_rank, "rank_up": after_rank["rank"] != before_rank["rank"],
            "credits_available": credits_available, "build_applied": build_applied,
            "talent_axis": disciplines[discipline]["talent_axis"],
            "talent": s["talents"].get(disciplines[discipline]["talent_axis"], "common")}


# --------------------------------------------------------------------------
# realms
# --------------------------------------------------------------------------

def realm_gap(cfg: dict, s: dict, target_n: int) -> list[str]:
    target = realm_by_n(cfg, target_n)
    have = totals(s)
    missing = []
    for key, need in target.get("requires", {}).items():
        if have.get(key, 0) < need:
            missing.append(f"{key} {have.get(key, 0)}/{need}")
    return missing


def breakthrough(target_n: int | None = None, *, stage: str = "", scene: str = "",
                 override: bool = False) -> dict:
    cfg, s = config(), status()
    current = s["realm"]["n"]
    st = store.load(store.STATE)

    # advancing a stage within the current realm
    if target_n is None or target_n == current:
        realm = realm_by_n(cfg, current)
        stages = realm["stages"]
        if not stage:
            idx = stages.index(s["realm"]["stage"]) if s["realm"]["stage"] in stages else -1
            if idx + 1 >= len(stages):
                raise ValueError(f"already at {realm['name']} {s['realm']['stage']}; the next step is realm {current + 1}.")
            stage = stages[idx + 1]
        if stage not in stages:
            raise ValueError(f"{realm['name']} has stages {stages}")
        s["realm"]["stage"] = stage
        s["events"].append({"chapter": st["current_chapter"], "kind": "stage",
                            "text": f"{realm['name']} -> {stage}", "scene": scene})
        save_status(s)
        return {"kind": "stage", "realm": realm["name"], "stage": stage, "cost": {}}

    if target_n != current + 1 and not override:
        raise PermissionError(f"refused: realms are crossed one at a time (at {current}, asked for {target_n}).")

    target = realm_by_n(cfg, target_n)
    missing = realm_gap(cfg, s, target_n)
    if missing and not override:
        raise PermissionError(
            f"refused: {target['name']} needs " + ", ".join(missing)
            + "\n  Meeting the numbers only makes a breakthrough possible (LK-BREAKTHROUGH-COSTS)."
        )
    if not scene and not override:
        raise PermissionError(
            "refused: a breakthrough is an event, not an accumulation. Give --scene describing where it happens "
            "and under what pressure (LK-BREAKTHROUGH-COSTS)."
        )

    # a breakthrough is paid for on the story's cost tracks
    prog = store.load(store.PROGRESSION)
    paid = {}
    for track, amount in (target.get("cost") or {}).items():
        if track in prog["tracks"]["cost"]:
            c = prog["tracks"]["cost"][track]
            c["value"] = max(c.get("floor", 0), c["value"] - amount)
            paid[track] = c["value"]
    store.save(store.PROGRESSION, prog)

    s["realm"] = {"n": target_n, "name": target["name"], "stages": None,
                  "stage": target["stages"][0], "since_chapter": st["current_chapter"]}
    s["realm"].pop("stages", None)
    if cfg["absorption_rules"]["familiarity_decay"]["resets_on_breakthrough"]:
        s["familiarity"] = {}
    s["events"].append({"chapter": st["current_chapter"], "kind": "breakthrough",
                        "text": f"{target['name']} ({target['stages'][0]})", "scene": scene,
                        "cost": target.get("cost") or {}, "override": bool(missing)})
    save_status(s)
    engine.log(st, f"system: breakthrough to {target['name']}" + (" [OVERRIDE]" if missing else ""))
    store.save(store.STATE, st)
    return {"kind": "realm", "realm": target["name"], "stage": target["stages"][0],
            "cost": target.get("cost") or {}, "paid": paid,
            "familiarity_reset": cfg["absorption_rules"]["familiarity_decay"]["resets_on_breakthrough"],
            "on_page": target.get("on_page", "")}


# --------------------------------------------------------------------------
# traits and talents
# --------------------------------------------------------------------------

def trait(trait_id: str, *, state: str = "", scene: str = "", notes: str = "") -> dict:
    cfg, s = config(), status()
    spec = next((t for t in cfg["traits"] if t["id"] == trait_id), None)
    if not spec:
        raise ValueError(f"unknown trait '{trait_id}'. Known: {', '.join(t['id'] for t in cfg['traits'])}")
    states = cfg["trait_states"]
    rec = next((t for t in s["traits"] if t["id"] == trait_id), None)
    if rec is None:
        rec = {"id": trait_id, "state": "dormant", "advanced_chapter": None, "notes": notes}
        s["traits"].append(rec)
    if not state:
        idx = states.index(rec["state"])
        if idx + 1 >= len(states):
            raise ValueError(f"{spec['name']} is already {rec['state']}")
        state = states[idx + 1]
    if state not in states:
        raise ValueError(f"trait states are {states}")
    st = store.load(store.STATE)
    before = rec["state"]
    rec["state"] = state
    rec["advanced_chapter"] = st["current_chapter"]
    if notes:
        rec["notes"] = notes
    s["events"].append({"chapter": st["current_chapter"], "kind": "trait",
                        "text": f"{spec['name']}: {before} -> {state}", "scene": scene})
    save_status(s)
    return {"trait": spec, "from": before, "to": state}


def talent(discipline: str, rating: str) -> dict:
    cfg, s = config(), status()
    if discipline not in cfg["talents"]["disciplines"]:
        raise ValueError(f"unknown discipline '{discipline}'. Known: {', '.join(cfg['talents']['disciplines'])}")
    if rating not in cfg["talents"]["scale"]:
        raise ValueError(f"ratings are {', '.join(cfg['talents']['scale'])}")
    before = s["talents"].get(discipline, "common")
    s["talents"][discipline] = rating
    save_status(s)
    return {"discipline": discipline, "from": before, "to": rating,
            "multiplier": cfg["talents"]["scale"][rating]}


def purge(amount: int, method: str, scene: str = "") -> dict:
    cfg, s = config(), status()
    before = s["residue"]["value"]
    s["residue"]["value"] = max(0, before - amount)
    s["residue"]["state"] = residue_state(cfg, s["residue"]["value"])
    st = store.load(store.STATE)
    s["events"].append({"chapter": st["current_chapter"], "kind": "purge",
                        "text": f"residue {before} -> {s['residue']['value']} via {method}", "scene": scene})
    save_status(s)
    return {"from": before, "to": s["residue"]["value"], "state": s["residue"]["state"], "method": method}


# --------------------------------------------------------------------------
# the readable sheet
# --------------------------------------------------------------------------

def render_sheet() -> str:
    cfg, s = config(), status()
    a = s["attributes"]
    tot = totals(s)
    nxt = s["realm"]["n"] + 1
    gap = realm_gap(cfg, s, nxt) if any(r["n"] == nxt for r in cfg["realms"]) else []

    out = [
        f"# Status — {s['owner']}",
        "",
        "_Generated by `novel.py system sheet`. Source: `engine/system-status.json`._",
        "_The author's instrument, not the reader's: these numbers never appear in the prose._",
        "",
        f"**Realm** {s['realm']['name']} · {s['realm']['stage']}  (since chapter {s['realm'].get('since_chapter', '?')})",
        f"**Points** {s['points']['unspent']} unspent · {s['points']['lifetime_earned']} earned lifetime",
        f"**Residue** {s['residue']['value']} — *{s['residue']['state']}*"
        + (f"  \n> {residue_effect(cfg, s['residue']['value'])}" if s["residue"]["value"] else ""),
        "",
        "## Attributes",
        "",
        "| Physical | | Mental | | Rare | |",
        "|---|--:|---|--:|---|--:|",
    ]
    for i in range(4):
        rare = ""
        if i < len(RARE):
            rare = f"{RARE[i]} | {a.get(RARE[i], 0)}"
        else:
            rare = " | "
        out.append(f"| {PHYSICAL[i]} | {a.get(PHYSICAL[i], 0)} | {MENTAL[i]} | {a.get(MENTAL[i], 0)} | {rare} |")
    out += [
        "",
        f"physical total **{tot['physical_total']}** · mental total **{tot['mental_total']}**",
        "",
    ]

    out += ["## Next realm", ""]
    if gap:
        target = realm_by_n(cfg, nxt)
        out.append(f"**{target['name']}** needs: " + ", ".join(gap))
        if target.get("cost"):
            out.append(f"Cost on breakthrough: {target['cost']}")
        if target.get("on_page"):
            out.append(f"> {target['on_page']}")
    elif any(r["n"] == nxt for r in cfg["realms"]):
        target = realm_by_n(cfg, nxt)
        out.append(f"**{target['name']}** — requirements met. It still has to happen in a scene, under pressure.")
    else:
        out.append("_Top of the ladder._")
    out.append("")

    out += ["## Talents", ""]
    by_rating = {}
    for d, r in sorted(s["talents"].items()):
        by_rating.setdefault(r, []).append(d)
    for rating in ("heaven-sent", "rare", "keen", "common", "dull"):
        if rating in by_rating:
            out.append(f"- **{rating}** ({cfg['talents']['scale'][rating]}×): {', '.join(by_rating[rating])}")
    out.append("")

    out += ["## Techniques", ""]
    if s["techniques"]:
        out += ["| Technique | Grade | Proficiency | Band |", "|---|---|--:|---|"]
        for t in s["techniques"]:
            out.append(f"| {t['name']} | {t.get('grade', 'common')} | {t['proficiency']} | {band_for(cfg, t['proficiency'])} |")
    else:
        out.append("_None recorded._")
    out.append("")

    out += ["## Professions", ""]
    if s["professions"]:
        out += ["| Profession | Proficiency | Rank | Talent | Build credits unspent |", "|---|--:|---|---|--:|"]
        for d, rec in sorted(s["professions"].items()):
            r = rank_for(cfg, rec["proficiency"])
            axis = cfg["professions"]["disciplines"][d]["talent_axis"]
            unspent = rec["proficiency"] // 10 - rec.get("build_credits_taken", 0)
            out.append(f"| {d} | {rec['proficiency']} | {r['rank']} {r['name']} | "
                       f"{s['talents'].get(axis, 'common')} | {unspent} |")
    else:
        out.append("_None recorded._")
    out.append("")

    out += ["## Bloodline traits", ""]
    for rec in s["traits"]:
        spec = next((t for t in cfg["traits"] if t["id"] == rec["id"]), {})
        out.append(f"- **{spec.get('name', rec['id'])}** — *{rec['state']}*"
                   + (f" (ch.{rec['advanced_chapter']})" if rec.get("advanced_chapter") else ""))
        if spec:
            out.append(f"  - gift: {spec['gift']}")
            out.append(f"  - toll: {spec['toll']}")
            if rec["state"] == "dormant":
                out.append(f"  - trigger: {spec['trigger']}")
        if rec.get("notes"):
            out.append(f"  - notes: {rec['notes']}")
    if not s["traits"]:
        out.append("_None known._")
    out.append("")

    out += ["## Absorption log", ""]
    if s["absorption_log"]:
        out += ["| Ch. | Source | Tier | Pts | ×decay | Residue | Who paid |", "|--:|---|---|--:|--:|--:|---|"]
        for e in s["absorption_log"][-40:]:
            out.append(f"| {e['chapter']} | {e['source_class']} | {e['tier_name']} | {e['points']} | "
                       f"{e['decay_multiplier']} | {e['residue']} | {e['who_paid']} |")
        out += ["", f"_{len(s['absorption_log'])} entries total; last 40 shown. Full record in "
                    "`engine/system-status.json`._"]
    else:
        out.append("_Nothing absorbed yet._")
    out.append("")

    out += ["## Events", ""]
    for e in s["events"][-25:]:
        out.append(f"- ch.{e['chapter']} **{e['kind']}** — {e['text']}"
                   + (f"  \n  _{e['scene']}_" if e.get("scene") else ""))
    out.append("")
    return "\n".join(out)
