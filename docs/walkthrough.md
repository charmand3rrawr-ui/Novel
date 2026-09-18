# Walkthrough

A real session, start to finish. Every block below is actual output from the
tools in this repository, captured against a scratch copy of the project at
chapter 1.

The loop is always the same:

```
plan  →  write  →  record  →  close  →  validate
```

## 1. Ask what the chapter owes

`novel.py plan` reads the arc, the beat cycle, the tension curve, the open
threads, and the budgets, and tells you what this chapter is for.

## 2. Bring on only what the story needs

Introducing a character requires a `--need`. The engine checks the arc licenses
that role and that the budget has room. The need string is stored on the
dossier permanently.

## 3. Write the chapter

The engine stops here. It has no opinion about prose.

## 4. Record what will matter later

`chapter record` captures the shape. `chapter point` captures the
**load-bearing** details — the ones a future chapter could contradict.

## 5. Pay for progression

Capability never rises for free.

## 6. Close the chapter and get the next plan

```
$ novel.py plan
====================================================================
 PLAN — Chapter 1  ·  ACT1 / A1 Entrance by the Side Door
====================================================================
 Question this arc answers: Can Kestrel survive a place built to exclude them?
 Word target: ~2600

This chapter owes
-----------------
 • Beat: hook — Open a want or a threat the reader can name in one sentence.
 • Tension target: 3/10
 • Plant at least 1 seed(s): record with `novel.py seed plant`.

Casting licence
---------------
 New character : YES
   arc licenses roles: rival, mentor, institution-face, peer-ally
 New environment: NO  — chapter budget spent: 1/1 environments already introduced in chapter 1
   arc licenses types: academy

Progression ceilings this chapter
---------------------------------
 craft:2  authority:1  insight:3  endurance:3  reach:1
 gate G1 Admitted to the discipline — needs craft 1/2


$ novel.py character introduce sila-corr --need "the threshold test needs a witness who benefits from Kestrel failing"
Sila Corr enters in chapter 1.
  need  : the threshold test needs a witness who benefits from Kestrel failing
  entry : called in by an established character under pressure
  file  : characters/cast/sila-corr.md
  - The scene must need them for a reason the reader already feels.
  - They arrive mid-action, doing their own business, not waiting to be met.
  - One concrete detail from `surface` lands in the first three lines.

$ novel.py seed plant --id th-pledge-holder --summary "The pledge that bought Kestrel's schooling is not held by the house they think"
Seed 'th-pledge-holder' planted in chapter 1.
  payable from chapter 4, stale after 16, rot at 31.

$ novel.py chapter record 1 ...
Recorded chapter 1 (A1, beat hook).
Add the load-bearing details with `novel.py chapter point`.

$ novel.py chapter point 1 --kind rule ...
lb-1-1 recorded on chapter 1: (rule, w5) The threshold register is superseded, never rewritten: every correction is visible to anyone who reads the sequence
  tags: register, threshold
lb-1-2 recorded on chapter 1: (relationship, w4) Sila Corr watched Kestrel pass and said nothing, which both of them understood as a decision
  tags: corr, rivalry
lb-1-3 recorded on chapter 1: (debt, w5) Kestrel's schooling was bought with a pledge taken when they were eleven, still an open entry
  tags: origin, pledge

$ novel.py advance craft --cost anonymity --reason "passing the threshold test in public view"
craft 2  (paid: anonymity 8)
  It must happen on the page in chapter 1, not in summary.

$ novel.py gate pass G1
Gate G1 — Admitted to the discipline — passed in chapter 1.
  unlocks: environment:academy-thorn-ledger

$ novel.py chapter close --tension 3 --kind conflict
Chapter 1 closed. Now on chapter 2 (A1).

====================================================================
 PLAN — Chapter 2  ·  ACT1 / A1 Entrance by the Side Door
====================================================================
 Question this arc answers: Can Kestrel survive a place built to exclude them?
 Word target: ~2600

This chapter owes
-----------------
 • Beat: pressure — Force the POV character to spend something: time, trust, safety, or self-image.
 • Tension target: 4/10
 • Plant at least 1 seed(s): record with `novel.py seed plant`.

Casting licence
---------------
 New character : YES
   arc licenses roles: rival, mentor, institution-face, peer-ally
 New environment: YES
   arc licenses types: academy

Progression ceilings this chapter
---------------------------------
 craft:2  authority:1  insight:3  endurance:3  reach:1

Must not contradict
-------------------
 • [ch.1] (rule) The threshold register is superseded, never rewritten: every correction is visible to anyone who reads the sequence
 • [ch.1] (debt) Kestrel's schooling was bought with a pledge taken when they were eleven, still an open entry
 • [ch.1] (relationship) Sila Corr watched Kestrel pass and said nothing, which both of them understood as a decision
```

## 7. Look back when the present needs the past

