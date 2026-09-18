"""Generate the macro plot for a long serial, then let the protagonist's state
bend it.

The skeleton is built from measured architecture: micro-arcs around 29 chapters,
the seven-phase macro cycle, chapter types drawn from the measured transition
matrix, seeds planted with payoff distances drawn from the measured return-gap
distribution, and realm milestones spaced against the page count.

Nothing here writes prose or invents events. It produces the frame: what each
arc is for, what question it answers, what it is allowed to introduce, which
chapters carry which mode, and where the protagonist's ladder crosses the page.

`derive` is the other half: it reads the live system state and says what the
plot now owes, so progression changes the plan instead of decorating it.
"""

from __future__ import annotations

import random
from datetime import date

from . import store, system

SKELETON = store.ENGINE / "plot-skeleton.json"
SPINE = store.ENGINE / "story-spine.json"

PHASES = ["arrival", "friction", "demonstration", "escalation", "resource", "confrontation", "departure"]
PHASE_WEIGHTS = [0.12, 0.16, 0.14, 0.16, 0.12, 0.2, 0.1]
PHASE_TYPE_BIAS = {
    "arrival": "travel", "friction": "negotiation", "demonstration": "revelation",
    "escalation": "negotiation", "resource": "training", "confrontation": "combat",
    "departure": "revelation",
}

# Measured transition matrix (serial-reference-A). Rows sum to ~1.
TRANSITIONS = {
    "combat":      {"combat": .502, "training": .100, "negotiation": .096, "travel": .088, "revelation": .096, "mixed": .118},
    "training":    {"combat": .122, "training": .274, "negotiation": .140, "travel": .119, "revelation": .213, "mixed": .132},
    "negotiation": {"combat": .128, "training": .095, "negotiation": .264, "travel": .130, "revelation": .205, "mixed": .178},
    "travel":      {"combat": .116, "training": .087, "negotiation": .118, "travel": .362, "revelation": .175, "mixed": .142},
    "revelation":  {"combat": .093, "training": .115, "negotiation": .171, "travel": .154, "revelation": .283, "mixed": .185},
    "mixed":       {"combat": .090, "training": .110, "negotiation": .163, "travel": .154, "revelation": .215, "mixed": .268},
}

PRESSURES = [
    "institutional gatekeeping", "patronage and obligation", "a debt called early",
    "a rival with better standing", "scarcity of a material everyone needs",
    "a jurisdiction that does not recognise him", "an audit", "a faction split",
    "a protector who wants something back", "law written for someone else",
    "a market cornered", "a sealed record", "conscription", "a quarantine",
    "an inheritance nobody wants", "a bounty", "an alliance that requires a hostage",
    "metered air", "a harvest that failed", "an accusation that is technically true",
]
STAKES = [
    "his place", "his anonymity", "a person who trusts him", "the pledge",
    "a profession rank", "a cache of materials", "a route out", "a name he uses",
    "someone else's freedom", "the only copy of a document", "a debt he was repaying quietly",
    "his access to a stage", "a body he cannot explain", "a promise made in public",
]
GAINS = [
    "a technique at Fluent", "a profession rank", "a patron", "a cache",
    "a name in a ledger", "a route nobody else knows", "a witness who owes him",
    "a bloodline trigger", "a forged discharge", "a workshop's failures",
    "a map of an unmetered seam", "a seat at a table", "a rival's method",
]
ENV_BY_SCALE = {
    0: ["academy", "workplace", "city-district", "origin-site"],
    1: ["city", "workplace", "city-district", "ship"],
    2: ["border-region", "country", "wilderness", "ship"],
    3: ["orbital-station", "country", "border-region"],
    4: ["moon-settlement", "orbital-station", "wilderness"],
    5: ["planet-frontier", "moon-settlement", "wilderness"],
}
ROLES_BY_PHASE = {
    "arrival": ["institution-face", "peer-ally"],
    "friction": ["rival", "institution-face"],
    "demonstration": ["patron", "peer-ally"],
    "escalation": ["handler", "rival-escalated", "antagonist"],
    "resource": ["mentor", "dependent"],
    "confrontation": ["antagonist", "the-discarded"],
    "departure": ["the-one-who-stays", "successor", "foil-from-outside"],
}


