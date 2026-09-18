# System Walkthrough

A real session against the protagonist's system. Every block is actual output
from `tools/novel.py system`, captured against a scratch copy of the project at
chapter 1.

The doctrine is in [`../engine/system-engine.md`](../engine/system-engine.md);
this is what it looks like in use.

## Absorbing, and the rails that bite

Note what happens across the five `ambient_training` calls: the same source
pays 4, 3, 3, 2, 2. Familiarity decay means grinding one source stops working,
and finding a *new kind of ending* is always worth more — which pushes the plot
outward instead of into a training montage.

Note also that `failed_craft` at tier 4 pays 16 in one go. A Master's ruined
forging is worth four mornings of stolen student effort, and that is why the
professions matter to him.

```
$ novel.py system absorb ambient_training --scene "the third-form hall, an hour before dawn" --who-paid "forty students who trained until they shook"
+4 points  (clear mote from ambient_training, base 4 × decay 1.0)
  unspent: 4
  who paid: forty students who trained until they shook

$ ... and again from the same source, four more times (familiarity decay)
+3 points  (clear mote from ambient_training, base 4 × decay 0.82)
  unspent: 7
  who paid: the same students
+3 points  (clear mote from ambient_training, base 4 × decay 0.672)
  unspent: 10
  who paid: the same students
+2 points  (clear mote from ambient_training, base 4 × decay 0.551)
  unspent: 12
  who paid: the same students
+2 points  (clear mote from ambient_training, base 4 × decay 0.452)
  unspent: 14
  who paid: the same students

$ novel.py system absorb failed_craft --tier 4 --scene "..." --who-paid "..."
+16 points  (radiant mote from failed_craft, base 16 × decay 1.0)
  residue +1 → 1 (clear)
  unspent: 30
  who paid: Ilesh, three weeks of work and a month of materials
  NOTE: chapter 1 is over the soft cap (30/25). The reader is starting to feel the escalation.

$ novel.py system absorb ruin --tier 5 --scene "..." --who-paid "..."   # tainted source
absorption refused:
  - chapter hard cap: 67 > 60 points in chapter 1
  This is the anti-inflation rail. Re-run with --override and the engine will log the exception.

=== the anti-inflation rail ===
$ novel.py system absorb combat_kill --tier 5 --points 60 --scene "..." --who-paid "..."
absorption refused:
  - chapter hard cap: 90 > 60 points in chapter 1
  This is the anti-inflation rail. Re-run with --override and the engine will log the exception.
(exit 2)
```

Three refusals in that transcript, and none of them is a bug:

- **The soft cap warning** at 30/25 points — the engine telling you the reader
  is starting to feel the escalation.
- **The hard cap refusal** at 67 > 60 — the anti-inflation rail. `--override`
  exists and logs the exception with its reason.
- Every absorption required `--scene` and `--who-paid`. The second one is
  `LK-MOTE-COSTS`: nothing sheds essence without losing it. By chapter forty
  that log reads as a ledger of everyone he has taken from.

## Spending, realms, professions, traits

