"""Command line for the novel engine. `tools/novel.py --help` for the map."""

from __future__ import annotations

import argparse
import sys

from . import calibrate, characters, continuity, engine, environments, framework, plotgen, store, system, validate

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


# ------------------------------------------------------------------- system

def cmd_system_status(args):
    cfg, s = system.config(), system.status()
    tot = system.totals(s)
    _p(BAR)
    _p(f" {cfg['system']['name'].upper()} — {s['owner']}")
    _p(BAR)
    _p(f" Realm   : {s['realm']['name']} · {s['realm']['stage']}  (since ch.{s['realm'].get('since_chapter', '?')})")
    _p(f" Points  : {s['points']['unspent']} unspent · {s['points']['lifetime_earned']} lifetime")
    _p(f" Residue : {s['residue']['value']} — {s['residue']['state']}")
    if s["residue"]["value"]:
        _p(f"           {system.residue_effect(cfg, s['residue']['value'])}")
    _h("Attributes")
    _p(" physical  " + "  ".join(f"{k}:{s['attributes'].get(k, 0)}" for k in system.PHYSICAL)
       + f"   (total {tot['physical_total']})")
    _p(" mental    " + "  ".join(f"{k}:{s['attributes'].get(k, 0)}" for k in system.MENTAL)
       + f"   (total {tot['mental_total']})")
    _p(" rare      " + "  ".join(f"{k}:{s['attributes'].get(k, 0)}" for k in system.RARE))
    nxt = s["realm"]["n"] + 1
    if any(r["n"] == nxt for r in cfg["realms"]):
        target = system.realm_by_n(cfg, nxt)
        gap = system.realm_gap(cfg, s, nxt)
        _h(f"Next realm — {target['name']}")
        _p(" needs: " + (", ".join(gap) if gap else "requirements MET — it still has to happen in a scene"))
        if target.get("cost"):
            _p(f" cost : {target['cost']}")
    caps = cfg["absorption_rules"]["caps"]
    _h("Absorption budget")
    _p(f" chapter {s['per_chapter']['chapter']}: {s['per_chapter']['points']} points "
       f"(soft {caps['points_per_chapter_soft']}, hard {caps['points_per_chapter_hard']})")
    _p(f" arc {s['per_arc']['arc']}: {s['per_arc']['points']} points (hard {caps['points_per_arc_hard']})")
    if s["familiarity"]:
        _p(" familiarity: " + ", ".join(
            f"{k}×{v} (→{max(cfg['absorption_rules']['familiarity_decay']['floor'], cfg['source_classes'][k]['decay'] ** v):.2f})"
            for k, v in sorted(s["familiarity"].items())))
    _p("")
    return 0


def cmd_system_sheet(args):
    store.write_text(system.SHEET, system.render_sheet())
    _p(f"Wrote {store.rel(system.SHEET)}")
    return 0


def cmd_system_absorb(args):
    try:
        r = system.absorb(args.source, scene=args.scene, who_paid=args.who_paid, tier=args.tier,
                          points=args.points, note=args.note or "", override=args.override)
    except PermissionError as exc:
        _p(str(exc))
        return 2
    e = r["entry"]
    _p(f"+{e['points']} points  ({e['tier_name']} mote from {e['source_class']}, "
       f"base {e['base_points']} × decay {e['decay_multiplier']})")
    if e["residue"]:
        _p(f"  residue +{e['residue']} → {r['status']['residue']['value']} ({r['status']['residue']['state']})")
    _p(f"  unspent: {r['status']['points']['unspent']}")
    _p(f"  who paid: {e['who_paid']}")
    if r["soft_cap_hit"]:
        _p(f"  NOTE: chapter {e['chapter']} is over the soft cap ({r['status']['per_chapter']['points']}"
           f"/{r['soft_cap']}). The reader is starting to feel the escalation.")
    if r["warnings"]:
        _p("  OVERRIDE logged: " + "; ".join(r["warnings"]))
    return 0


