"""Command line for the novel engine. `tools/novel.py --help` for the map."""

from __future__ import annotations

import argparse
import sys

from . import characters, continuity, engine, environments, store, validate

BAR = "=" * 68


def _p(*a):
    print(*a)


def _h(title):
    _p("")
    _p(title)
    _p("-" * len(title))


def _csv(value):
    return [v.strip() for v in (value or "").split(",") if v.strip()]


# ---------------------------------------------------------------- status/plan

def cmd_status(args):
    ctx = engine.context()
    state = ctx["state"]
    arc = engine.arc_for_chapter(ctx["arcs"], state["current_chapter"])
    pl = engine.plan(ctx)
    _p(BAR)
    _p(f" Chapter {state['current_chapter']}  ·  {pl['act']} / {arc['id']} {arc['name']}")
    _p(BAR)
    _p(f" Central question : {arc['central_question']}")
    _p(f" Pressure source  : {arc['pressure_source']}")
    _p(f" Beat             : {pl['beat']}   Tension target: {pl['tension_target']}/10"
       + ("   [REST CHAPTER]" if pl["rest"] else ""))
    _p(f" POV              : {state.get('current_pov', '-')}")
    _p(f" On stage         : {', '.join(state.get('active_characters', [])) or '—'}")
    _p(f" Stages live      : {', '.join(state.get('active_environments', [])) or '—'}")
    _p(f" Open threads     : {pl['open_thread_count']}")

    creg, ereg = characters.registry(), environments.registry()
    _p(f" Bench            : {sum(1 for c in creg['characters'] if c['status'] == 'dormant')} dormant characters, "
       f"{sum(1 for e in ereg['environments'] if e['status'] == 'dormant')} dormant environments")
    budget = ctx["tempo"]["introduction_budget"]
    _p(f" Introductions    : characters {state['introductions_this_arc'].get('characters', 0)}"
       f"/{budget['named_characters_per_arc']} this arc · "
       f"environments {state['introductions_this_arc'].get('environments', 0)}"
       f"/{budget['environments_per_arc']} this arc")

    prog = ctx["progression"]
    _h("Protagonist tracks")
    for group in ("capability", "cost", "internal"):
        row = "  ".join(f"{k}:{v['value']}" for k, v in prog["tracks"][group].items())
        _p(f" {group:11} {row}")
    gates = engine.gate_report(ctx)
    if gates["ready"]:
        _p("")
        for g in gates["ready"]:
            _p(f" GATE READY  {g['id']} {g['name']}  ({g.get('on_page', 'earn it on the page')})")
    errors, warnings = validate.run()
    if errors or warnings:
        _h("Health")
        for e in errors:
            _p(f" ERROR   {e}")
        for w in warnings[:5]:
            _p(f" warn    {w}")
    _p("")
    return 0


def cmd_plan(args):
    ctx = engine.context()
    pl = engine.plan(ctx, args.chapter)
    _p(BAR)
    _p(f" PLAN — Chapter {pl['chapter']}  ·  {pl['act']} / {pl['arc']} {pl['arc_name']}")
    _p(BAR)
    _p(f" Question this arc answers: {pl['central_question']}")
    _p(f" Word target: ~{pl['word_target']}")
    _h("This chapter owes")
    for o in pl["obligations"]:
        _p(f" • {o}")
    if pl["payable_threads"]:
        _h("Seeds ripe for payoff")
        for t in pl["payable_threads"]:
            _p(f" • {t['id']} (planted {t['age']} chapters ago) — {t['summary']}")
    _h("Casting licence")
    _p(f" New character : {'YES' if pl['may_introduce_character'] else 'NO'}"
       + ("" if pl["may_introduce_character"] else "  — " + "; ".join(pl["character_block_reasons"])))
    _p(f"   arc licenses roles: {', '.join(pl['licensed_roles'])}")
    _p(f" New environment: {'YES' if pl['may_introduce_environment'] else 'NO'}"
       + ("" if pl["may_introduce_environment"] else "  — " + "; ".join(pl["environment_block_reasons"])))
    _p(f"   arc licenses types: {', '.join(pl['licensed_environments'])}")
    _h("Progression ceilings this chapter")
    _p(" " + "  ".join(f"{k}:{v}" for k, v in pl["capability_ceiling"].items()))
    if pl["gates_blocked"]:
        for g in pl["gates_blocked"]:
            _p(f" gate {g['id']} {g['name']} — needs {', '.join(g['missing'])}")
    br = continuity.brief(pl["chapter"])
    if br["binding_facts"]:
        _h("Must not contradict")
        for f in br["binding_facts"][:8]:
            _p(f" • [ch.{f['chapter']}] ({f['kind']}) {f['text']}")
    _p("")
    return 0


