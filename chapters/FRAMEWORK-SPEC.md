# Chapter Framework Spec

A **framework** is the document you write before the chapter and read while
writing it. One per chapter, in `chapters/frameworks/ch-NNN.md`, **minimum 500
words**. `novel.py framework check` enforces both the length and the sections.

It is not an outline of events. An outline says what happens; a framework says
*why this chapter exists, who wants what inside it, and what it costs them* —
so that when you sit down to write, every scene decision has an answer already.

## Required sections

Eleven, in this order. The generator scaffolds all of them from live engine
state; you fill the judgement.

### 1. Header
Chapter number, act and arc, beat from the tempo, tension target, word target,
POV, and the chapter **shape** from `chapters/shapes.json`.

### 2. Purpose
Why this chapter exists. The test: *what does the novel lose if you cut it?* If
the honest answer is "pace", cut it and write the next one.

### 3. Goal
Two goals, always distinguished:
- **Plot goal** — what must be true at the end that was not true at the start.
- **Reader goal** — what the reader must feel, suspect, or fear by the last line.

### 4. Setting, and how it has changed
Where the chapter happens, its sensory signature, and — this is the part people
skip — **the delta**. What is different about this place since the reader last
stood in it? A place that is identical in chapter 50 and chapter 5 is scenery.
If this is the location's first appearance, say what it is changing *from* in
the world, and what it will become.

### 5. Characters involved, and how
Every character on the page gets four lines:
- **Why they are here** — the reason, in their own terms, not the plot's.
- **Agenda** — what they are trying to get out of this chapter. It is never
  "help the protagonist."
- **Emotional state entering → leaving** — both halves. The arrow is the point.
- **What they conceal** — everyone is holding something back, including the POV.

### 6. Conflicts
Three layers, each named concretely:
- **External** — the situation, the clock, the opposition.
- **Interpersonal** — who wants something incompatible with whom.
- **Internal** — the protagonist's lie under pressure in this specific way.
And: **what is actually at stake** — the thing that is worse at the end if he
loses. If you cannot name it, the chapter has no tension to calibrate.

### 7. The system
What the Tally does here. Which source class, who paid for it, what it costs in
residue, and whether any of it is visible to another character. If the system
does nothing this chapter, say so explicitly — that is a legitimate and
necessary choice, and naming it stops the drift where every chapter becomes a
gain.

### 8. Continuity
- **Must not contradict** — binding facts from `novel.py brief`.
- **Seeds planted** — with the thread ids you will register.
- **Callbacks paid** — which earlier chapter this cashes.

### 9. Shape
The archetype from `shapes.json`, with its opening move, turn, and closing
move written out for *this* chapter, plus the shape's failure mode restated as
a thing to watch for.

### 10. Exit state
What has changed. What the next chapter inherits: on-stage cast, live stages,
open threads, the protagonist's position, and the emotional temperature.

### 11. Failure modes
Three specific ways this chapter goes wrong — not generic craft advice. "Sila's
agenda collapses into rivalry-for-its-own-sake" is useful. "Pacing might drag"
is not.

## Workflow

```
novel.py plan --chapter 7          # what the tempo asks for
novel.py brief --chapter 7         # what the past requires
novel.py framework new 7 --shape the-offer \
    --characters mc-kestrel-vane,sila-corr --environments academy-thorn-ledger
        ... fill in the judgement ...
novel.py framework check 7         # length and sections
        ... write the chapter ...
novel.py chapter record 7 ...
```

## Craft texture

[`CRAFT-PATTERNS.md`](CRAFT-PATTERNS.md) holds the measured emotional and
intentional texture of the form — how feeling is delivered (interiority, not
emotion words), how often goals are restated, how progression language behaves
across a long run, and where the power-creep signature shows up. Read it when
filling section 5 (characters and emotion) and section 3 (goal).

## Plot architecture

[`PLOT-ARCHITECTURE.md`](PLOT-ARCHITECTURE.md) holds the measured organisation
of plot: which chapter type follows which, how long a mode sustains, whether
confrontation runs on a schedule, measured arc length, and how far setups
travel before they pay. Read it when choosing a shape and when deciding what
the next chapter should be.

## On sourcing structure from other novels

Read widely in the genre and steal *shapes* — the stock structures in
`shapes.json` are exactly that, and they belong to everyone. Do not build
frameworks by transcribing and recombining the chapters of specific
in-copyright serials: a chapter-by-chapter merge of three novels is a
derivative of all three, and blending them does not change that. The
abstraction that is safe and genuinely useful is the one already in this repo —
"this is a *threshold test* chapter, which opens on stated rules and turns on
the gap between the rule as written and the rule as enforced."