def cmd_system_spend(args):
    try:
        r = system.spend(args.attribute, args.amount, override=args.override)
    except PermissionError as exc:
        _p(str(exc))
        return 2
    _p(f"{r['attribute']} {r['from']} → {r['to']}  (cost {r['cost']} points, {r['remaining']} unspent)")
    return 0


def cmd_system_train(args):
    r = system.train(args.attribute, args.amount, scene=args.scene, note=args.note or "")
    _p(f"{r['attribute']} {r['from']} → {r['to']}  (earned by work — no points, nothing died)")
    return 0


def cmd_system_technique(args):
    r = system.technique(args.name, amount=args.amount, grade=args.grade,
                         spend_points=args.spend, scene=args.scene or "")
    _p(f"{r['name']}: {r['from']} → {r['to']}" + (f" (cost {r['cost']} points)" if r["cost"] else ""))
    if r["band_change"]:
        _p(f"  band: {r['band_change'][0]} → {r['band_change'][1]}")
        if r["earned_band"] and not r["scene"]:
            _p("  NOTE: mastery and origin bands must be earned in a scene, not bought. Record the scene.")
    return 0


def cmd_system_profession(args):
    try:
        r = system.profession(args.discipline, amount=args.amount, take_build=args.build or "")
    except PermissionError as exc:
        _p(str(exc))
        return 2
    _p(f"{r['discipline']}: {r['from']} → {r['to']} proficiency "
       f"(talent {r['talent']} on {r['talent_axis']})")
    if r["rank_up"]:
        _p(f"  RANK UP → {r['rank']['rank']} {r['rank']['name']}")
        _p("  Requires a certification piece made under observation. Failure is public and expensive.")
    if r["build_applied"]:
        _p(f"  build credit spent: {r['build_applied']} +1")
    _p(f"  build credits available: {r['credits_available']}")
    return 0


def cmd_system_realm(args):
    try:
        r = system.breakthrough(args.to, stage=args.stage or "", scene=args.scene or "",
                                override=args.override)
    except PermissionError as exc:
        _p(str(exc))
        return 2
    if r["kind"] == "stage":
        _p(f"{r['realm']} → {r['stage']}")
        return 0
    _p(f"BREAKTHROUGH — {r['realm']} ({r['stage']})")
    if r["cost"]:
        _p(f"  paid on the story's cost tracks: {r['cost']}  → now {r['paid']}")
    if r["familiarity_reset"]:
        _p("  familiarity reset: every source class pays full again. The frontier reopened.")
    if r.get("on_page"):
        _p(f"  {r['on_page']}")
    return 0


def cmd_system_trait(args):
    r = system.trait(args.id, state=args.state or "", scene=args.scene or "", notes=args.notes or "")
    _p(f"{r['trait']['name']}: {r['from']} → {r['to']}")
    _p(f"  gift: {r['trait']['gift']}")
    _p(f"  toll: {r['trait']['toll']}   (LK-TRAIT-TOLL — it lands on the page or the trait is a cheat)")
    return 0


def cmd_system_talent(args):
    r = system.talent(args.discipline, args.rating)
    _p(f"{r['discipline']}: {r['from']} → {r['to']} ({r['multiplier']}× rate)")
    return 0


def cmd_system_purge(args):
    r = system.purge(args.amount, args.method, scene=args.scene or "")
    _p(f"residue {r['from']} → {r['to']} ({r['state']}) via {r['method']}")
    return 0