# ---------------------------------------------------------------- characters

def cmd_character_new(args):
    c = characters.generate(args.role, need=args.need, culture=args.culture,
                            seed=args.seed, name=args.name, notes=args.notes or "")
    path = characters.persist(c)
    _p(f"Created {c['name']} ({c['role']}) — dormant.")
    _p(f"  id   : {c['id']}")
    _p(f"  seed : {c['seed']}  (regenerate the same character with --seed {c['seed']})")
    _p(f"  file : {path}")
    _p("")
    _p("  Contradictions to play:")
    for t in c["contradictions"]:
        _p(f"   - {t}")
    _p("")
    _p("They are on the bench. `novel.py character introduce " + c["id"] + " --need \"...\"` when the story needs them.")
    return 0


def cmd_character_list(args):
    reg = characters.registry()
    rows = [c for c in reg["characters"] if not args.status or c["status"] == args.status]
    if not rows:
        _p("No characters match.")
        return 0
    for c in sorted(rows, key=lambda c: (c["status"] != "active", c["role"], c["name"])):
        ch = f"ch.{c['introduced_chapter']}" if c.get("introduced_chapter") else "—"
        _p(f" {c['status']:8} {c['role']:18} {c['name']:24} {ch:7} {c['id']}")
    return 0


def cmd_character_show(args):
    reg = characters.registry()
    c = characters.find(reg, args.id)
    if not c:
        _p(f"unknown character: {args.id}")
        return 1
    _p((store.ROOT / c["file"]).read_text(encoding="utf-8"))
    return 0


def cmd_character_introduce(args):
    try:
        c = characters.introduce(args.id, need=args.need, chapter=args.chapter, override=args.override)
    except PermissionError as exc:
        _p(str(exc))
        return 2
    _p(f"{c['name']} enters in chapter {c['introduced_chapter']}.")
    _p(f"  need  : {c['need_that_licenses']}")
    _p(f"  entry : {c['contract']['entry_pretext']}")
    _p(f"  file  : {c['file']}")
    for cond in c["contract"]["first_appearance_conditions"]:
        _p(f"  - {cond}")
    return 0


# -------------------------------------------------------------- environments

def cmd_env_new(args):
    e = environments.generate(args.type, need=args.need, name=args.name, seed=args.seed,
                              parent=args.parent or "", notes=args.notes or "")
    path = environments.persist(e)
    _p(f"Built {e['name']} ({e['type']}, scale {e['scale']}) — dormant.")
    _p(f"  id     : {e['id']}")
    _p(f"  seed   : {e['seed']}")
    _p(f"  file   : {path}")
    _p(f"  secret : {e['secret']}")
    _p("  affordances:")
    for a in e["affordances"]:
        _p(f"   - {a}")
    return 0


def cmd_env_list(args):
    reg = environments.registry()
    rows = [e for e in reg["environments"] if not args.status or e["status"] == args.status]
    if not rows:
        _p("No environments match.")
        return 0
    for e in sorted(rows, key=lambda e: (e["status"] != "active", e["scale"], e["name"])):
        ch = f"ch.{e['activated_chapter']}" if e.get("activated_chapter") else "—"
        _p(f" {e['status']:8} {e['type']:18} {e['scale']:10} {e['name']:26} {ch:7} {e['id']}")
    return 0


