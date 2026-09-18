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
4. **Never break a canon lock** (`bible/canon-locks.json`). Breaking one is a
   defect, not a creative choice. Changing one is a deliberate act with a
   commit message explaining it.
5. **Run `novel.py validate` before committing.** It must pass clean.

## When adding a chapter

```
novel.py plan && novel.py brief     # before
novel.py chapter record N ...       # after
novel.py chapter point N ...        # every load-bearing detail
novel.py chapter close --tension T --kind K
novel.py continuity sync && novel.py validate
```

## When changing the tools

- Standard library only. No dependencies, no build step.
- Data on disk stays JSON or Markdown, hand-editable without the tools present.
- Every refusal the engine issues must say *why* and how to override it.
- Smoke-test with `python3 tools/novel.py status` and `validate` before committing.

## The mining tool

`tools/scrape_characters.py` may only be pointed at public-domain works, the
user's own drafts, or licensed material. Its guarantees — no source prose
stored, no source names reused, no automatic promotion — are the reason it is
safe to use. Do not weaken them.
