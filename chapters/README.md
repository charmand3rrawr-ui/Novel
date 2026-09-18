# Chapters

The prose lives here, one file per chapter: `chapter-001.md`, `chapter-002.md`,
and so on. Nothing in this directory is generated. The engine has no opinion
about your sentences.

## Before writing

```
tools/novel.py plan        # what this chapter owes the reader
tools/novel.py brief       # what it must not contradict
```

Copy the plan's obligations into the chapter file's front block and write
against them.

## After writing

```
tools/novel.py chapter record 7 --title "..." --summary "..." \
    --tension 6 --kind conflict \
    --characters mc-kestrel-vane,sila-corr --environments academy-thorn-ledger

tools/novel.py chapter point 7 --kind promise --weight 5 --tags corr,register \
    --text "the thing a future chapter could contradict"

tools/novel.py chapter close --tension 6 --kind conflict
tools/novel.py continuity sync
tools/novel.py validate
```

`--kind` is the scene type: conflict, discovery, relationship, consequence, or
quiet. The engine tracks the mix against
`engine/tempo.json → scene_mix_target_per_arc` and warns when you have run three
action chapters in a row or two quiet ones.

Use `_template.md` as the starting file for each chapter.