def cmd_system_log(args):
    s = system.status()
    log = s["absorption_log"]
    if args.chapter is not None:
        log = [e for e in log if e["chapter"] == args.chapter]
    if not log:
        _p("Nothing absorbed" + (f" in chapter {args.chapter}" if args.chapter is not None else "") + ".")
    else:
        total = sum(e["points"] for e in log)
        _p(f"{len(log)} absorption(s), {total} points:")
        for e in log[-args.limit:]:
            _p(f" ch.{e['chapter']:>3}  {e['points']:>3}pt  {e['tier_name']:<12} {e['source_class']:<18} "
               f"paid by: {e['who_paid']}")
            if e.get("scene"):
                _p(f"          {e['scene']}")
    if s["events"]:
        _h("Events")
        for e in s["events"][-args.limit:]:
            _p(f" ch.{e['chapter']:>3}  {e['kind']:<12} {e['text']}")
    return 0


def cmd_system_forecast(args):
    cfg, s = system.config(), system.status()
    _h("Cost to raise each attribute")
    for group, names in (("physical", system.PHYSICAL), ("mental", system.MENTAL), ("rare", system.RARE)):
        for name in names:
            v = s["attributes"].get(name, 0)
            _p(f" {name:14} {v:>4}   +1 costs {system.raise_cost(cfg, name, v, v + 1):>3}   "
               f"+5 costs {system.raise_cost(cfg, name, v, v + 5):>4}")
    nxt = s["realm"]["n"] + 1
    if any(r["n"] == nxt for r in cfg["realms"]):
        target = system.realm_by_n(cfg, nxt)
        gap = system.realm_gap(cfg, s, nxt)
        _h(f"To reach {target['name']}")
        if not gap:
            _p(" Requirements met. It needs a scene, pressure, and a cost that does not come back.")
        else:
            for g in gap:
                _p(f" {g}")
            tot = system.totals(s)
            need_phys = max(0, target["requires"].get("physical_total", 0) - tot["physical_total"])
            need_ment = max(0, target["requires"].get("mental_total", 0) - tot["mental_total"])
            est = 0
            for names, need in ((system.PHYSICAL, need_phys), (system.MENTAL, need_ment)):
                per = need // len(names)
                for n in names:
                    v = s["attributes"].get(n, 0)
                    est += system.raise_cost(cfg, n, v, v + per)
            _p(f"\n Rough cost if spread evenly: ~{est} points "
               f"({s['points']['unspent']} unspent, {s['points']['lifetime_earned']} earned so far)")
            caps = cfg["absorption_rules"]["caps"]
            _p(f" At the {caps['points_per_chapter_soft']}-point soft cap that is "
               f"~{max(1, round(est / caps['points_per_chapter_soft']))} chapters of absorption.")
    _p("")
    return 0


# ---------------------------------------------------------------- frameworks

def cmd_framework_new(args):
    n = args.number
    path = framework.path_for(n)
    if path.exists() and not args.force:
        _p(f"{store.rel(path)} already exists. Use --force to regenerate (it will overwrite your fills).")
        return 1
    text = framework.generate(n, shape_id=args.shape or "", cast=_csv(args.characters) or None,
                              stages=_csv(args.environments) or None, pov=args.pov or "")
    store.write_text(path, text)
    r = framework.check(n)
    _p(f"Wrote {r['path']}  ({r['words']} words, minimum {r['min_words']})")
    _p(f"  {r['unfilled_prompts']} prompts to fill in — search for _<")
    _p(f"  Check with: novel.py framework check {n}")
    return 0


def cmd_framework_check(args):
    rows = [framework.check(args.number)] if args.number else framework.listing()
    if not rows:
        _p("No frameworks yet. `novel.py framework new 1`")
        return 0
    bad = 0
    for r in rows:
        flag = "ok " if r["ok"] else "FIX"
        if not r["ok"]:
            bad += 1
        _p(f" {flag} ch.{r['chapter']:<4} {r['words']:>5} words  "
           f"{r['unfilled_prompts']:>3} unfilled  {r['path']}")
        if r["missing_sections"]:
            _p(f"      missing sections: {', '.join(r['missing_sections'])}")
        if not r["long_enough"]:
            _p(f"      under the {r['min_words']}-word minimum by {r['min_words'] - r['words']}")
    if len(rows) > 1:
        done = sum(1 for r in rows if r["ok"] and r["unfilled_prompts"] == 0)
        _p("")
        _p(f" {len(rows)} framework(s): {done} complete, "
           f"{sum(1 for r in rows if r['unfilled_prompts'])} still carrying prompts, {bad} failing.")
    return 1 if bad else 0


