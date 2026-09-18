"""Chapter frameworks: the document you write before the chapter.

The generator does not invent story. It assembles everything the project
already knows about chapter N — the arc's promise, the beat the tempo asks for,
the tension target, the active cast with their wounds and agendas, the active
stages and how they have changed, the binding continuity facts, the unpaid
threads, and the protagonist's system position — into the eleven-section
document in `chapters/FRAMEWORK-SPEC.md`, with the judgement calls left as
prompts.

Minimum 500 words, enforced by `check`.
"""

from __future__ import annotations

import re
from datetime import date

from . import characters, continuity, engine, environments, store, system

FRAMEWORKS = store.CHAPTERS / "frameworks"
SHAPES = store.CHAPTERS / "shapes.json"

REQUIRED_SECTIONS = [
    "Purpose", "Goal", "Setting", "Characters involved", "Conflicts",
    "The system", "Continuity", "Shape", "Exit state", "Failure modes",
]
MIN_WORDS = 500


def shapes() -> dict:
    return store.load(SHAPES)


def find_shape(shape_id: str) -> dict:
    for s in shapes()["shapes"]:
        if s["id"] == shape_id:
            return s
    known = ", ".join(s["id"] for s in shapes()["shapes"])
    raise ValueError(f"unknown shape '{shape_id}'. Known: {known}")


def suggest_shapes(beat: str) -> list[dict]:
    return [s for s in shapes()["shapes"] if beat in s.get("serves_beats", [])]


def path_for(n: int):
    return FRAMEWORKS / f"ch-{n:03d}.md"


def planned_in(entity_id: str, before: int) -> list[int]:
    """Chapters earlier than `before` whose FRAMEWORK already plans this
    character or environment. Frameworks are written ahead of the continuity
    record, so 'last seen' has to consult both."""
    hits = []
    if not FRAMEWORKS.exists():
        return hits
    for p in sorted(FRAMEWORKS.glob("ch-*.md")):
        m = re.match(r"ch-(\d+)\.md", p.name)
        if not m:
            continue
        n = int(m.group(1))
        if n >= before:
            continue
        if entity_id in p.read_text(encoding="utf-8"):
            hits.append(n)
    return hits


def _last_appearance(entity_id: str, n: int, recorded: dict) -> str:
    """One line describing when this entity was last on the page, from the
    continuity record first and planned frameworks second."""
    rec = recorded.get(entity_id)
    plan = [c for c in planned_in(entity_id, n)]
    if rec and plan and max(plan) > rec:
        return f"last recorded in chapter {rec}; also planned in chapter {max(plan)}"
    if rec:
        return f"last recorded on the page in chapter {rec}"
    if plan:
        return f"no continuity record yet; planned in chapter {max(plan)} per its framework"
    return ""


# --------------------------------------------------------------------------
# generation
# --------------------------------------------------------------------------

