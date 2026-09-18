# Continuity

This is the novel's memory: the answer to *"what does this chapter have to
respect?"* without re-reading the book.

## Files

- **`chapter-index.json`** — per chapter: what happened, who was on stage,
  where, and the **load-bearing** items the future is not allowed to
  contradict. This is the pinpointing file.
- **`threads.json`** — every seed planted and whether it has been paid.
- **`reference-map.md`** — generated human-readable mirror of both.
  Regenerate with `novel.py continuity sync`.

## Load-bearing points

Not everything in a chapter matters later. A point is load-bearing when a
future chapter could contradict it. Record those, and nothing else.

```
tools/novel.py chapter point 4 \
  --kind promise --weight 5 \
  --text "Corr promised Kestrel a copy of the threshold register before term's end" \
  --tags corr,register,promise \
  --lock LK-NO-ERASURE
```

- **kind** — fact, promise, object, injury, rule, relationship, secret, name,
  place, debt
- **weight** — 1 (colour) to 5 (the novel breaks if this is contradicted)
- **tags** — how you will search for it in forty chapters
- **lock** — optional citation to a canon lock in `bible/canon-locks.json`
- **`--soft`** — colour, not canon; excluded from binding briefs

## Looking back

```
tools/novel.py lookback "register promise corr"
tools/novel.py lookback --tags ledger --kinds debt,promise --min-weight 4
tools/novel.py lookback "the audit" --before 30
```

Results are ranked by weight, term overlap, tag hits, recency, and whether the
point is binding — and every hit cites its chapter, so you go straight to the
source scene.

```
tools/novel.py brief --chapter 31
```

gives the full picture before you write: binding facts, unpaid threads, the
last three chapters, and when each cast member and stage was last seen.

## Threads

```
tools/novel.py seed plant --id th-audit-report --summary "The Cinder auditor's report was superseded, not withdrawn"
tools/novel.py seed pay --id th-audit-report --note "Kestrel finds the superseding entry"
```

Seeds are payable after `min` chapters, stale after `soft_max`, and **rot**
after `hard_max` — at which point the validator raises it as an error. Rot has
three cures and all of them are legitimate: pay it, repurpose it, or retire it
on the page.