def cmd_env_show(args):
    reg = environments.registry()
    e = environments.find(reg, args.id)
    if not e:
        _p(f"unknown environment: {args.id}")
        return 1
    _p((store.ROOT / e["file"]).read_text(encoding="utf-8"))
    return 0


def cmd_env_activate(args):
    try:
        e = environments.activate(args.id, need=args.need, chapter=args.chapter, override=args.override)
    except PermissionError as exc:
        _p(str(exc))
        return 2
    _p(f"{e['name']} comes on stage in chapter {e['activated_chapter']}.")
    _p(f"  sensory signature : {e['sensory_signature']}")
    _p(f"  access rule       : {e['access_rule']}")
    _p(f"  file              : {e['file']}")
    return 0


# -------------------------------------------------------------------- seeds

def cmd_seed_plant(args):
    ctx = engine.context()
    ch = args.chapter or ctx["state"]["current_chapter"]
    th = continuity.plant(args.id, args.summary, ch, kind=args.kind, owner=args.owner or "")
    window = ctx["tempo"]["seed_policy"]["payoff_window_chapters"]
    _p(f"Seed '{th['id']}' planted in chapter {ch}.")
    _p(f"  payable from chapter {ch + window['min']}, stale after {ch + window['soft_max']}, "
       f"rot at {ch + window['hard_max']}.")
    return 0


def cmd_seed_pay(args):
    ctx = engine.context()
    ch = args.chapter or ctx["state"]["current_chapter"]
    th = continuity.pay(args.id, ch, args.note or "", status=args.status)
    _p(f"Thread '{th['id']}' {th['status']} in chapter {ch} (planted ch.{th['planted_chapter']}, "
       f"{ch - th['planted_chapter']} chapters carried).")
    return 0


def cmd_seed_list(args):
    t = continuity.threads()
    rows = [th for th in t["threads"] if not args.status or th["status"] == args.status]
    if not rows:
        _p("No threads.")
        return 0
    cur = engine.context()["state"]["current_chapter"]
    for th in sorted(rows, key=lambda x: x["planted_chapter"]):
        age = cur - th["planted_chapter"]
        _p(f" {th['status']:8} ch.{th['planted_chapter']:<4} age {age:<4} {th['id']:22} {th['summary']}")
    return 0


# ------------------------------------------------------------------ chapters

def cmd_chapter_record(args):
    idx = continuity.index()
    ctx = engine.context()
    ch = continuity.ensure_chapter(
        idx, args.number,
        title=args.title, summary=args.summary, pov=args.pov or ctx["state"].get("current_pov", ""),
        tension=args.tension, kind=args.kind,
        arc=engine.arc_for_chapter(ctx["arcs"], args.number)["id"],
        beat=engine.beat_for_chapter(ctx["tempo"], args.number),
        characters=_csv(args.characters), environments=_csv(args.environments),
    )
    continuity.save_index(idx)
    _p(f"Recorded chapter {ch['chapter']} ({ch['arc']}, beat {ch['beat']}).")
    _p("Add the load-bearing details with `novel.py chapter point`.")
    return 0


def cmd_chapter_point(args):
    p = continuity.add_point(args.number, args.kind, args.text, weight=args.weight,
                             tags=_csv(args.tags), must_respect=not args.soft, lock=args.lock or "")
    _p(f"{p['id']} recorded on chapter {args.number}: ({p['kind']}, w{p['weight']}) {p['text']}")
    if p["tags"]:
        _p(f"  tags: {', '.join(p['tags'])}")
    return 0


def cmd_chapter_close(args):
    ctx = engine.context()
    closed = ctx["state"]["current_chapter"]
    state = engine.close_chapter(ctx, tension=args.tension, kind=args.kind, revelation=args.revelation)
    _p(f"Chapter {closed} closed. Now on chapter {state['current_chapter']} ({state['current_arc']}).")
    _p("")
    args.chapter = None
    return cmd_plan(args)


# ---------------------------------------------------------------- continuity

