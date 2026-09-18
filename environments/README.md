# Environments

## The rule

> The world is large. The novel is not. A place is built in full and stays
> dormant until a scene needs a stage it does not already have.

- `dormant/` — built, unmet. Scales from a room to a planetary system.
- `active/` — currently available to the prose.

`palette.json` holds the raw material: scale tiers, type templates, sensory
signatures, access rules, secrets, and the ways a place changes over a novel.
Extend it freely — the generator only ever recombines what is there.

## Types available

`academy`, `workplace`, `city-district`, `city`, `border-region`, `country`,
`orbital-station`, `moon-settlement`, `planet-frontier`, `ship`, `wilderness`,
`origin-site`.

Each arc licenses only some of them (`engine/arcs.json →
licensed_environments`). That is how the world opens outward at the story's
pace rather than the author's enthusiasm.

## Building and staging

```
tools/novel.py env new --type academy \
  --need "Arc 1 needs an institution that can exclude Kestrel formally"

tools/novel.py env activate academy-thorn-ledger \
  --need "the threshold test has to happen somewhere that can fail them"
```

## What makes an environment load-bearing

Not description. **Affordances** — what the stage makes possible that no other
stage does:

- forced proximity between people who would avoid each other
- a public arena where reputation is made and lost in one scene
- a hard deadline the place itself imposes
- somewhere a body, a document, or a person can vanish

If a new place offers no affordance the current active set lacks, the scene
belongs somewhere you have already built.

## Places change

Every dossier carries `change_over_time`. A place that is identical in Chapter
50 and Chapter 5 is scenery. A place that tightens, hollows, inverts, opens, or
floods is a character.
