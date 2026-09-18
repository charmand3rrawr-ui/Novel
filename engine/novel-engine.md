# The Novel Engine

The engine's job is to make the novel's pacing a decision rather than a mood.
It never writes prose. It answers one question: *given where the story is, what
does the next chapter owe the reader, and what is it forbidden to spend?*

Run it with `tools/novel.py`.

## The four dials

### 1. Beat (`tempo.json → beat_cycle`)

Chapters rotate through six beats: **hook → pressure → complication → cost →
revelation → consolidation**. The cycle is a floor, not a ceiling. Its purpose
is to stop the two failure modes of long-form serial fiction: eight chapters of
escalation with no consolidation, or four chapters of consolidation with no
cost.

### 2. Tension (`tempo.json → tension_curve`)

Each arc declares an opening, peak, and closing tension. The engine interpolates
a target for every chapter, peaks at three-quarter depth, then releases. Rest
chapters cut the target by `release_depth` so the reader can breathe.

Deviate by one, deliberately, and log why. Deviate by three and you have a
different novel than the one the arcs describe.

### 3. Introduction budget (`tempo.json → introduction_budget`)

This is the rule that makes the whole framework work:

> A character or environment exists in full long before the reader meets them,
> and meets the reader only when the storyline needs them.

The budget makes that enforceable. Four named characters per arc. Two
environments per arc. One environment per chapter. A cooldown after any major
introduction. `character introduce` and `env activate` refuse past the budget,
and refuse a role or place the current arc does not license. `--override`
exists, and it writes the exception into `state.json`'s log with your reason.

**Why a budget rather than judgement:** in serial fiction the failure is never
one bad decision, it is thirty small ones. A cast grows by one reasonable
person at a time until no one is on the page often enough to matter.

### 4. Progression (`progression.json`)

Two ladders run side by side, and they are welded together at the breakthroughs.

- **`progression.json` is who he becomes** — the story tracks below.
- **`system-status.json` is what he can do** — attributes, realm, techniques,
  professions. See [`system-engine.md`](system-engine.md).

Every realm breakthrough debits this file's cost tracks, so power cannot rise
without the person paying for it.

The protagonist has three groups of tracks:

- **capability** — craft, authority, insight, endurance, reach
- **cost** — intimacy, integrity, anonymity, body
- **internal** — lie_grip and its mirror, self_knowledge

`novel.py advance craft --cost anonymity` is the only way capability rises, and
it requires naming the cost. Growth is also rationed against the page count: a
track may not exceed its starting value plus `chapter / 6` before Act III. The
protagonist cannot outrun the novel.

`lie_grip` falls only after an on-page refusal, failure, or confrontation —
never from reflection. `self_knowledge` is always `10 - lie_grip`; the
validator enforces it.

**Gates** are the named thresholds where progression becomes plot. Each says
what it requires, what it unlocks, what it costs, and what must happen on the
page for it to count.

## The daily loop

```
novel.py status                 # where am I
novel.py plan                   # what does this chapter owe
novel.py brief                  # what must it not contradict
        ... write the chapter ...
novel.py chapter record 7 --title "..." --summary "..." --tension 6 \
    --kind conflict --characters mc-kestrel-vane,sila-corr --environments academy-thorn-ledger
novel.py chapter point 7 --kind promise --text "..." --weight 5 --tags ledger,corr
novel.py seed plant --id th-corr-favour --summary "..."
novel.py chapter close --tension 6 --kind conflict
novel.py continuity sync
novel.py validate
```

## When the engine says no

It refuses in three situations, and each refusal is information:

1. **Budget spent.** You want a new character and the arc has had its four.
   Usually the right answer is that an existing character should do this job —
   which is almost always the better scene.
2. **Not licensed by the arc.** You want an orbital station in Arc 1. Either the
   arc is wrong or the scene is early.
3. **Progression ceiling.** The protagonist would gain a capability the story
   has not paid for yet. Write the chapter that earns it.

`--override` is always available. It is not a failure to use it; it is a
failure to use it without a reason in the log.

## Files

| File | What it holds |
|---|---|
| `system-engine.md` | the protagonist's system: absorption, realms, traits, professions |
| `system.json` | how that system works — sources, mote tiers, caps, realms, traits |
| `system-status.json` | where he is: stats, points, residue, and the full absorption log |
| `tempo.json` | beats, tension curve, cadence rules, budgets, seed policy |
| `progression.json` | the protagonist's tracks, exchange rules, gates, development spine |
| `arcs.json` | acts, arcs, promises, licensed roles and environments |
| `state.json` | live position: chapter, arc, on-stage cast, budgets spent, log |