def cmd_lookback(args):
    hits = continuity.lookback(args.query or "", tags=_csv(args.tags), kinds=_csv(args.kinds),
                               before=args.before, min_weight=args.min_weight, limit=args.limit)
    if not hits:
        _p("Nothing in the record matches. Either it was never load-bearing, or it was never recorded.")
        return 0
    _p(f"{len(hits)} reference(s):")
    for h in hits:
        flag = "!" if h["must_respect"] else " "
        _p(f" [ch.{h['chapter']:>3}]{flag} ({h['kind']}, w{h['weight']}, score {h['score']}) {h['text']}")
        if h["tags"]:
            _p(f"           tags: {', '.join(h['tags'])}   id: {h['id']}")
    return 0


def cmd_brief(args):
    ctx = engine.context()
    n = args.chapter or ctx["state"]["current_chapter"]
    br = continuity.brief(n)
    _p(BAR)
    _p(f" CONTINUITY BRIEF — writing chapter {n}")
    _p(BAR)
    _h("Binding facts (do not contradict)")
    for f in br["binding_facts"] or []:
        _p(f" • [ch.{f['chapter']}] ({f['kind']}, w{f['weight']}) {f['text']}")
    if not br["binding_facts"]:
        _p(" — nothing recorded yet")
    _h("Unpaid threads")
    for th in br["unpaid_threads"]:
        _p(f" • {th['id']} (ch.{th['planted_chapter']}, {n - th['planted_chapter']} chapters carried) {th['summary']}")
    if not br["unpaid_threads"]:
        _p(" — none")
    _h("Last three chapters")
    for c in br["recent_chapters"]:
        _p(f" ch.{c['chapter']} {c['title']}: {c['summary'][:140]}")
    _h("Last seen")
    for who, ch in list(br["cast_last_seen"].items())[:10]:
        _p(f" {who:28} ch.{ch}")
    for where, ch in list(br["stage_last_seen"].items())[:10]:
        _p(f" {where:28} ch.{ch}")
    _p("")
    return 0


def cmd_continuity_sync(args):
    text = continuity.render_reference_map()
    out = store.CONTINUITY / "reference-map.md"
    store.write_text(out, text)
    _p(f"Wrote {store.rel(out)}")
    return 0


# --------------------------------------------------------------- progression

def cmd_advance(args):
    prog = store.load(store.PROGRESSION)
    ctx = engine.context()
    state, arcs = ctx["state"], ctx["arcs"]
    chapter = state["current_chapter"]
    cap = prog["tracks"]["capability"]
    cost = prog["tracks"]["cost"]

    if args.track not in cap:
        _p(f"unknown capability track '{args.track}'. Known: {', '.join(cap)}")
        return 1
    if args.cost not in cost:
        _p(f"unknown cost track '{args.cost}'. Known: {', '.join(cost)}")
        return 1
    if engine.is_rest_chapter(ctx["tempo"], chapter) and not args.override:
        _p(f"chapter {chapter} is a rest chapter: no capability track may rise. Use --override to log an exception.")
        return 2

    amount = args.amount
    ceiling = engine.capability_ceiling(chapter, arcs, state["current_arc"], cap[args.track].get("start", 0))
    new = cap[args.track]["value"] + amount
    if new > ceiling and not args.override:
        _p(f"refused: {args.track} would reach {new}, ceiling at chapter {chapter} is {ceiling}.")
        _p("  The story has not paid for this yet. Write more chapters or use --override with a reason.")
        return 2
    cap[args.track]["value"] = min(new, cap[args.track].get("ceiling", 10))
    cost[args.cost]["value"] = max(cost[args.cost].get("floor", 0), cost[args.cost]["value"] - amount)
    store.save(store.PROGRESSION, prog)
    engine.log(state, f"progression: {args.track} +{amount} paid with {args.cost} -{amount}"
                      + (f" — {args.reason}" if args.reason else ""))
    store.save(store.STATE, state)
    _p(f"{args.track} {cap[args.track]['value']}  (paid: {args.cost} {cost[args.cost]['value']})")
    _p(f"  It must happen on the page in chapter {chapter}, not in summary.")
    return 0