def cmd_framework_shapes(args):
    data = framework.shapes()
    rows = framework.suggest_shapes(args.beat) if args.beat else data["shapes"]
    if args.beat:
        _p(f"Shapes that serve a '{args.beat}' beat:\n")
    for s in rows:
        _p(f" {s['id']:<20} {s['name']}")
        _p(f"   {s['for']}")
        _p(f"   open: {s['open']}")
        _p(f"   turn: {s['turn']}")
        _p(f"   close: {s['close']}")
        _p(f"   costs: {s['costs']}  ·  serves: {', '.join(s.get('serves_beats', []))}")
        _p("")
    return 0


def cmd_calibrate(args):
    for line in calibrate.report():
        _p(line)
    return 0


# --------------------------------------------------------------------- plot

def cmd_plot_build(args):
    sk = plotgen.build(total=args.chapters, seed=args.seed)
    store.save(plotgen.SKELETON, sk)
    _p(f"Built a {sk['total_chapters']}-chapter skeleton (seed {sk['seed']}).")
    _p(f"  {len(sk['volumes'])} volumes, {len(sk['arcs'])} arcs, {len(sk['seeds'])} planned seeds")
    lens = [a["length"] for a in sk["arcs"]]
    lens.sort()
    _p(f"  arc lengths: median {lens[len(lens) // 2]}, min {lens[0]}, max {lens[-1]}")
    from collections import Counter
    c = Counter(sk["chapter_types"])
    _p("  chapter types: " + ", ".join(f"{k} {v * 100 // len(sk['chapter_types'])}%"
                                       for k, v in c.most_common()))
    _p(f"  written to {store.rel(plotgen.SKELETON)}")
    if args.sync:
        n = _sync_arcs(sk)
        _p(f"  synced {n} arcs into engine/arcs.json")
    return 0


def _sync_arcs(sk):
    """Project the skeleton into engine/arcs.json so the tempo engine, the
    framework generator and validate all see the same structure."""
    acts = []
    for v in sk["volumes"]:
        acts.append({"id": v["id"], "name": f"Volume {v['id'][1:]}", "arcs": v["arcs"]})
    arcs = []
    for a in sk["arcs"]:
        arcs.append({
            "id": a["id"], "name": f"Arc {a['id'][1:]}", "chapters": a["chapters"],
            "promise": a["promise"], "central_question": a["central_question"],
            "pressure_source": a["pressure_source"],
            "licensed_environments": a["licensed_environments"],
            "licensed_character_roles": a["licensed_character_roles"],
            "closes_on": a["closes_on"], "tension": a["tension"],
        })
    store.save(store.ARCS, {"description": "Projected from engine/plot-skeleton.json by `novel.py plot build "
                                           "--sync`. Edit the skeleton, not this file.",
                            "acts": acts, "arcs": arcs})
    return len(arcs)


