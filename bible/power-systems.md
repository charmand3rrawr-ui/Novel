# Power Systems

How strength works in this world — for everyone, not just the protagonist. The
protagonist's private system (`engine/system-engine.md`) sits on top of these
rules and breaks none of them.

Four ladders run in parallel. Most people climb one. The dangerous ones climb
two.

| Ladder | Raises | Gated by | Visible to others |
|---|---|---|---|
| **Cultivation** | realm, capacity, lifespan | breakthroughs | yes — realm is readable |
| **Martial arts** | technique proficiency | repetition, instruction | partly — style is readable |
| **Sorcery** | pattern authority | comprehension, inscription | yes — sorcery leaves marks |
| **Bloodline** | innate ceiling | awakening conditions | rarely, until it manifests |

## 1. Cultivation — the realms

Every living thing holds **essence**. Cultivation is the practice of widening
what you can hold and refining what you hold into something the world will
obey.

| # | Realm | What changes | Scale of action |
|---|---|---|---|
| 0 | **Unmarked** | nothing; a mortal | a person |
| 1 | **Tempering** (9 gates) | the body stops being the limit | a fight |
| 2 | **Kindling** (early/mid/late/peak) | essence ignites and circulates | a room, a duel |
| 3 | **Nexus** | essence condenses to a seat that persists through sleep and death-shock | a building, a company |
| 4 | **Aperture** | the body opens to the world's essence; external power flows in | a district, a battlefield |
| 5 | **Ascendant** | leaves the ground; ages slowly | a city, a region |
| 6 | **Sovereign** | holds a domain where local law bends to intent | a country, a moon |
| 7 | **Void-Walker** | crosses the dark between bodies unaided | planet to planet |
| 8 | **Unwritten** | passes out of every record that could hold them | unknown |

**Breakthroughs are events, not accumulations.** Meeting the numbers makes a
breakthrough *possible*. It happens in a scene, under pressure, and it costs
something that does not come back (`LK-BREAKTHROUGH-COSTS`).

**Realm is legible.** A cultivator two realms above you can read yours at a
glance; one realm above, with effort; equal, only by fighting. This is why
concealment is a skill and why underestimating is a plot device with rules.

**Realm is not victory.** A Kindling cultivator with a grandmaster's technique,
the right ground, and four minutes of preparation kills a careless Nexus. The
novel must honour this or the tension dies at Realm 3.

## 2. Martial arts — techniques and proficiency

Techniques are owned, taught, stolen, and sold. Each has a **proficiency**
score, 0–100, and four bands:

| Band | Range | What it means |
|---|---|---|
| Rote | 0–24 | you can perform it, slowly, if nothing is happening |
| Fluent | 25–59 | it works in a real fight |
| Mastery | 60–89 | it works when you are exhausted, injured, and surprised |
| Origin | 90–100 | you understand why it was invented, and can alter it |

Proficiency rises with repetition, correction, and near-death. Rate is
multiplied by the practitioner's **talent** in that discipline (below).

Grades run **common → refined → profound → heavenly → origin**. A profound
technique at Fluent beats a common technique at Mastery about half the time,
and the half it loses is the interesting half.

## 3. Sorcery — patterns and inscription

Sorcery is not willpower; it is **notation**. A pattern is a true statement
about how something behaves, written where the world can read it: on a blade,
a wall, a formation floor, the inside of a skull.

- **Comprehension** determines what patterns you can hold in mind.
- **Spirit** determines how many you can drive at once.
- **Inscription** (a profession, see `professions.md`) determines what you can
  fix in place so it does not need driving.

Sorcery is slow, expensive, and unanswerable when prepared. A sorcerer caught
unprepared is a scholar with a knife. The tempo of every sorcery scene is
therefore about *time*, not power.

## 4. Bloodlines — mystical genetic traits

Traits are inherited, rare, and mostly dormant. Four states:

**dormant → stirred → awakened → ascended**

A trait advances only on a **trigger**: a specific pressure, environment,
substance, or proximity. Triggers are discoverable, and half the world's
politics is families guarding the knowledge of what triggers theirs.

Every trait grants a **gift** and carries a **toll**. No exceptions
(`LK-TRAIT-TOLL`). A trait with no toll is a rumour, a forgery, or a trap.

Examples in play — the full registry lives in `engine/system.json → traits`:

- **Iron-Marrow** — bone density and shock tolerance rise sharply. *Toll:* the
  body stops reporting damage accurately.
- **Hollow-Ear** — hears essence move, including through walls and lies.
  *Toll:* cannot filter it; crowds and cities are agony.
- **Thousand-Coin** — abnormal fortune in small things, compounding. *Toll:*
  the luck is conserved; it is taken from someone nearby, always someone known.
- **Kiln-Blood** — the body tolerates heat and reagent toxicity that would kill
  a peer; the great alchemist trait. *Toll:* cannot be healed by ordinary
  medicine; everything must be earned twice.
- **Null-Weave** — patterns fail near them. *Toll:* their own sorcery fails too,
  and cultivators find them unsettling without knowing why.

## 5. Talents — innate aptitude

Talent is not power; it is **rate**. A talent rating multiplies how fast
proficiency and comprehension accumulate in one discipline.

| Rating | Multiplier | Frequency |
|---|---|---|
| dull | 0.5× | common |
| common | 1.0× | the majority |
| keen | 1.5× | one in dozens |
| rare | 2.5× | one in thousands |
| heaven-sent | 4.0× | one in a generation, and everyone knows their name |

Talents are measured per discipline: blade, palm, spear, sorcery, formation,
alchemy, forging, cooking, comprehension, concealment. A person can be
heaven-sent at forging and dull at everything that would keep them alive.

**Talent is public information.** Assessment happens at institutions, on
record, and a high rating buys patronage the way competence buys it in the
chartered houses. This is how the world sorts children, and it is why the
protagonist's private system is so dangerous: it produces results that talent
ratings cannot explain.

## 6. How the ladders interact

- **Essence is finite and local.** A place that has been cultivated in for
  centuries is thin. A place nobody has touched is rich. This drives migration,
  war, and the value of frontier worlds (`bible/cosmology-and-scale.md`).
- **Realm raises the ceiling; technique, sorcery and profession decide what you
  do under it.** Nobody wins on realm alone above Kindling.
- **Bloodline sets the shape of the ceiling**, not its height.
- **Professions convert power into wealth and wealth into power**, which is the
  only reliable ladder for someone without talent — see
  [`professions.md`](professions.md).

## 7. What the power system may never do

Constraints exist so the novel keeps working at chapter sixty. These are canon
locks; see `bible/canon-locks.json`.

- No power reverses death (`LK-DEATH-STANDS`).
- No power reads minds. Intent, emotion, and essence can be *sensed*;
  sentences cannot (`LK-NO-MIND-READING`).
- No breakthrough is free (`LK-BREAKTHROUGH-COSTS`).
- Every bloodline trait carries a toll (`LK-TRAIT-TOLL`).
- Distance between worlds still takes time below Void-Walker (`LK-DISTANCE`).