def cmd_lie(args):
    prog = store.load(store.PROGRESSION)
    internal = prog["tracks"]["internal"]
    new = max(0, min(10, internal["lie_grip"]["value"] - args.amount))
    internal["lie_grip"]["value"] = new
    internal["self_knowledge"]["value"] = 10 - new
    store.save(store.PROGRESSION, prog)
    _p(f"lie_grip {new}  ·  self_knowledge {10 - new}")
    _p("  Valid only after an on-page refusal, failure, or confrontation.")
    return 0


def cmd_gate_pass(args):
    ctx = engine.context()
    state = ctx["state"]
    gate = next((g for g in ctx["progression"]["gates"] if g["id"] == args.id), None)
    if not gate:
        _p(f"unknown gate: {args.id}")
        return 1
    if args.id in state.get("gates_passed", []):
        _p(f"{args.id} already passed.")
        return 0
    state.setdefault("gates_passed", []).append(args.id)
    engine.log(state, f"gate {args.id} '{gate['name']}' passed")
    store.save(store.STATE, state)
    _p(f"Gate {args.id} — {gate['name']} — passed in chapter {state['current_chapter']}.")
    for unlock in gate.get("unlocks", []):
        _p(f"  unlocks: {unlock}")
    if gate.get("cost"):
        _p(f"  cost owed: {gate['cost']} — apply it with `novel.py advance` or on the page.")
    return 0


# ----------------------------------------------------------------- validate

def cmd_validate(args):
    errors, warnings = validate.run()
    for e in errors:
        _p(f"ERROR   {e}")
    for w in warnings:
        _p(f"warn    {w}")
    if not errors and not warnings:
        _p("Clean. The bible, the engine, and the registries agree.")
    return 1 if errors else 0


# --------------------------------------------------------------------- parser