def cmd_plot_show(args):
    sk = plotgen.skeleton()
    n = args.chapter or store.load(store.STATE)["current_chapter"]
    arc = plotgen.arc_for(sk, n)
    vol = plotgen.volume_for(sk, n)
    if not arc:
        _p(f"chapter {n} is outside the skeleton (1-{sk['total_chapters']})")
        return 1
    _p(BAR)
    _p(f" Chapter {n}  ·  {vol['id'] if vol else '?'} / {arc['id']}  ·  "
       f"phase {plotgen.phase_for(arc, n)}  ·  type {plotgen.chapter_type(sk, n)}")
    _p(BAR)
    _p(f" Arc {arc['id']}: chapters {arc['chapters'][0]}-{arc['chapters'][1]} ({arc['length']})")
    _p(f" Question : {arc['central_question']}")
    _p(f" Pressure : {arc['pressure_source']}")
    _p(f" Stake    : {arc['stake']}")
    _p(f" Closes on: {arc['closes_on']}")
    _p(f" Licensed : {', '.join(arc['licensed_environments'])} | {', '.join(arc['licensed_character_roles'])}")
    _h("Phases")
    for seg in arc["phases"]:
        mark = " <-- here" if seg["from"] <= n <= seg["to"] else ""
        _p(f"  {seg['phase']:<14} ch.{seg['from']}-{seg['to']}{mark}")
    _h("Chapter types in this arc")
    row = [plotgen.chapter_type(sk, c) for c in range(arc["chapters"][0], arc["chapters"][1] + 1)]
    _p("  " + " ".join(t[:3] for t in row))
    nearby = [s for s in sk["realm_plan"] if abs(s["target_chapter"] - n) <= 60]
    if nearby:
        _h("Ladder nearby")
        for s in nearby:
            _p(f"  ch.{s['target_chapter']:<6} {s['realm']} {s['stage']}"
               + ("  [BREAKTHROUGH]" if s["is_breakthrough"] else ""))
    return 0


def cmd_plot_arcs(args):
    sk = plotgen.skeleton()
    for v in sk["volumes"]:
        _p(f"\n{v['id']}  chapters {v['chapters'][0]}-{v['chapters'][1]}")
        for aid in v["arcs"]:
            a = next(x for x in sk["arcs"] if x["id"] == aid)
            _p(f"  {a['id']}  ch.{a['chapters'][0]:>5}-{a['chapters'][1]:<5} ({a['length']:>3})  "
               f"{a['pressure_source']}")
            if args.verbose:
                _p(f"        {a['central_question']}")
    return 0


def cmd_plot_next(args):
    d = plotgen.derive(args.chapter)
    _p(BAR)
    _p(f" WHAT THE PLOT OWES — chapter {d['chapter']}  ·  arc {d['arc']}  ·  "
       f"phase {d['phase']}  ·  type {d['chapter_type']}")
    _p(BAR)
    _p(f" Arc question: {d['arc_question']}")
    _p(f" Arc pressure: {d['arc_pressure']}")
    if d["divergence"]:
        _h("Divergence from the plan")
        for x in d["divergence"]:
            _p(f" ! {x}")
    if d["directives"]:
        _h("Driven by his current state")
        for kind, text in d["directives"]:
            _p(f" [{kind}] {text}")
    else:
        _p("")
        _p(" No state-driven directives. The arc plan stands.")
    if d["seeds_planting"]:
        _h("Seeds the plan plants here")
        for s in d["seeds_planting"]:
            _p(f"  plant now, pay at ch.{s['target_payoff']} ({s['band']}, {s['gap']} chapters)")
    if d["seeds_due"]:
        _h("Seeds due for payoff here")
        for s in d["seeds_due"]:
            _p(f"  planted ch.{s['planted_chapter']} ({s['gap']} chapters carried, {s['band']})")
    _p("")
    return 0