def generate(n: int, *, shape_id: str = "", cast: list[str] | None = None,
             stages: list[str] | None = None, pov: str = "") -> str:
    ctx = engine.context()
    pl = engine.plan(ctx, n)
    br = continuity.brief(n)
    creg, ereg = characters.registry(), environments.registry()
    arc = engine.arc_for_chapter(ctx["arcs"], n)

    cast = cast or pl["active_characters"]
    stages = stages or pl["active_environments"]
    pov = pov or ctx["state"].get("current_pov", "")

    if not shape_id:
        candidates = suggest_shapes(pl["beat"])
        shape = candidates[0] if candidates else shapes()["shapes"][0]
    else:
        shape = find_shape(shape_id)

    out = []
    a = out.append

    # 1. header ------------------------------------------------------------
    a(f"# Chapter {n} — Framework")
    a("")
    a(f"`{pl['act']} / {pl['arc']} {pl['arc_name']}` · beat **{pl['beat']}** · "
      f"tension target **{pl['tension_target']}/10** · ~{pl['word_target']} words · "
      f"POV **{pov}** · shape **{shape['name']}**")
    a("")
    a(f"> **Arc promise:** {arc['promise']}  ")
    a(f"> **Arc question:** {arc['central_question']}  ")
    a(f"> **Pressure this arc:** {arc['pressure_source']}")
    a("")
    a("**The tempo asks for:**")
    a("")
    for o in pl["obligations"]:
        a(f"- {o}")
    a("")

    # 2. purpose -----------------------------------------------------------
    a("## Purpose")
    a("")
    a(f"_Why this chapter exists. Test: what does the novel lose if it is cut?_")
    a("")
    a(f"This is a **{pl['beat']}** beat inside *{arc['name']}*, which promises: "
      f"{arc['promise'].lower().rstrip('.')}. The chapter's job in that promise is to "
      f"{shape['for'][0].lower()}{shape['for'][1:].rstrip('.')}.")
    a("")
    a("- **Without it, the novel loses:** _<one sentence — and if the answer is \"pace\", cut it>_")
    a("- **It earns its place because:** _<the thing only this chapter can do>_")
    a("")

    # 3. goal --------------------------------------------------------------
    a("## Goal")
    a("")
    a("- **Plot goal** — what must be true at the end that was not true at the start: _<...>_")
    a("- **Reader goal** — what the reader must feel, suspect, or fear by the last line: _<...>_")
    a(f"- **Tension calibration** — open around {max(1, pl['tension_target'] - 2)}, "
      f"land on {pl['tension_target']}. "
      + ("This is a REST chapter: lower the tension and raise the dread."
         if pl["rest"] else "Do not exceed the target by more than 1 without logging why."))
    a("")

    # 4. setting -----------------------------------------------------------
    a("## Setting, and how it has changed")
    a("")
    if not stages:
        a("_No environment is active. Either stage one (`novel.py env activate`) or write this "
          "chapter somewhere already established._")
        a("")
    for eid in stages:
        e = environments.find(ereg, eid)
        if not e:
            a(f"- **{eid}** — not in the registry. Build it before the chapter: `novel.py env new`.")
            continue
        last = _last_appearance(eid, n, br["stage_last_seen"])
        a(f"### {e['name']} — {e['type']}, scale {e['scale']}")
        a("")
        a(f"- **Sensory signature:** {e['sensory_signature']}")
        a(f"- **Access rule:** {e['access_rule']}")
        a(f"- **Power here:** {e['power_structure']}")
        a(f"- **Hazards in play:** {', '.join(e['hazards'])}")
        a(f"- **Affordances this chapter uses:** {'; '.join(e['affordances'][:2])}")
        a(f"- **Its secret (not necessarily revealed):** {e['secret']}")
        a(f"- **How it changes across the novel:** {e['change_over_time']}")
        if last:
            a(f"- **THE DELTA** — {last}. What is different now? "
              "_<light, staffing, damage, who is missing, what the rules have become, what the "
              "protagonist can now notice that he could not before>_")
        else:
            a("- **THE DELTA** — first appearance. What is it changing *from* in the world, and "
              "what will it become by the arc's end? _<...>_")
        a("")

    # 5. characters --------------------------------------------------------
    a("## Characters involved, and how")
    a("")
    for cid in cast:
        c = characters.find(creg, cid)
        if not c:
            a(f"### {cid}")
            a("")
            a("_Not in the registry. `novel.py character new` before the chapter._")
            a("")
            continue
        last = _last_appearance(cid, n, br["cast_last_seen"])
        a(f"### {c['name']} — {c['role']}" + ("  *(POV)*" if cid == pov else ""))
        a("")
        a(f"- **Why they are here:** _<their reason, in their terms — never \"the plot needs them\">_")
        a(f"- **Agenda this chapter:** _<what they are trying to get; never \"help the protagonist\">_")
        a(f"- **Emotional state:** _<entering>_ → _<leaving>_")
        a(f"- **What they conceal:** _<everyone holds something back, including the POV>_")
        a(f"- Standing material — wound: {c['core']['wound']}")
        a(f"- Standing material — lie: {c['core']['lie']}")
        a(f"- Standing material — fear: {c['core']['fear']}; mask: {c['surface']['mask']}")
        a(f"- Voice handle: {c['surface']['verbal_tic']}")
        a(f"- Offstage, they are: {c['offstage_life']}")
        if last:
            a(f"- {last[0].upper()}{last[1:]}. _<what has happened to them since?>_")
        a("")
    if len(cast) < 2:
        a("_Only one character is on stage. Confirm that is deliberate — a beat of "
          "**" + pl["beat"] + "** usually needs someone to push against._")
        a("")

    # 6. conflicts ---------------------------------------------------------
    a("## Conflicts")
    a("")
    a(f"- **External** — the situation, the clock, the opposition. Arc pressure is "
      f"*{arc['pressure_source']}*: _<how it presses here>_")
    a("- **Interpersonal** — who wants something incompatible with whom: _<...>_")
    a(f"- **Internal** — the protagonist's lie under pressure in this specific way. "
      f"The lie: *{ctx['progression']['development_spine']['lie']}* _<how this chapter tests it>_")
    a("- **What is actually at stake** — the concrete thing that is worse at the end if he "
      "loses: _<name it, or the chapter has no tension to calibrate>_")
    a("")

    # 7. system ------------------------------------------------------------
    a("## The system")
    a("")
    try:
        scfg, sst = system.config(), system.status()
        nxt = sst["realm"]["n"] + 1
        gap = system.realm_gap(scfg, sst, nxt) if any(r["n"] == nxt for r in scfg["realms"]) else []
        caps = scfg["absorption_rules"]["caps"]
        a(f"- **Position entering:** {sst['realm']['name']} · {sst['realm']['stage']}, "
          f"{sst['points']['unspent']} unspent points, residue {sst['residue']['value']} "
          f"({sst['residue']['state']})")
        if gap:
            a(f"- **Next realm ({system.realm_by_n(scfg, nxt)['name']}) still needs:** {', '.join(gap)}")
        a(f"- **Budget:** {caps['points_per_chapter_soft']} points is the soft cap for this chapter, "
          f"{caps['points_per_chapter_hard']} the hard one.")
    except FileNotFoundError:
        a("- _System files not found._")
    a("- **Does the Tally move this chapter?** _<yes/no — and \"no\" is a legitimate, necessary "
      "answer. Naming it stops the drift where every chapter becomes a gain.>_")
    a("- **Source class and who paid:** _<LK-MOTE-COSTS — name the body, object, or labour>_")
    a("- **Visible to anyone?** _<who almost noticed, and what they think they saw>_")
    a("")

    # 8. continuity --------------------------------------------------------
    a("## Continuity")
    a("")
    a("**Must not contradict:**")
    a("")
    if br["binding_facts"]:
        for f in br["binding_facts"][:8]:
            a(f"- [ch.{f['chapter']}] ({f['kind']}, w{f['weight']}) {f['text']}")
    else:
        a("- _Nothing binding recorded yet._")
    a("")
    a("**Unpaid threads:**")
    a("")
    if br["unpaid_threads"]:
        for th in br["unpaid_threads"]:
            a(f"- `{th['id']}` (planted ch.{th['planted_chapter']}, "
              f"{n - th['planted_chapter']} chapters carried) {th['summary']}")
    else:
        a("- _None open._")
    a("")
    a(f"**Seeds to plant here:** _<at least "
      f"{ctx['tempo']['seed_policy']['min_seeds_planted_per_chapter']}, with the thread ids "
      "you will register>_")
    a("")
    a("**Callbacks paid:** _<which earlier chapter this cashes, or none>_")
    a("")

    # 9. shape -------------------------------------------------------------
    a("## Shape")
    a("")
    a(f"**{shape['name']}** — {shape['for']}")
    a("")
    a(f"- **Opening move:** {shape['open']}")
    a(f"  - _here:_ _<...>_")
    a(f"- **Turn:** {shape['turn']}")
    a(f"  - _here:_ _<...>_")
    a(f"- **Closing move:** {shape['close']}")
    a(f"  - _here:_ _<...>_")
    a(f"- **This shape costs:** {shape['costs']}")
    a(f"- **Watch for:** {shape['failure_mode']}")
    if shape.get("pairs_with"):
        a(f"- **Pairs well with:** {', '.join(shape['pairs_with'])} — consider for the next chapter.")
    a("")

    # 10. exit state -------------------------------------------------------
    a("## Exit state")
    a("")
    a("- **Changed by the end:** _<...>_")
    a(f"- **On stage leaving:** {', '.join(cast) or '—'}")
    a(f"- **Stages live leaving:** {', '.join(stages) or '—'}")
    a("- **Open threads leaving:** _<count and which>_")
    a("- **Emotional temperature handed to the next chapter:** _<...>_")
    nb = engine.beat_for_chapter(ctx["tempo"], n + 1)
    a(f"- **Next chapter's beat is `{nb}`** — leave it something to work with.")
    a("")

    # 11. failure modes ----------------------------------------------------
    a("## Failure modes")
    a("")
    a("_Three specific ways THIS chapter goes wrong. Not generic craft advice._")
    a("")
    a(f"1. _<...>_")
    a(f"2. _<...>_")
    a(f"3. {shape['failure_mode']}")
    a("")
    a("---")
    a(f"_Scaffolded by `novel.py framework new {n}` on {date.today().isoformat()} "
      f"from arcs.json, tempo.json, the registries, the continuity index, and system-status.json. "
      f"Spec: `chapters/FRAMEWORK-SPEC.md`._")
    a("")
    return "\n".join(out)


