# A Web Novel Framework

A working system for writing a long serial novel: a world bible that binds, an
engine that sets the tempo, a cast and a world that are built deep and revealed
late, a memory the present can search, and a miner that turns other people's
novels into raw creative material without borrowing anything from them.

Pure Python standard library. No install, no build step, no dependencies.

```
tools/novel.py status
```

## The idea

Three problems kill long serial fiction, and each has a file here that answers
it.

**Pacing drifts.** Chapters escalate for eight straight weeks, or nothing
happens for five. → `engine/` holds a beat cycle, a tension curve, cadence
rules, and progression gates. `novel.py plan` tells you what the next chapter
owes the reader before you write a word.

**The cast and the map sprawl.** One reasonable new character at a time until
nobody is on the page often enough to matter. → Characters and environments are
generated *in full* — wound, lie, offstage life, exit condition; power
structure, secret, affordances — and then held **dormant**. They come forward
only when the storyline needs them, and the engine enforces it with per-arc
budgets and arc licensing. It will refuse you, and say why.

**The past gets lost.** By chapter forty nobody remembers what chapter six
established. → `continuity/` records each chapter's **load-bearing** items with
weights and tags, and `novel.py lookback` searches them with chapter citations.

## Layout

```
bible/          what is permanently true      — canon locks, cosmology, history, factions, cultures, style
engine/         what the next chapter owes    — tempo, arcs, progression, live state
characters/     who exists                    — cast/ on the page, dormant/ on the bench
environments/   where it can happen           — active/ and dormant/, room to star system
continuity/     what the past requires        — chapter index, threads, generated reference map
inspiration/    where new material comes from — trait lexicon, miner output
chapters/       the prose
tools/          novel.py, scrape_characters.py, novelkit/
docs/           walkthrough with real session output
```

## The loop

```
novel.py status                  where the novel stands
novel.py plan                    what this chapter owes
novel.py brief                   what it must not contradict
     ... write the chapter ...
novel.py chapter record 7 --title "..." --summary "..." --tension 6 --kind conflict \
     --characters mc-kestrel-vane,sila-corr --environments academy-thorn-ledger
novel.py chapter point 7 --kind promise --weight 5 --tags corr --text "..."
novel.py seed plant --id th-... --summary "..."
novel.py chapter close --tension 6 --kind conflict
novel.py continuity sync
novel.py validate
```

See [`docs/walkthrough.md`](docs/walkthrough.md) for a full session with real
output.

## Characters: deep first, late second

```
novel.py character new --role rival --need "Kestrel's method needs a mirror that shows its cost"
novel.py character introduce sila-corr --need "the threshold test needs a witness who benefits from failure"
```

The generator draws **contradictory** atoms from `inspiration/lexicon.json`:
the mask is chosen so it cannot protect the competence, the loyalty shape so it
guarantees the fear arrives. Every dossier records its `seed`, so `--seed N`
reproduces a character exactly.

`introduce` refuses if the arc does not license the role, if the per-arc or
per-chapter budget is spent, or if a cooldown is running. `--override` always
exists, and writes your reason into the engine log.

Full model in [`characters/README.md`](characters/README.md).

## Environments: the world opens at the story's pace

```
novel.py env new --type moon-settlement --need "Arc 4 needs a place where the books are visibly wrong"
novel.py env activate academy-thorn-ledger --need "the threshold test needs somewhere that can fail them publicly"
```

Twelve types across twelve scale tiers — room, building, campus, district,
city, region, country, planet, moon, orbital, frontier, system. Each arc
licenses only some. A place that is never needed cost you one command; a place
brought forward early costs you a reader.

Full model in [`environments/README.md`](environments/README.md).

## The world bible

[`bible/`](bible/00-world-bible.md) holds what does not move: canon locks that
are defects to break, the scale ladder, the history that presses on the
present, factions with one want and one pressure point each, three cultures,
and the prose contract.

The premise: obligation is recorded, the houses that keep the books have become
the government, and the one thing the system cannot process is a gift.

## The novel engine

[`engine/novel-engine.md`](engine/novel-engine.md) explains the four dials —
beat, tension, introduction budget, progression — and what each refusal means.

Progression is the strict one. Capability never rises for free:

```
novel.py advance craft --cost anonymity --reason "passing the threshold test in public"
```

and no track may exceed its starting value plus `chapter / 6` before Act III.
The protagonist cannot outrun the novel.

## Continuity: pinpointing what matters

```
novel.py chapter point 12 --kind debt --weight 5 --tags pledge,origin \
    --text "Kestrel's schooling was bought with a pledge taken when they were eleven" \
    --lock LK-NO-ERASURE

novel.py lookback "pledge schooling"
novel.py lookback --tags register --kinds rule,promise --min-weight 4
novel.py brief --chapter 31
```

Points are ranked by weight, term and tag overlap, recency, and whether they
are binding, and every hit cites its chapter. `continuity/reference-map.md` is
the generated human-readable mirror.

Full model in [`continuity/README.md`](continuity/README.md).

## Mining other novels for creativity

```
tools/scrape_characters.py --source pg-1342 --source pg-84
tools/scrape_characters.py --review
tools/scrape_characters.py --promote all
```

For each figure in a source it builds a behavioural fingerprint — speech
register, adverb register, action class — then **crosses fingerprints from
different sources** and writes the result through this project's own phrase
templates. Every promoted atom is a hybrid no single source owns, phrased in
language none of them used.

It never stores source prose. It never reuses source names — every name
detected goes onto an avoid-list the generator steers around. It never promotes
anything automatically. Point it only at text you are entitled to analyse:
public-domain works, your own drafts, or licensed material.

Full model in [`inspiration/README.md`](inspiration/README.md).

## Validation

```
novel.py validate
```

Checks that the registries and the files agree, that state and registries agree
about who is on stage, that progression has not outrun the page count, that
`lie_grip + self_knowledge == 10`, that canon lock citations resolve, that no
thread has rotted past its payoff window, and that every written chapter has a
continuity record.

## Making it yours

Everything above is a worked example, not a fixture. The framework is the
directory structure, the tools, and the rules. To write a different novel:
rewrite `bible/`, redraw `engine/arcs.json` and `engine/progression.json`,
empty the registries, and keep the loop.