def cmd_plot_cast(args):
    """Generate the bench an arc's phases call for. Personalities are random —
    contradictory atoms drawn from the lexicon — and every one carries the arc's
    own need, so `character introduce` has a sentence to check against."""
    sk = plotgen.skeleton()
    arc = next((a for a in sk["arcs"] if a["id"] == args.arc), None)
    if not arc:
        _p(f"unknown arc '{args.arc}'. Try `novel.py plot arcs`.")
        return 1
    wanted = []
    for seg in arc["phases"]:
        for role in plotgen.ROLES_BY_PHASE[seg["phase"]]:
            if role in arc["licensed_character_roles"] and role not in [w[0] for w in wanted]:
                wanted.append((role, seg["phase"]))
    if args.limit:
        wanted = wanted[:args.limit]
    if not wanted:
        _p(f"{arc['id']} licenses {arc['licensed_character_roles']}, none of which its phases call for.")
        return 0
    rng = __import__("random").Random(args.seed if args.seed is not None else arc["chapters"][0])
    made = []
    for role, phase in wanted:
        need = (f"{arc['id']} ({phase} phase): {arc['pressure_source']} needs a {role} for the arc to "
                f"put {arc['stake']} at risk")
        c = characters.generate(role, need=need, culture=args.culture,
                                seed=rng.randrange(1 << 30))
        try:
            characters.persist(c)
        except ValueError:
            continue
        made.append(c)
        _p(f" {c['name']:<24} {role:<18} seed {c['seed']}")
        _p(f"   lie:  {c['core']['lie']}")
        _p(f"   mask: {c['surface']['mask']}")
        _p(f"   hole: {c['capability']['hole']}")
    _p("")
    _p(f"{len(made)} benched for {arc['id']}. None are on the page until "
       "`novel.py character introduce <id> --need \"...\"`.")
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

    sy = sub.add_parser("system", help="the protagonist's attribute system: absorption, realms, traits, professions")
    sysub = sy.add_subparsers(dest="sub", required=True)
    sysub.add_parser("status", help="where the protagonist stands in the system").set_defaults(func=cmd_system_status)
    sysub.add_parser("sheet", help="regenerate engine/system-status.md").set_defaults(func=cmd_system_sheet)

    ab = sysub.add_parser("absorb", help="absorb motes from a source that ended")
    ab.add_argument("source", help="source class, e.g. ambient_training, combat_kill, failed_craft, ruin")
    ab.add_argument("--scene", required=True, help="where on the page this happened (witness rule)")
    ab.add_argument("--who-paid", required=True, dest="who_paid",
                    help="who or what lost this essence (LK-MOTE-COSTS)")
    ab.add_argument("--tier", type=int, help="mote tier 1-5; defaults to the class median")
    ab.add_argument("--points", type=int, help="explicit point value before decay")
    ab.add_argument("--note", default="")
    ab.add_argument("--override", action="store_true")
    ab.set_defaults(func=cmd_system_absorb)

    sp2 = sysub.add_parser("spend", help="spend points to raise an attribute")
    sp2.add_argument("attribute"); sp2.add_argument("amount", type=int, nargs="?", default=1)
    sp2.add_argument("--override", action="store_true")
    sp2.set_defaults(func=cmd_system_spend)

    tn = sysub.add_parser("train", help="attributes earned by work rather than absorption")
    tn.add_argument("attribute"); tn.add_argument("amount", type=int)
    tn.add_argument("--scene", required=True); tn.add_argument("--note")
    tn.set_defaults(func=cmd_system_train)

    tq = sysub.add_parser("technique", help="record or raise a technique's proficiency")
    tq.add_argument("name"); tq.add_argument("--amount", type=int, default=0)
    tq.add_argument("--grade", default="common",
                    choices=["common", "refined", "profound", "heavenly", "origin"])
    tq.add_argument("--spend", action="store_true", help="pay for it with system points")
    tq.add_argument("--scene")
    tq.set_defaults(func=cmd_system_technique)

    pf = sysub.add_parser("profession", help="raise a profession and take its build credits")
    pf.add_argument("discipline"); pf.add_argument("--amount", type=int, default=0)
    pf.add_argument("--build", help="attribute to spend a build credit on")
    pf.set_defaults(func=cmd_system_profession)

    rm = sysub.add_parser("realm", help="advance a stage, or break through to the next realm")
    rm.add_argument("--to", type=int, help="target realm number; omit to advance one stage")
    rm.add_argument("--stage"); rm.add_argument("--scene")
    rm.add_argument("--override", action="store_true")
    rm.set_defaults(func=cmd_system_realm)

    tr = sysub.add_parser("trait", help="advance a bloodline trait")
    tr.add_argument("id"); tr.add_argument("--state", choices=["dormant", "stirred", "awakened", "ascended"])
    tr.add_argument("--scene"); tr.add_argument("--notes")
    tr.set_defaults(func=cmd_system_trait)

    tl = sysub.add_parser("talent", help="set a talent rating")
    tl.add_argument("discipline"); tl.add_argument("rating",
                    choices=["dull", "common", "keen", "rare", "heaven-sent"])
    tl.set_defaults(func=cmd_system_talent)

    pg = sysub.add_parser("purge", help="clear residue")
    pg.add_argument("amount", type=int)
    pg.add_argument("--method", required=True, choices=["alchemy", "cooking", "time"])
    pg.add_argument("--scene")
    pg.set_defaults(func=cmd_system_purge)

    lg = sysub.add_parser("log", help="the absorption and event log")
    lg.add_argument("--chapter", type=int); lg.add_argument("--limit", type=int, default=25)
    lg.set_defaults(func=cmd_system_log)

    sysub.add_parser("forecast", help="what the next realm costs in points and chapters").set_defaults(func=cmd_system_forecast)

    fw = sub.add_parser("framework", help="per-chapter framework documents (see chapters/FRAMEWORK-SPEC.md)")
    fwsub = fw.add_subparsers(dest="sub", required=True)
    fn = fwsub.add_parser("new", help="scaffold a framework from live engine state")
    fn.add_argument("number", type=int)
    fn.add_argument("--shape", help="chapter shape id; omit to let the beat choose")
    fn.add_argument("--characters", default=""); fn.add_argument("--environments", default="")
    fn.add_argument("--pov", default=""); fn.add_argument("--force", action="store_true")
    fn.set_defaults(func=cmd_framework_new)
    fc = fwsub.add_parser("check", help="verify length and required sections")
    fc.add_argument("number", type=int, nargs="?")
    fc.set_defaults(func=cmd_framework_check)
    fs = fwsub.add_parser("shapes", help="list the chapter-shape archetypes")
    fs.add_argument("--beat", choices=["hook", "pressure", "complication", "cost", "revelation", "consolidation"])
    fs.set_defaults(func=cmd_framework_shapes)

    pl2 = sub.add_parser("plot", help="the macro plot skeleton, and what the protagonist's state does to it")
    plsub = pl2.add_subparsers(dest="sub", required=True)
    pb = plsub.add_parser("build", help="generate the skeleton")
    pb.add_argument("--chapters", type=int, default=1337)
    pb.add_argument("--seed", type=int)
    pb.add_argument("--sync", action="store_true", help="project it into engine/arcs.json")
    pb.set_defaults(func=cmd_plot_build)
    ps = plsub.add_parser("show", help="where a chapter sits in the plan")
    ps.add_argument("--chapter", type=int); ps.set_defaults(func=cmd_plot_show)
    pa = plsub.add_parser("arcs", help="the whole arc map")
    pa.add_argument("--verbose", action="store_true"); pa.set_defaults(func=cmd_plot_arcs)
    pn = plsub.add_parser("next", help="what the plot owes, driven by his current state")
    pn.add_argument("--chapter", type=int); pn.set_defaults(func=cmd_plot_next)
    pc = plsub.add_parser("cast", help="generate the bench an arc's phases call for")
    pc.add_argument("arc"); pc.add_argument("--limit", type=int, default=4)
    pc.add_argument("--culture", default="ledger", choices=sorted(characters.SYLLABLES))
    pc.add_argument("--seed", type=int)
    pc.set_defaults(func=cmd_plot_cast)

    sub.add_parser("calibrate", help="compare the tempo against genre architecture").set_defaults(func=cmd_calibrate)
    sub.add_parser("validate", help="check the whole project for contradictions").set_defaults(func=cmd_validate)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