# --------------------------------------------------------------------------
# checking
# --------------------------------------------------------------------------

def word_count(text: str) -> int:
    body = re.sub(r"```.*?```", " ", text, flags=re.S)
    return len(re.findall(r"[A-Za-z0-9'’\-]+", body))


def unfilled(text: str) -> int:
    return len(re.findall(r"_<[^>]*>_", text))


def check(n: int) -> dict:
    p = path_for(n)
    if not p.exists():
        raise FileNotFoundError(f"no framework for chapter {n}: {store.rel(p)}")
    text = p.read_text(encoding="utf-8")
    words = word_count(text)
    missing = [s for s in REQUIRED_SECTIONS if not re.search(rf"^##\s+{re.escape(s)}", text, re.M)]
    return {
        "chapter": n, "path": store.rel(p), "words": words, "min_words": MIN_WORDS,
        "long_enough": words >= MIN_WORDS, "missing_sections": missing,
        "unfilled_prompts": unfilled(text),
        "ok": words >= MIN_WORDS and not missing,
    }


def listing() -> list[dict]:
    if not FRAMEWORKS.exists():
        return []
    rows = []
    for p in sorted(FRAMEWORKS.glob("ch-*.md")):
        m = re.match(r"ch-(\d+)\.md", p.name)
        if not m:
            continue
        n = int(m.group(1))
        try:
            rows.append(check(n))
        except FileNotFoundError:
            continue
    return rows
