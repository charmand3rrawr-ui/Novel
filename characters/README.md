# Characters

## The rule

> Deep first, late second. A character is built in full — wound, lie, mask,
> offstage life, exit condition — and then waits on the bench until the
> storyline needs them.

Two directories enforce it:

- `dormant/` — fully built, not yet met by the reader. This is inventory, not
  debt. A dossier that is never used cost you one command.
- `cast/` — on the page. Everyone here must be doing something in the current
  arc or be deliberately offstage with a reason recorded.

`registry.json` is the machine index. The Markdown dossiers are the
human-readable truth; edit them freely, and keep the registry's `id`, `status`,
and `file` fields accurate (or let the CLI do it).

## Building one

```
tools/novel.py character new --role rival \
  --need "Kestrel's method needs a mirror that shows its cost" \
  --culture ledger
```

The generator draws contradictory atoms from `inspiration/lexicon.json`: the
mask is chosen so it cannot protect the competence, and the loyalty shape is
chosen so it guarantees the fear arrives. Every dossier records the `seed` that
produced it, so `--seed N` reproduces it exactly.

Generation is a starting position, not a character. Rewrite anything. The
fields that matter most — `bonds.to_protagonist`, `trajectory.break_point`,
`trajectory.exit_condition`, and the voice sample — are deliberately left
undefined for you.

## Introducing one

```
tools/novel.py character introduce sila-corr \
  --need "the threshold test needs a witness who benefits from Kestrel failing"
```

The engine refuses if the arc does not license that role, if the arc or chapter
budget is spent, or if a cooldown is running after a major introduction. The
`--need` string is stored on the dossier permanently. If you cannot write that
sentence, the character is not needed yet.

## The depth model

| Layer | Field | Why it exists |
|---|---|---|
| Core | wound, lie, want, need, fear, moral axis | the engine of their behaviour |
| Surface | mask, verbal tic, physical signature | what the reader meets first |
| Capability | spike, secondary, hole | what they can and cannot do under pressure |
| Bonds | loyalty shape, leverage both ways | why scenes with them have stakes |
| Offstage life | what they do in chapters they are absent from | why they feel like a person |
| Trajectory | arc shape, break point, exit condition | so they leave the novel on purpose |
| Contract | entry pretext, first-appearance conditions | so they arrive well |

The wound is never introduced, only discovered (`LK-EARNED-WOUND`).