def build_parser():
    p = argparse.ArgumentParser(prog="novel.py", description="The novel engine: tempo, casting, world, and memory.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="where the novel stands right now").set_defaults(func=cmd_status)

    pl = sub.add_parser("plan", help="what the next chapter owes the reader")
    pl.add_argument("--chapter", type=int)
    pl.set_defaults(func=cmd_plan)

    ch = sub.add_parser("character", help="create, bench, and introduce people").add_subparsers(dest="sub", required=True)
    n = ch.add_parser("new", help="generate a deep dossier onto the bench")
    n.add_argument("--role", required=True)
    n.add_argument("--need", required=True, help="the storyline need that may one day license them")
    n.add_argument("--culture", default="ledger", choices=sorted(characters.SYLLABLES))
    n.add_argument("--name")
    n.add_argument("--seed", type=int)
    n.add_argument("--notes")
    n.set_defaults(func=cmd_character_new)
    l = ch.add_parser("list"); l.add_argument("--status", choices=["active", "dormant"]); l.set_defaults(func=cmd_character_list)
    s = ch.add_parser("show"); s.add_argument("id"); s.set_defaults(func=cmd_character_show)
    i = ch.add_parser("introduce", help="move from bench to page - requires a stated need")
    i.add_argument("id"); i.add_argument("--need", required=True)
    i.add_argument("--chapter", type=int); i.add_argument("--override", action="store_true")
    i.set_defaults(func=cmd_character_introduce)

    ev = sub.add_parser("env", help="build and stage places").add_subparsers(dest="sub", required=True)
    en = ev.add_parser("new")
    en.add_argument("--type", required=True)
    en.add_argument("--need", required=True)
    en.add_argument("--name"); en.add_argument("--seed", type=int); en.add_argument("--parent"); en.add_argument("--notes")
    en.set_defaults(func=cmd_env_new)
    el = ev.add_parser("list"); el.add_argument("--status", choices=["active", "dormant"]); el.set_defaults(func=cmd_env_list)
    es = ev.add_parser("show"); es.add_argument("id"); es.set_defaults(func=cmd_env_show)
    ea = ev.add_parser("activate"); ea.add_argument("id"); ea.add_argument("--need", required=True)
    ea.add_argument("--chapter", type=int); ea.add_argument("--override", action="store_true")
    ea.set_defaults(func=cmd_env_activate)

    sd = sub.add_parser("seed", help="plant and pay off setups").add_subparsers(dest="sub", required=True)
    sp = sd.add_parser("plant"); sp.add_argument("--id", required=True); sp.add_argument("--summary", required=True)
    sp.add_argument("--chapter", type=int); sp.add_argument("--kind", default="seed"); sp.add_argument("--owner")
    sp.set_defaults(func=cmd_seed_plant)
    sy = sd.add_parser("pay"); sy.add_argument("--id", required=True); sy.add_argument("--chapter", type=int)
    sy.add_argument("--note"); sy.add_argument("--status", default="paid", choices=["paid", "repurposed", "retired"])
    sy.set_defaults(func=cmd_seed_pay)
    sl = sd.add_parser("list"); sl.add_argument("--status"); sl.set_defaults(func=cmd_seed_list)

    cp = sub.add_parser("chapter", help="record what happened and what must be remembered").add_subparsers(dest="sub", required=True)
    cr = cp.add_parser("record"); cr.add_argument("number", type=int)
    cr.add_argument("--title", default=""); cr.add_argument("--summary", default="")
    cr.add_argument("--tension", type=int, default=0); cr.add_argument("--kind", default="")
    cr.add_argument("--pov", default=""); cr.add_argument("--characters", default=""); cr.add_argument("--environments", default="")
    cr.set_defaults(func=cmd_chapter_record)
    cpt = cp.add_parser("point", help="record a load-bearing detail later chapters must respect")
    cpt.add_argument("number", type=int); cpt.add_argument("--kind", required=True, choices=continuity.KINDS)
    cpt.add_argument("--text", required=True); cpt.add_argument("--weight", type=int, default=3)
    cpt.add_argument("--tags", default=""); cpt.add_argument("--soft", action="store_true", help="colour, not canon")
    cpt.add_argument("--lock", default="", help="canon lock id this detail rests on, e.g. LK-NO-ERASURE")
    cpt.set_defaults(func=cmd_chapter_point)
    cc = cp.add_parser("close", help="advance the metronome")
    cc.add_argument("--tension", type=int, required=True)
    cc.add_argument("--kind", default="conflict", choices=["conflict", "discovery", "relationship", "consequence", "quiet"])
    cc.add_argument("--revelation", action="store_true")
    cc.set_defaults(func=cmd_chapter_close)

    lb = sub.add_parser("lookback", help="search the past for what this chapter must respect")
    lb.add_argument("query", nargs="?", default="")
    lb.add_argument("--tags", default=""); lb.add_argument("--kinds", default="")
    lb.add_argument("--before", type=int); lb.add_argument("--min-weight", type=int, default=1, dest="min_weight")
    lb.add_argument("--limit", type=int, default=20)
    lb.set_defaults(func=cmd_lookback)

    br = sub.add_parser("brief", help="the full continuity brief for a chapter")
    br.add_argument("--chapter", type=int); br.set_defaults(func=cmd_brief)

    ct = sub.add_parser("continuity").add_subparsers(dest="sub", required=True)
    ct.add_parser("sync", help="regenerate continuity/reference-map.md").set_defaults(func=cmd_continuity_sync)

    ad = sub.add_parser("advance", help="raise a capability track - requires paying a cost track")
    ad.add_argument("track"); ad.add_argument("--cost", required=True); ad.add_argument("--amount", type=int, default=1)
    ad.add_argument("--reason"); ad.add_argument("--override", action="store_true")
    ad.set_defaults(func=cmd_advance)

    li = sub.add_parser("lie", help="loosen the protagonist's controlling lie after an on-page break")
    li.add_argument("--amount", type=int, default=1); li.set_defaults(func=cmd_lie)

    gt = sub.add_parser("gate").add_subparsers(dest="sub", required=True)
    gp = gt.add_parser("pass"); gp.add_argument("id"); gp.set_defaults(func=cmd_gate_pass)

    sub.add_parser("validate", help="check the whole project for contradictions").set_defaults(func=cmd_validate)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
