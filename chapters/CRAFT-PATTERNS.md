# Craft Patterns

What the measurements actually say about **feeling, emotion, progression and
goal** — and what to do with it in this novel.

Numbers come from `serial-reference-A` (3,204 chapters, measured with
`tools/analyze_structure.py --deep --craft`). Rates are hits per 1,000 words at
corpus level. The interpretation is judgement, and is marked as such.

---

## 1. The dominant feeling is not an emotion. It is advancement.

| Register | Rate /1k | In % of chapters | First decile → last |
|---|--:|--:|---|
| **progression** | **9.12** | 97.6% | 5.45 → **12.34** |
| sensory | 8.36 | 99.1% | 7.77 → 15.93 |
| **interiority** | **5.36** | 98.6% | 5.31 → 5.68 |
| **goal / intent** | **3.97** | 94.7% | 4.81 → 4.20 |
| stakes | 2.76 | 78.5% | 3.05 → 2.32 |
| surprise | 2.30 | 89.0% | 1.56 → 2.34 |
| joy | 2.25 | 82.2% | 2.41 → 2.04 |
| social standing | 1.77 | 75.8% | 1.65 → 1.53 |
| anger | 0.89 | 45.2% | 0.88 → 0.90 |
| fear | 0.85 | 52.6% | 0.71 → 0.83 |
| contempt | 0.39 | 29.8% | 0.41 → 0.42 |
| shame | 0.29 | 25.1% | 0.28 → 0.30 |
| sorrow | 0.27 | 23.1% | 0.30 → 0.24 |
| resolve | 0.16 | 15.2% | 0.10 → 0.07 |

**Progression vocabulary outweighs every emotion combined**, appears in 97.6% of
chapters, and roughly *doubles* across the run. The feeling the form delivers is
not anger or triumph. It is the sensation of a number going up, narrated.

*What to do with it:* decide consciously how loud that register runs in your
book. Your novel has an unusual advantage here — the Tally means advancement is
morally charged rather than neutral, so you can run the register loud and have
it mean something. But if progression language appears in 97% of your chapters
without the cost tracks moving, you have written the genre's failure mode.

---

## 2. Emotion is thin, cool, and mostly satisfaction

Every emotion category lands under 2.5/1k. Joy is the most frequent (82% of
chapters) and it is not delight — the vocabulary clusters on *satisfaction*.
Sorrow, shame and resolve each appear in under a quarter of chapters.

The striking one: **resolve appears in 15.2% of chapters and falls to 0.07/1k by
the end.** The "he clenched his fist and vowed" beat that the genre is mocked
for is, in this sample, rare and getting rarer.

*Interpretation:* the form does not deliver feeling through emotion words. It
delivers feeling through **interiority** (5.36/1k, present in 98.6% of chapters)
— we are told what he thought, realised, knew and decided, constantly. The
emotion is inferred from access, not stated.

*What to do with it:* this is the single most transferable technique here, and
it happens to suit your protagonist exactly. Kestrel is a man who converts
feeling into accounting. High interiority plus low emotional vocabulary *is* his
voice — he tells you the calculation, and the reader supplies the grief. Where
the reference serial does this by convention, you can do it as characterisation.

---

## 3. Goals are restated constantly, not assumed

Goal and intent language appears in **94.7% of chapters** at 3.97/1k. The reader
is essentially never uncertain about what the protagonist is trying to do right
now.

This is the load-bearing retention technique of the form, and it is invisible
until you count it. A reader arriving at chapter 1,800 after a week away is
re-oriented within a paragraph, because the chapter tells them the objective
again.

*What to do with it:* your framework spec already separates **plot goal** from
**reader goal** for every chapter. Add the discipline that the *chapter's own
objective* surfaces in the prose, early, in the POV's terms — not as a recap,
but as him wanting something nameable on the first page.

---

## 4. Almost every chapter is a fresh entry point

From the structural pass:

- **Only 2.7% of chapters open by continuing the previous scene** (a pronoun
  subject). 44% open on scene-setting, 41% on a named subject, 12% on cold
  dialogue.