```
$ novel.py system spend strength 3
strength 9 → 12  (cost 5 points, 25 unspent)

$ novel.py system spend fortune 1        # refused on principle
refused: fortune is not bought. It rises almost never, and when it does someone nearby pays for it (LK-ESSENCE-FINITE, and the Thousand-Coin toll).
  Use --override if this is that scene.
(exit 2)

$ novel.py system realm --to 2 --scene "cornered on the quay stair"   # numbers not met
refused: Kindling needs physical_total 35/60, spirit 6/12
  Meeting the numbers only makes a breakthrough possible (LK-BREAKTHROUGH-COSTS).
(exit 2)

$ novel.py system realm      # advance one stage within Tempering
Tempering → gate 4

$ novel.py system profession forging --amount 12
forging: 0 → 12 proficiency (talent common on forging)
  RANK UP → 1 Apprentice
  Requires a certification piece made under observation. Failure is public and expensive.
  build credits available: 1

$ novel.py system profession forging --build strength
forging: 12 → 12 proficiency (talent common on forging)
  build credit spent: strength +1
  build credits available: 0

$ novel.py system technique "Sundering Palm" --grade profound --amount 30
Sundering Palm: 0 → 30
  band: rote → fluent

$ novel.py system trait thousand-coin --scene "he takes the windfall knowing whose it was"
Thousand-Coin: dormant → stirred
  gift: abnormal fortune in small things, compounding
  toll: the luck is conserved and taken from someone nearby, always someone known   (LK-TRAIT-TOLL — it lands on the page or the trait is a cheat)

$ novel.py system forecast

Cost to raise each attribute
----------------------------
 strength         13   +1 costs   2   +5 costs   10
 agility           7   +1 costs   1   +5 costs    7
 reflex            8   +1 costs   1   +5 costs    8
 constitution      8   +1 costs   1   +5 costs    8
 perception       12   +1 costs   2   +5 costs   10
 comprehension    14   +1 costs   2   +5 costs   10
 will             11   +1 costs   2   +5 costs   10
 spirit            6   +1 costs   1   +5 costs    6
 fortune           1   +1 costs   5   +5 costs   25
 affinity          0   +1 costs   5   +5 costs   25

To reach Kindling
-----------------
 physical_total 36/60
 spirit 6/12

 Rough cost if spread evenly: ~41 points (25 unspent, 106 earned so far)
 At the 25-point soft cap that is ~2 chapters of absorption.


$ novel.py system log --limit 4
6 absorption(s), 30 points:
 ch.  1    3pt  clear        ambient_training   paid by: the same students
          same hall, same hour
 ch.  1    2pt  clear        ambient_training   paid by: the same students
          same hall, same hour
 ch.  1    2pt  clear        ambient_training   paid by: the same students
          same hall, same hour
 ch.  1   16pt  radiant      failed_craft       paid by: Ilesh, three weeks of work and a month of materials
          Master Ilesh ruins a profound-grade spear head and walks out

Events
------
 ch.  0  baseline     Starting state at the opening of the novel. Appraisal Rank 1 and a keen formation talent are on record; the Tally is not.
 ch.  1  stage        Tempering -> gate 4
 ch.  1  trait        Thousand-Coin: dormant -> stirred
```

`fortune` refuses to be bought at all. In this world luck is conserved, and the
Thousand-Coin toll says whose it was. If a scene genuinely earns it, `--override`
is there.

## A breakthrough

Meeting the numbers only makes a breakthrough possible. It needs a scene, and it
bills the story's cost tracks in `progression.json`:

```
$ novel.py system realm --to 2 --scene "the quay stair, bleeding, with the tide coming in" --override
BREAKTHROUGH — Kindling (early)
  paid on the story's cost tracks: {'body': 1, 'anonymity': 1}  → now {'body': 7, 'anonymity': 8}
  familiarity reset: every source class pays full again. The frontier reopened.
  Essence ignites. It is survivable and it is not private — someone always feels it.
```

The familiarity reset is the reward loop: the first thing he does in a new realm
is go back over old ground and find it rich again.

## Validation

The system is checked by `novel.py validate` along with everything else. Here it
is catching a deliberately corrupted status file:

```
$ novel.py validate
ERROR   point accounting broken: 106 earned != 81 spent + 999 unspent
ERROR   residue is 80 but state says 'clear' (should be 'deviating')
ERROR   talent 'blade' has invalid rating 'godlike'
ERROR   profession 'forging' is rank 7 at 12 proficiency (should be 1)
warn    residue 80: a deviation event is due on the page
warn    current realm Kindling is held without meeting physical_total 36/60, spirit 6/12 (an override, or the numbers drifted)
```

That last warning is the useful one in practice: it tells you the protagonist is
holding a realm he has not actually paid for, either because you overrode a
breakthrough deliberately or because the numbers drifted underneath him.

## The readable sheet

`novel.py system sheet` regenerates
[`../engine/system-status.md`](../engine/system-status.md): realm, attributes,
what the next realm needs, talents, techniques, professions with unspent build
credits, bloodline traits with their gifts and tolls, the last forty absorptions
with who paid for each, and the event history.

It is the author's instrument. The numbers never appear in the prose — on the
page, strength is shown by what it does to a room.
