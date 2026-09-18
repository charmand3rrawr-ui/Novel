# Plot Architecture

Not plot — the *organisation* of plot. What kind of chapter follows what kind,
how long a mode sustains, whether confrontation runs on a schedule, where the
cast turns over, and how far a setup travels before it is cashed.

Measured from `serial-reference-A` (3,204 chapters) with
`tools/analyze_structure.py --deep --craft --plot`. Chapter types are assigned
by which plot register is most elevated **relative to that register's own
corpus norm**, so a naturally common register cannot win every chapter.

---

## 1. Six modes, evenly rotated

| Chapter type | Share |
|---|--:|
| revelation | 19.9% |
| combat | 17.8% |
| mixed | 17.3% |
| travel | 16.9% |
| negotiation | 15.8% |
| training | 12.3% |

No mode dominates. The most common single type is **revelation** — something
being discovered, revealed or understood — not combat. Training, the mode the
genre is caricatured by, is the *rarest* at 12.3%.

---

## 2. The transition matrix — the central finding

Probability that a chapter of the row type is followed by each column type:

| from ↓ / to → | combat | training | negotiation | travel | revelation | mixed |
|---|--:|--:|--:|--:|--:|--:|
| **combat** | **50.2%** | 10.0% | 9.6% | 8.8% | 9.6% | 11.8% |
| travel | 11.6% | 8.7% | 11.8% | **36.2%** | 17.5% | 14.2% |
| revelation | 9.3% | 11.5% | 17.1% | 15.4% | **28.3%** | 18.5% |
| training | 12.2% | **27.4%** | 14.0% | 11.9% | 21.3% | 13.2% |
| negotiation | 12.8% | 9.5% | **26.4%** | 13.0% | 20.5% | 17.8% |
| mixed | 9.0% | 11.0% | 16.3% | 15.4% | 21.5% | 26.8% |

**Combat is the only strongly self-sustaining mode at 50.2%.** Every other type
sits between 26% and 36% on its own diagonal. A fight is twice as likely to be
followed by another fight as anything else is to repeat itself.

Read the combat row across: after a fight, the successor distribution is almost
flat — roughly 9–12% to each of the other five. The form does not resolve a
fight into a negotiation or a journey. It either keeps fighting or moves on to
anything at all, with no preference.

Second finding, easy to miss: **revelation is the most common destination from
almost every row.** From training (21.3%), from negotiation (20.5%), from mixed
(21.5%), from travel (17.5%). Whatever a chapter was doing, the likeliest next
move is that something gets found out. That is the real engine.

---

## 3. Modes are single chapters; combat is the exception

| Type | Median run | Max run | Share of runs that are one chapter |
|---|--:|--:|--:|
| combat | 1 | **23** | 60% |
| travel | 1 | 12 | 69% |
| negotiation | 1 | 7 | 76% |
| training | 1 | 6 | 76% |
| revelation | 1 | 6 | 74% |
| mixed | 1 | 6 | 76% |

Every mode has a median run of exactly one chapter. The form rotates fast. But
combat has a long tail the others do not — extended set-pieces up to **23
consecutive chapters**, while nothing else exceeds 12.

*Implication:* the architecture is "rotate every chapter, except when you commit
to a battle, and then commit completely."

---

## 4. Confrontation is clustered, not scheduled

Autocorrelation of combat density: r = 0.62 at lag 1, 0.53 at lag 2, 0.47 at
lag 3, 0.45 at lag 4, 0.41 at lag 5 — a smooth decay with **no periodic peak**
anywhere out to lag 30.

High short-lag correlation with no cycle means combat density comes in **bursts
rather than on a rhythm**. There is no "fight every six chapters" metronome.
When the story needs a confrontation it runs several in a row, then leaves it
alone for a long time.

*Implication:* do not schedule your confrontations on a cadence. The tempo
engine should govern tension, not fight frequency — which is how
`engine/tempo.json` already works, and this is evidence it was the right call.

---

## 5. Arc length, measured from cast turnover

Arc boundaries found by entity replacement: where the set of named things in
the previous 10 chapters barely overlaps the next 10.

- Median overlap between adjacent windows: **0.279**
- Boundaries detected: **58**
- Median gap between boundaries: **29 chapters** (p10 10, p90 141)

That 0.279 median is the headline: at any given point, only about a quarter of
the named things in play will still be in play ten chapters later. The cast is
in constant churn.

**Measured arc length is ~29 chapters.** Your arcs are 12–16.

---

## 6. Setup and payoff — the novel's memory

Every gap where a named entity disappears and later returns:

- Absences recorded: **64,219**
- Median absence: **9 chapters**
- Absences of 20+ chapters that still return: **22,571 (35.1%)**
- Of those long returns: median **65 chapters**, p90 **475**, max **3,061**

**A third of all disappearances are long returns, and the typical one is gone
for 65 chapters before coming back.** The form plants deep and cashes late, far
more than its reputation suggests.

This is the sharpest conflict with your current engine. `tempo.json` sets the
seed payoff window at min 3, soft_max 15, **hard_max 30** — past which
`validate` raises the thread as *rot* and demands you pay, repurpose or retire
it. The measured median long return is **65 chapters**, more than twice your rot
threshold. Your engine would force-retire exactly the plants this form is built
on.

---

## What to change

Ranked by how much it matters:

1. **Raise the rot threshold.** `hard_max: 30` is wrong for a serial. Measured
   practice is a median long return of 65 and a p90 of 475. Suggest soft_max 40,
   hard_max 120 — and treat rot as a warning rather than an error past 40.
2. **Decide arc length deliberately.** Measured ~29 chapters against your 12–16.
   If you are writing a serial, your arcs are half the length the form uses.
3. **Let combat chain.** `max_consecutive_action_chapters: 3` against a measured
   max run of 23 and a 50.2% self-transition. Three is a literary novel's limit.
   If you want extended set-pieces, raise it or exempt a declared battle.
4. **Make revelation the default successor.** It is the most likely next move
   from nearly every mode. `revelation_every: 8` in your tempo treats it as a
   rationed event; measured, it is the connective tissue — 19.9% of all chapters.
5. **Do not schedule confrontation.** Already correct in your engine; the data
   confirms it.

---

## Caveats

One serial, translated. Chapter typing is lexical, not semantic — a chapter
about a negotiation that happens to use combat vocabulary will be scored as
combat. The transition matrix is robust to that (the diagonal dominance of
combat survives any reasonable relabelling), but the exact percentages should
be read as approximate.

Arc boundaries are inferred from cast replacement alone. They are a good proxy
and they are not the author's chapter breaks.