- **Only 3.3% end mid-action.** 62% end on a statement, 26% on dialogue.
- **65% of endings are quiet**, not hooks.

The belief that this form runs on cliffhangers is false. What it actually runs
on is *self-containment*: each chapter is a complete unit with a stated
objective, an interior line, and a landing. The hook is that the next chapter is
ninety seconds away.

*What to do with it:* if you serialise, this is the adjustment that matters more
than chapter length. Your `shapes.json` archetypes all assume a chapter is a
scene; in serial architecture a chapter is closer to a *beat with a frame around
it*. Consider annotating each shape with a serial variant.

---

## 5. The internal shape of a chapter is flat

| Position in chapter | 1st fifth | 2nd | 3rd | 4th | 5th |
|---|--:|--:|--:|--:|--:|
| dialogue density | 0.245 | 0.287 | 0.289 | 0.296 | 0.300 |
| paragraph words | 18.1 | 18.6 | 18.6 | 18.7 | 18.9 |

Chapters do not build texture toward a climax. They hold one consistent density
from first line to last, with dialogue very slightly back-loaded.

Sentences: **median 9 words**, p90 17, standard deviation 5.5, and 26% of
sentences are 5 words or shorter. Paragraphs average 18 words and 26% are under
10. Dialogue arrives as **17 short volleys of ~7 words** per chapter, not
speeches.

*What to do with it:* this is a texture you can adopt or reject wholesale, but
choose. Your style guide currently says "vary length deliberately; a short
sentence after three long ones is the novel's main emphasis tool." That is a
literary technique and it is incompatible with a stdev of 5.5. Both work. They
are different books, and your prose contract should say which one you are
writing.

---

## 6. The power-creep signature is visible in the data

Across the run:

- progression language **rises** 5.45 → 12.34
- stakes language **falls** 3.05 → 2.32
- chapter length **falls** 34% (1,425 → 939 median words)
- dialogue **falls** 0.33 → 0.21
- sensory language **doubles** 7.77 → 15.93

Read together: later chapters are shorter, less conversational, more
description-and-action dense, talk about power twice as much, and about danger
less. That is what power creep looks like when you measure it instead of arguing
about it — the vocabulary of threat thins out exactly as the vocabulary of
strength thickens.

*What to do with it:* this is the argument for the anti-inflation rails already
in `engine/system.json`, and for the **setback ratio** that `novel.py calibrate`
keeps flagging as untracked. If you take one thing from this whole analysis:
instrument the ratio of chapters where the protagonist ends materially worse
off, and hold it above 20% deliberately, because the drift is real, measurable,
and gradual enough that you will not feel it happening.

---

## 7. Cast philosophy: name freely, drop most

5,408 distinct named entities. Median 1 new per chapter, p90 of 4. **33.6%
appear in exactly one chapter and never again.** Median span between first and
last appearance is 125 chapters; the p90 is 2,706 — a small core persists almost
the entire run.

*Interpretation:* the form names things liberally and lets almost all of them
go. A named character is a scene resource, not a commitment.

*What to do with it:* this is genuinely at odds with this project's design, and
the conflict is worth naming. Your introduction budget enforces a small,
persistent, deeply-built cast — four named characters per arc, each with a wound
and an exit condition. The reference serial does the opposite. Neither is wrong.
But if you ever feel the budget strangling a scene, the alternative is a
**two-tier cast**: keep the dossier discipline for the persistent core, and
allow named-but-disposable figures who exist for one chapter and are never
registered. If you want that, it is a small change to the engine.

---

## What I would actually take

Ranked, for this novel specifically:

1. **High interiority, low emotional vocabulary.** It suits Kestrel exactly and
   costs nothing to adopt.
2. **A nameable objective on the first page of every chapter**, in his terms.
3. **The setback ratio**, instrumented, held above 20%.
4. **Self-contained chapters** if you serialise — the 2.7% continuation figure
   is the real lesson, far more than chapter length.
5. **Sentence and paragraph texture** — only if you are writing for a phone.
   This one is a genuine fork, not an upgrade.

What I would leave: the cast churn, the flat internal profile, and the drift in
stakes language, which is a bug the form tolerates rather than a technique.