Forty chapters later, the question is never "what happened in chapter 1?" but
"what did I establish about the pledge?" That is what `lookback` and `brief`
are for.

```
$ novel.py lookback "pledge schooling eleven"
1 reference(s):
 [ch.  1]! (debt, w5, score 21.0) Kestrel's schooling was bought with a pledge taken when they were eleven, still an open entry
           tags: origin, pledge   id: lb-1-3

$ novel.py lookback --tags register --min-weight 4
1 reference(s):
 [ch.  1]! (rule, w5, score 16.0) The threshold register is superseded, never rewritten: every correction is visible to anyone who reads the sequence
           tags: register, threshold   id: lb-1-1

$ novel.py brief
====================================================================
 CONTINUITY BRIEF — writing chapter 2
====================================================================

Binding facts (do not contradict)
---------------------------------
 • [ch.1] (rule, w5) The threshold register is superseded, never rewritten: every correction is visible to anyone who reads the sequence
 • [ch.1] (debt, w5) Kestrel's schooling was bought with a pledge taken when they were eleven, still an open entry
 • [ch.1] (relationship, w4) Sila Corr watched Kestrel pass and said nothing, which both of them understood as a decision

Unpaid threads
--------------
 • th-pledge-holder (ch.1, 1 chapters carried) The pledge that bought Kestrel's schooling is not held by the house they think

Last three chapters
-------------------
 ch.1 The Second Door: Kestrel reconstructs a standing from partial entries to pass the threshold test, and is seen doing it by someone who was counting on failure

Last seen
---------
 mc-kestrel-vane              ch.1
 sila-corr                    ch.1
 academy-thorn-ledger         ch.1


$ novel.py continuity sync
Wrote continuity/reference-map.md

$ novel.py validate
Clean. The bible, the engine, and the registries agree.

$ novel.py status
====================================================================
 Chapter 2  ·  ACT1 / A1 Entrance by the Side Door
====================================================================
 Central question : Can Kestrel survive a place built to exclude them?
 Pressure source  : institutional gatekeeping
 Beat             : pressure   Tension target: 4/10
 POV              : mc-kestrel-vane
 On stage         : mc-kestrel-vane, sila-corr
 Stages live      : academy-thorn-ledger
 Open threads     : 1
 Bench            : 0 dormant characters, 1 dormant environments
 Introductions    : characters 1/4 this arc · environments 1/2 this arc

Protagonist tracks
------------------
 capability  craft:2  authority:0  insight:2  endurance:2  reach:0
 cost        intimacy:6  integrity:7  anonymity:8  body:8
 internal    lie_grip:9  self_knowledge:1
```

## What the engine refused along the way

Real refusals, from the same session:

```
$ novel.py env activate orbital-station-pale-verge --need "wanted it now"
activation refused:
  - arc A1 licenses ['academy']; 'orbital-station' is outside it
  - chapter budget spent: 1/1 environments already introduced in chapter 1
  Re-run with --override and the engine will log the exception.
```

Both refusals are information. The station is built and waiting in
`environments/dormant/` — Arc 3 licenses it, and the story will reach it. Until
then it costs nothing to have it ready and everything to bring it forward early.

## The mining pipeline

```
$ tools/scrape_characters.py --source pg-1342 --source pg-84 --seed 11
fetching Pride and Prejudice (public domain (US)) ...
fetching Frankenstein (public domain (US)) ...
  pg-1342: 12 figures profiled from 12 candidate names
  pg-84: 12 figures profiled from 12 candidate names

16 new candidate atom(s) written to inspiration/mined.json.
23 source names added to the avoid-list — the generator will not reuse them.
  mined-verbal_tic-1         [verbal_tic] goes silent for exactly as long as it takes to unnerve
  mined-mask-1               [mask] principle invoked at exactly the moment it is convenient
  mined-competence-1         [competence] can move a room's decision without appearing to speak first
  mined-arc_shape-1          [arc_shape] holds, holds, holds, then breaks in one irreversible scene

$ tools/scrape_characters.py --promote all
Promoted 16 atom(s) into inspiration/lexicon.json.
```

Those atoms are now in the generator's pool. The rival in this project,
Sila Corr, drew one of them:

```
$ novel.py character new --role rival --name "Sila Corr" --seed 90210 --need "..."
Created Sila Corr (rival) — dormant.

  Contradictions to play:
   - The mask (reasonableness used as a battering ram) cannot protect the spike
     (acquires dialects and registers unnervingly fast) when it is tested in public.
   - Their loyalty (loyal to terms, not people; will honor a bad deal to the letter)
     guarantees they will meet the thing they fear: being replaceable.
   - The lie — A clean conscience is worth more than a saved life. — will look true
     for most of their time on the page.
```

"Reasonableness used as a battering ram" is a mined atom: a cross of one book's
action register with another book's adverb register, expressed in language
neither book used. Regenerate her exactly with `--seed 90210`.
