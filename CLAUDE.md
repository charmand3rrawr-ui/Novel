# Working in this repository

This is a writing project with a toolchain, not a software project. The code
exists to keep the novel honest.

## Before changing anything

Read `README.md`, then `engine/novel-engine.md`. The framework has opinions and
they are load-bearing.

## Rules that are not negotiable

1. **Never introduce a character or environment without a `--need`.** The whole
   design rests on just-in-time reveal. If the need cannot be stated in one
   sentence, it is not needed yet.
2. **Never edit `engine/state.json` by hand** unless repairing corruption. It is
   the engine's save file; use the CLI so the log stays truthful.
3. **Never raise a capability track without paying a cost track.** Use
   `novel.py advance`, which enforces it.
4. **Never absorb without a scene and a payer.** `novel.py system absorb`
   requires `--scene` and `--who-paid`. Nothing sheds essence without losing it
   (`LK-MOTE-COSTS`), and the absorption log is the novel's case against the
   protagonist. Do not weaken this.
5. **Never hand-edit `engine/system-status.json`** except to repair corruption.
   Use `novel.py system`, so the log and the event history stay truthful.
6. **Never let a breakthrough be free.** `novel.py system realm` requires a
   `--scene` and debits the story's cost tracks (`LK-BREAKTHROUGH-COSTS`).
7. **Never break a canon lock** (`bible/canon-locks.json`). Breaking one is a
   defect, not a creative choice. Changing one is a deliberate act with a
   commit message explaining it.
8. **Run `novel.py validate` before committing.** It must pass clean.

## The protagonist's system

`engine/system-engine.md` is the doctrine; `engine/system.json` is the rules;
`engine/system-status.json` is the live state and the absorption log. The four
anti-inflation rails — familiarity decay, per-chapter and per-arc caps, residue,
and the witness rule — are the reason the system is safe to write with. Retune
them in the data, never by removing the refusals.

Power-system facts that apply to everyone (realms, techniques, sorcery,
bloodlines, talents) belong in `bible/power-systems.md`, not in the system
files. Professions belong in `bible/professions.md`.

## When adding a chapter

Write the framework first — `chapters/FRAMEWORK-SPEC.md`, minimum 500 words,
eleven sections, in `chapters/frameworks/ch-NNN.md`:

```
novel.py framework shapes --beat <beat>
novel.py framework new N --shape <id> --characters ... --environments ...
novel.py framework check N
```

Do not build frameworks by transcribing and recombining chapters of specific
in-copyright novels. Structural archetypes are generic and live in
`chapters/shapes.json`; a chapter-by-chapter merge of particular serials is a
derivative of them, and blending several does not change that.

```
novel.py plan && novel.py brief     # before
novel.py chapter record N ...       # after
novel.py chapter point N ...        # every load-bearing detail
novel.py chapter close --tension T --kind K
novel.py continuity sync && novel.py validate
```

If the chapter moved the system:

```
novel.py system absorb <source> --scene "..." --who-paid "..."
novel.py system spend <attribute> <n>
novel.py system realm --to N --scene "..."      # only if it happened under pressure
novel.py system sheet
```

## When changing the tools

- Standard library only. No dependencies, no build step.
- Data on disk stays JSON or Markdown, hand-editable without the tools present.
- Every refusal the engine issues must say *why* and how to override it.
- Smoke-test with `python3 tools/novel.py status` and `validate` before committing.

## Structure analysis

`tools/analyze_structure.py` may only be pointed at public-domain works, the
user's own drafts, or licensed material — the same rule as the mining tool. It
stores aggregate numbers only; the one-way abstraction is what makes it safe.
Do not extend it to retain prose, names, or plot summaries.

`engine/genre-priors.json` is explicitly labelled as estimates. If you replace
a prior with a measurement, move it into `inspiration/structure-metrics.json`
via the analyser rather than editing the priors to look like data.

## The mining tool

`tools/scrape_characters.py` may only be pointed at public-domain works, the
user's own drafts, or licensed material. Its guarantees — no source prose
stored, no source names reused, no automatic promotion — are the reason it is
safe to use. Do not weaken them.