def skeleton() -> dict:
    return store.load(SKELETON)


# --------------------------------------------------------------------------
# building
# --------------------------------------------------------------------------

def _arc_lengths(rng: random.Random, total: int) -> list[int]:
    """Micro-arc lengths around the measured median of 29, p10 10, p90 141 —
    a long right tail, so a few arcs sprawl and most do not."""
    lengths = []
    used = 0
    while used < total:
        roll = rng.random()
        if roll < 0.1:
            n = rng.randint(8, 14)
        elif roll < 0.85:
            n = rng.randint(20, 38)
        else:
            n = rng.randint(50, 120)
        n = min(n, total - used)
        if n < 6 and lengths:
            lengths[-1] += n
        else:
            lengths.append(n)
        used += n
    return lengths


def _chapter_types(rng: random.Random, arcs: list[dict], total: int) -> list[str]:
    """Markov walk over the measured matrix, nudged by the arc phase so the
    confrontation stretch actually fights and the arrival stretch actually
    travels."""
    phase_of = {}
    for arc in arcs:
        for seg in arc["phases"]:
            for ch in range(seg["from"], seg["to"] + 1):
                phase_of[ch] = seg["phase"]
    out, cur = [], "travel"
    for ch in range(1, total + 1):
        row = dict(TRANSITIONS[cur])
        bias = PHASE_TYPE_BIAS.get(phase_of.get(ch, ""), None)
        if bias:
            row[bias] = row.get(bias, 0) + 0.45
        picks, weights = list(row), [row[k] for k in row]
        cur = rng.choices(picks, weights=weights, k=1)[0]
        out.append(cur)
    return out


def _phases_for(rng: random.Random, start: int, length: int) -> list[dict]:
    counts = [max(1, round(length * w)) for w in PHASE_WEIGHTS]
    while sum(counts) > length:
        counts[counts.index(max(counts))] -= 1
    while sum(counts) < length:
        counts[rng.randrange(len(counts))] += 1
    out, cursor = [], start
    for phase, n in zip(PHASES, counts):
        out.append({"phase": phase, "from": cursor, "to": cursor + n - 1})
        cursor += n
    return out


def _realm_plan(total: int) -> list[dict]:
    """Every realm and stage laid against the page count, evenly spaced. The
    engine still refuses any breakthrough that is not earned in a scene."""
    cfg = system.config()
    steps = []
    for realm in cfg["realms"]:
        if realm["n"] == 0:
            continue
        for i, stage in enumerate(realm["stages"]):
            steps.append({"realm_n": realm["n"], "realm": realm["name"], "stage": stage,
                          "is_breakthrough": i == 0})
    spacing = total / (len(steps) + 1)
    for i, s in enumerate(steps, 1):
        s["target_chapter"] = int(round(i * spacing))
    return steps


