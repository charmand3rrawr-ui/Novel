# Style Guide

The prose contract. The engine enforces structure; this file holds the voice.

## Point of view

Close third, past tense, one POV per chapter. POV may not switch more often
than `tempo.json → cadence_rules.pov_switch_min_gap`. The reader should always
be able to answer "whose chapter is this?" from the first paragraph.

## Sentences

- Concrete nouns carry the scene; adjectives are rationed.
- Vary length deliberately. A short sentence after three long ones is the
  novel's main emphasis tool. Do not spend it on nothing.
- No more than one simile per scene, and it must come from the POV character's
  own field of knowledge. Kestrel thinks in instruments and terms.

## Dialogue

- Attribution is *said* unless the verb is doing real work.
- Every named character has one speech habit recorded in their dossier
  (`surface.verbal_tic`). Use it sparingly; three appearances is a
  characterisation, six is a tic the reader starts hating.
- People talk past each other more often than they clash directly. The ledger
  is a world of implication.

## Exposition

- The bible exists so the prose does not have to explain. Reveal the world
  through use, pricing, and consequence.
- Never explain an instrument before a character needs it. The reader learns
  what a *standing* is by watching one bite.
- Hard cap: `tempo.json → introduction_budget.new_proper_nouns_per_chapter`.

## Chapter shape

- Open in motion or in pressure, never in preparation.
- Close on a change of state, not on a summary.
- Cliffhanger ratio is a budget, not a habit
  (`cadence_rules.cliffhanger_ratio`). A chapter that ends quietly after a loud
  one is worth more than another hook.

## Forbidden

- Dream sequences used as revelation.
- Prophecy, destiny, or foreknowledge of any kind (`LK-NO-PROPHECY`).
- A character explaining their own wound in dialogue (`LK-EARNED-WOUND`).
- Power levels quoted as numbers in the prose. The status sheet is the
  author's instrument, not the reader's; on the page, strength is shown by what
  it does to a room.
- An institution arriving to save the protagonist (`LK-NO-RESCUE`).
