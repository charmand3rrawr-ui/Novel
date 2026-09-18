# Chapters

The prose lives here, one file per chapter: `chapter-001.md`, `chapter-002.md`,
and so on. Nothing in this directory is generated. The engine has no opinion
about your sentences.

## Before writing: the framework

Every chapter gets a **framework** first — a document of at least 500 words in
`frameworks/ch-NNN.md` that says why the chapter exists, who wants what inside
it, how the setting has changed since the reader last stood in it, and what the
chapter must accomplish. The spec is [`FRAMEWORK-SPEC.md`](FRAMEWORK-SPEC.md);
the archetypes it builds on are in [`shapes.json`](shapes.json).

```
tools/novel.py plan --chapter 7      # what the tempo asks for
tools/novel.py brief --chapter 7     # what the past requires
tools/novel.py framework shapes --beat cost     # which shapes serve that beat
tools/novel.py framework new 7 --shape the-squeeze \
    --characters mc-kestrel-vane,sila-corr --environments academy-thorn-ledger
        ... fill in the judgement ...
tools/novel.py framework check 7
```

`framework new` scaffolds roughly a thousand words from live engine state — the
arc's promise, the beat, the tension target, each character's wound, lie, fear,
mask and voice handle, the stage's sensory signature and how it changes, the
binding continuity facts, the unpaid threads, and the protagonist's system
position — leaving the judgement calls as `_<prompts>_` for you. `framework
check` enforces the 500-word minimum and the eleven required sections, and
counts prompts you have not filled.

Then write against the framework.

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