def _build_from_spine(rng: random.Random, spine: dict) -> list[dict]:
    """Arcs generated inside the story's declared movements, so the macro plot
    bends toward the intended shape instead of wandering."""
    arcs, i = [], 0
    for mv in spine["movements"]:
        lo, hi = mv["chapters"]
        span = hi - lo + 1
        n_arcs = mv["arcs"]
        base = span // n_arcs
        bounds, cursor = [], lo
        for k in range(n_arcs):
            length = span - (cursor - lo) if k == n_arcs - 1 else base + rng.randint(-4, 4)
            bounds.append((cursor, cursor + length - 1))
            cursor += length
        # draw without replacement inside a movement: an arc that repeats the
        # previous arc's pressure reads as the plot stalling, not escalating
        pool_p = mv["pressures"][:]; rng.shuffle(pool_p)
        pool_s = mv["stakes"][:]; rng.shuffle(pool_s)
        pool_g = mv["gains"][:]; rng.shuffle(pool_g)
        for k, (a0, a1) in enumerate(bounds):
            i += 1
            pressure = pool_p[k % len(pool_p)] if len(pool_p) >= n_arcs else rng.choice(mv["pressures"])
            stake = pool_s[k % len(pool_s)]
            gain = pool_g[k % len(pool_g)]
            arcs.append({
                "id": f"A{i:02d}", "movement": mv["id"], "chapters": [a0, a1], "length": a1 - a0 + 1,
                "scale_tier": mv["scale_tier"],
                "pressure_source": pressure,
                "central_question": f"Can he keep {stake} while {pressure} holds?",
                "promise": f"He enters with {stake} intact and leaves having spent it, or kept it at a price.",
                "closes_on": f"The confrontation resolves and he carries out {gain}.",
                # the first arc of the novel must license the stage it opens on
                "licensed_environments": sorted(set(rng.sample(mv["environments"],
                                                               k=min(3, len(mv["environments"]))))
                                                | ({mv["environments"][0]} if i == 1 else set())),
                "licensed_character_roles": sorted(set(rng.sample(mv["roles"], k=min(3, len(mv["roles"]))))),
                "phases": _phases_for(rng, a0, a1 - a0 + 1),
                "tension": dict(mv["tension"]),
                "gain_on_close": gain, "stake": stake,
            })
    return arcs


def build(total: int = 1337, seed: int | None = None) -> dict:
    seed = seed if seed is not None else random.randrange(1 << 30)
    rng = random.Random(seed)

    spine = store.load(SPINE, None)
    if spine:
        total = spine.get("total_chapters", total)
        arcs = _build_from_spine(rng, spine)
        volumes = [{"id": mv["id"], "name": mv["name"], "chapters": mv["chapters"],
                    "question": mv["question"],
                    "arcs": [a["id"] for a in arcs if a["movement"] == mv["id"]]}
                   for mv in spine["movements"]]
        types = _chapter_types(rng, arcs, total)
        realm_plan = _realm_plan(total)
        seeds = _plan_seeds(rng, arcs, total)
        return {
            "description": "Generated from engine/story-spine.json. Structure from measured serial "
                           "architecture; movements, pressures and stakes from the story's own spine.",
            "generated": date.today().isoformat(), "seed": seed, "total_chapters": total,
            "spine": spine.get("description", ""), "volumes": volumes, "arcs": arcs,
            "chapter_types": types, "realm_plan": realm_plan, "seeds": seeds,
            "calibration": {"source": "serial-reference-A via engine/genre-priors.json"},
        }

    lengths = _arc_lengths(rng, total)
    arcs, cursor = [], 1
    for i, n in enumerate(lengths, 1):
        scale = min(5, int((cursor / total) * 6))
        phases = _phases_for(rng, cursor, n)
        pressure = rng.choice(PRESSURES)
        stake = rng.choice(STAKES)
        gain = rng.choice(GAINS)
        arcs.append({
            "id": f"A{i:02d}",
            "chapters": [cursor, cursor + n - 1],
            "length": n,
            "scale_tier": scale,
            "pressure_source": pressure,
            "central_question": f"Can he keep {stake} while {pressure} holds?",
            "promise": f"He enters with {stake} intact and leaves having traded it, or kept it at a price.",
            "closes_on": f"The confrontation resolves and he carries out {gain}.",
            "licensed_environments": sorted(set(rng.sample(ENV_BY_SCALE[scale], k=min(2, len(ENV_BY_SCALE[scale]))))
                                             | ({"academy"} if i == 1 else set())),
            "licensed_character_roles": sorted({r for p in PHASES for r in ROLES_BY_PHASE[p]
                                                if rng.random() < 0.45}) or ["rival", "peer-ally"],
            "phases": phases,
            "tension": {"open": rng.randint(3, 5), "peak": rng.randint(8, 10), "close": rng.randint(2, 5)},
            "gain_on_close": gain,
            "stake": stake,
        })
        cursor += n

    # volumes group arcs into 150-400 chapter books
    volumes, vstart, varcs = [], 1, []
    for arc in arcs:
        varcs.append(arc["id"])
        if arc["chapters"][1] - vstart + 1 >= 230 or arc is arcs[-1]:
            volumes.append({"id": f"V{len(volumes) + 1}", "chapters": [vstart, arc["chapters"][1]],
                            "arcs": list(varcs)})
            vstart = arc["chapters"][1] + 1
            varcs = []

    types = _chapter_types(rng, arcs, total)
    realm_plan = _realm_plan(total)

    seeds = _plan_seeds(rng, arcs, total)
    return {
        "description": ("Generated macro plot. Structure comes from measured serial architecture; content is "
                        "this novel's own. Rebuild any time with `novel.py plot build`; the protagonist's "
                        "state can bend it via `novel.py plot next`."),
        "generated": date.today().isoformat(),
        "seed": seed,
        "total_chapters": total,
        "volumes": volumes,
        "arcs": arcs,
        "chapter_types": types,
        "realm_plan": realm_plan,
        "seeds": seeds,
        "calibration": {
            "arc_length_median_target": 29,
            "source": "serial-reference-A via engine/genre-priors.json",
        },
    }


