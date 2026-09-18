# A Web Novel Framework

A working system for writing a long serial progression novel: a world bible that
binds, an engine that sets the tempo, a protagonist's attribute system with
anti-inflation rails, a cast and a world that are built deep and revealed late,
a memory the present can search, and a miner that turns other people's novels
into raw creative material without borrowing anything from them.

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

**Power inflates.** The protagonist outruns the story, and by chapter thirty
nothing can threaten him. → `engine/system.json` rations it: familiarity decay
so grinding one source stops paying, hard caps per chapter and per arc, residue
that turns convenience into plot, and breakthroughs that debit the story's cost
tracks. `novel.py system` refuses, out loud, with a reason.

## Layout

```
bible/          what is permanently true      — canon locks, power systems, professions, cosmology, history, factions, cultures, style
engine/         what the next chapter owes    — tempo, arcs, progression, live state
                the protagonist's system      — system-engine.md, system.json, system-status.json/.md
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
novel.py framework new 7 --shape the-offer \
     --characters mc-kestrel-vane,sila-corr --environments academy-thorn-ledger
novel.py framework check 7       500-word minimum, eleven required sections
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
output, and [`docs/system-walkthrough.md`](docs/system-walkthrough.md) for the
protagonist's system in use.

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

## Chapter frameworks

Before a chapter is written it gets a framework: at least 500 words in
`chapters/frameworks/ch-NNN.md` covering purpose, plot and reader goals, the
setting **and how it has changed since the reader last stood in it**, every
character with their reason for being there, their agenda, their emotional
state entering and leaving and what they conceal, the external / interpersonal
/ internal conflicts and what is concretely at stake, what the system does and
who paid for it, the continuity it must not contradict, its structural shape,
its exit state, and three specific ways it goes wrong.

```
novel.py framework shapes --beat cost
novel.py framework new 7 --shape the-squeeze --characters ... --environments ...
novel.py framework check
```

`framework new` assembles ~1,000 words from live engine state and leaves the
judgement as prompts. `chapters/shapes.json` holds fourteen **chapter-shape
archetypes** — the stock structures of the genre, not the plot of any
particular book: the demonstration, the threshold test, the squeeze, the quiet
acquisition, the workshop, the hunt, the offer, the witness, the breakthrough,
the reckoning, the rest that isn't, the reveal to one person, the humiliation,
two rooms. Each names its opening move, its turn, its closing move, what it
costs, and how it fails.

Five worked frameworks ship in `chapters/frameworks/`, 1,575–1,729 words each,
covering the opening arc.

Spec: [`chapters/FRAMEWORK-SPEC.md`](chapters/FRAMEWORK-SPEC.md).

## The protagonist's system

He can see what things shed when they end, and take it. Everyone else climbs by
spending; he climbs by collecting what is already being lost.

```
novel.py system status
novel.py system absorb ambient_training \
    --scene "the third-form hall, an hour before dawn" \
    --who-paid "forty students who trained until they shook"
novel.py system spend strength 3
novel.py system realm --to 2 --scene "the quay stair, bleeding, with the tide coming in"
novel.py system forecast
novel.py system sheet
```

Four rails stop it inflating, and each refuses out loud:

- **Familiarity decay** — `multiplier = decay ^ (times absorbed this realm)`,
  floored at 0.15. Grinding the same source stops paying; finding a *new kind of
  ending* is always worth more, which pushes the plot outward. A breakthrough
  resets every counter.
- **Caps** — 25 points/chapter soft, 60 hard, 320/arc. Over soft it warns that
  the reader is feeling the escalation; over hard it refuses.
- **Residue** — tainted sources leave what the system cannot spend. At 25/50/75/100
  it does something on the page, and clearing it costs money, a favour, or trust.
- **The witness rule** — `absorb` requires `--scene` and `--who-paid`. Nothing
  sheds essence without losing it (`LK-MOTE-COSTS`), so the absorption log is a
  ledger of everyone he has quietly taken from, and by chapter forty that
  document is the novel's case against him.

Breakthroughs debit the story's cost tracks in `progression.json` — body,
anonymity, intimacy, integrity — so the power ladder and the character ladder
stay welded together.

`engine/system-status.json` is the live state and full log;
`engine/system-status.md` is the readable character sheet. The numbers never
appear in the prose: the sheet is the author's instrument, so that what he could
do in chapter 12 and what he can do in chapter 48 are answerable questions with
the same answer every time.

Full model in [`engine/system-engine.md`](engine/system-engine.md).

## The world's power systems

Four ladders everyone climbs, in
[`bible/power-systems.md`](bible/power-systems.md): **cultivation** (nine realms,
Unmarked to Unwritten, scaling from a fight to crossing between worlds),
**martial arts** (technique proficiency in four bands), **sorcery** (patterns and
inscription — notation, not willpower), and **bloodline traits** (dormant →
stirred → awakened → ascended, every one with a gift and a toll).

**Talent is rate, not power** — dull to heaven-sent, 0.5× to 4×, assessed
publicly per discipline. Which is exactly why the protagonist's results are
inexplicable to everyone who has seen his ratings.

[`bible/professions.md`](bible/professions.md) holds the second ladder, open to
anyone the talent assessors wrote off: forging, alchemy, cooking, inscription,
taming, appraisal, across nine ranks from Apprentice to Unwritten. Professions
feed power four ways — the practice builds attributes, the products are usable,
the wealth buys time, and rank opens doors realm does not. Failed work sheds
essence, which is why the protagonist haunts workshops.

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

On the system it checks point accounting (`earned == spent + unspent`), residue
state against residue value, that the current realm's requirements are actually
met, profession ranks against proficiency, trait states and talent ratings
against the config, the per-chapter and per-arc caps, and that every absorption
in the log names both a scene and who paid for it.

## Making it yours

Everything above is a worked example, not a fixture. The framework is the
directory structure, the tools, and the rules. To write a different novel:
rewrite `bible/`, redraw `engine/arcs.json` and `engine/progression.json`,
empty the registries, and keep the loop.

The power systems and the professions stand on their own; the chartered-house /
ledger layer is the institutional skin over them and can be swapped for sects,
empires, guilds or academies without touching the engine, the system, or any
tool. To retune the system itself, edit `engine/system.json` — sources, tiers,
decay rates, caps, realms, traits and professions are all data, and nothing in
the code hardcodes them.