# --------------------------------------------------------------------------
# reading
# --------------------------------------------------------------------------

def _plan_seeds(rng: random.Random, arcs: list[dict], total: int) -> list[dict]:
    """Payoff distances drawn from the measured return-gap distribution, scaled
    to this novel's length."""
    scale = total / 3204
    near_hi = max(6, int(39 * max(scale, 0.1) * 8))
    deep_hi = max(near_hi + 10, int(120 * max(scale, 0.1) * 6))
    seeds = []
    for arc in arcs:
        for _ in range(rng.randint(1, 3)):
            plant = rng.randint(arc["chapters"][0], arc["chapters"][1])
            roll = rng.random()
            if roll < 0.65:
                gap = rng.randint(2, near_hi)
            elif roll < 0.92:
                gap = rng.randint(near_hi + 1, deep_hi)
            else:
                gap = rng.randint(deep_hi + 1, max(deep_hi + 2, int(total * 0.6)))
            seeds.append({"planted_chapter": plant, "target_payoff": min(total, plant + gap),
                          "gap": gap, "arc": arc["id"],
                          "band": "near" if gap <= near_hi else ("deep" if gap <= deep_hi else "very deep")})
    seeds.sort(key=lambda s: s["planted_chapter"])
    return seeds


def arc_for(sk: dict, chapter: int) -> dict | None:
    for a in sk["arcs"]:
        if a["chapters"][0] <= chapter <= a["chapters"][1]:
            return a
    return None


def phase_for(arc: dict, chapter: int) -> str:
    for seg in arc["phases"]:
        if seg["from"] <= chapter <= seg["to"]:
            return seg["phase"]
    return "?"


def volume_for(sk: dict, chapter: int) -> dict | None:
    for v in sk["volumes"]:
        if v["chapters"][0] <= chapter <= v["chapters"][1]:
            return v
    return None


def chapter_type(sk: dict, chapter: int) -> str:
    types = sk["chapter_types"]
    return types[chapter - 1] if 1 <= chapter <= len(types) else "?"


# --------------------------------------------------------------------------
# progression drives the plot
# --------------------------------------------------------------------------

def derive(chapter: int | None = None) -> dict:
    """Read the protagonist's live state and say what the plot now owes.

    This is the half that matters: the skeleton is a plan, and the plan is
    wrong the moment the protagonist diverges from it. Everything returned here
    outranks the skeleton.
    """
    sk = skeleton()
    cfg, sst = system.config(), system.status()
    st = store.load(store.STATE)
    prog = store.load(store.PROGRESSION)
    chapter = chapter or st["current_chapter"]
    arc = arc_for(sk, chapter)

    directives, divergence = [], []

    # where the plan expected him to be
    due = [s for s in sk["realm_plan"] if s["target_chapter"] <= chapter]
    expected = due[-1] if due else None
    if expected:
        if sst["realm"]["n"] < expected["realm_n"]:
            divergence.append(
                f"BEHIND: the plan put him at {expected['realm']} {expected['stage']} by chapter "
                f"{expected['target_chapter']}; he is at {sst['realm']['name']} {sst['realm']['stage']}. "
                "Either the next arc hands him a resource, or the plan is wrong and should be rebuilt from here.")
        elif sst["realm"]["n"] > expected["realm_n"]:
            divergence.append(
                f"AHEAD: he is at {sst['realm']['name']}, the plan expected {expected['realm']}. "
                "The opposition tier in the coming arcs is too soft. Rebuild downstream or escalate.")

    # residue is a clock
    res = sst["residue"]["value"]
    state_name = system.residue_state(cfg, res)
    if res >= 75:
        directives.append(("CRISIS", f"Residue {res} ({state_name}). A deviation event is overdue and must "
                                     "land on the page, at the worst available time. This outranks the arc plan."))
    elif res >= 50:
        directives.append(("PRESSURE", f"Residue {res} ({state_name}). He is worse in long fights now. "
                                       "A confrontation phase should expose it before he can purge."))
    elif res >= 25:
        directives.append(("SEED", f"Residue {res} ({state_name}). Sleep and perception should be going wrong "
                                   "in small ways nobody comments on."))

    # cost tracks at the floor are relationship plot
    for name, tr in prog["tracks"]["cost"].items():
        if tr["value"] <= tr.get("floor", 0) + 1:
            directives.append(("RUPTURE", f"Cost track '{name}' is at {tr['value']}. Something has to break "
                                          f"that cannot be repaired by competence. Give the next arc a scene "
                                          f"where {name} is the thing on the table."))

    # traits that are stirred want their trigger
    for rec in sst["traits"]:
        if rec["state"] == "stirred":
            spec = next((x for x in cfg["traits"] if x["id"] == rec["id"]), {})
            directives.append(("TRIGGER", f"Trait '{spec.get('name', rec['id'])}' is stirred. Its trigger — "
                                          f"{spec.get('trigger', 'unknown')} — should be reachable inside the "
                                          f"next two arcs. Its toll ({spec.get('toll', '?')}) lands on the page."))

    # readiness for the next realm
    nxt = sst["realm"]["n"] + 1
    if any(r["n"] == nxt for r in cfg["realms"]):
        gap = system.realm_gap(cfg, sst, nxt)
        target = next((s for s in sk["realm_plan"] if s["realm_n"] == nxt and s["is_breakthrough"]), None)
        if not gap:
            directives.append(("BREAKTHROUGH", f"Requirements for {system.realm_by_n(cfg, nxt)['name']} are met. "
                                               "It needs a confrontation phase and a cost that does not come back."))
        elif target:
            directives.append(("TRAJECTORY", f"{system.realm_by_n(cfg, nxt)['name']} is planned for chapter "
                                             f"{target['target_chapter']}; still needs {', '.join(gap)}. "
                                             "An arc between here and there must supply it."))

    # unspent points are a plot smell
    if sst["points"]["unspent"] >= 40:
        directives.append(("INVENTORY", f"{sst['points']['unspent']} unspent points. A gain that sits unspent "
                                        "reads as inventory — the measured form spends within a few chapters. "
                                        "Force a scene that requires the capability he has not bought."))

    return {
        "chapter": chapter,
        "arc": arc["id"] if arc else None,
        "phase": phase_for(arc, chapter) if arc else None,
        "chapter_type": chapter_type(sk, chapter),
        "arc_question": arc["central_question"] if arc else None,
        "arc_pressure": arc["pressure_source"] if arc else None,
        "directives": directives,
        "divergence": divergence,
        "seeds_due": [s for s in sk["seeds"] if s["target_payoff"] == chapter],
        "seeds_planting": [s for s in sk["seeds"] if s["planted_chapter"] == chapter],
    }
