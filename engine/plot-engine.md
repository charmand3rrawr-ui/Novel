# The Plot Engine

A 1,337-chapter macro plot, generated from measured serial architecture, that
the protagonist's own state is allowed to overrule.

Two files and two commands do the work:

| | |
|---|---|
| `plot-skeleton.json` | the plan: volumes, arcs, phases, chapter types, ladder, seeds |
| `novel.py plot build` | regenerates it |
| `novel.py plot show` | where a chapter sits in the plan |
| `novel.py plot next` | **what the plot owes right now, given his actual state** |

## What the skeleton is built from

Nothing in the structure is invented. Every parameter traces to
`engine/genre-priors.json` and `chapters/PLOT-ARCHITECTURE.md`:

- **Arc lengths** cluster around the measured median of 29 chapters, with the
  measured long tail — most arcs 20–38, a few sprawling past 100.
- **Chapter types** are a Markov walk over the measured transition matrix, so
  combat chains the way it actually chains (50.2% self-transition) and
  revelation stays the connective tissue.
- **The seven-phase macro cycle** — arrival, friction, demonstration,
  escalation, resource, confrontation, departure — shapes each arc and biases
  the walk, so a confrontation stretch fights and an arrival stretch travels.
- **Seeds** are planted with payoff distances drawn from the measured
  return-gap distribution: 65% near (3–39 chapters), 27% deep (40–120), 8% very
  deep (121–475).
- **The ladder** places every realm and stage against the page count, spaced so
  the protagonist cannot outrun 1,337 chapters.

The *content* — pressures, stakes, questions, gains — is this novel's own,
recombined from the world in `bible/`.

## The half that matters: progression drives plot

A skeleton is a plan, and the plan is wrong the moment the protagonist diverges
from it. `novel.py plot next` reads the live system state and emits directives
that **outrank the arc plan**:

| Trigger | Directive |
|---|---|
| residue ≥ 75 | `CRISIS` — a deviation event is overdue and lands at the worst time |
| residue ≥ 50 | `PRESSURE` — expose it in a confrontation before he can purge |
| residue ≥ 25 | `SEED` — sleep and perception going wrong in small ways |
| a cost track at its floor | `RUPTURE` — something breaks that competence cannot repair |
| a trait stirred | `TRIGGER` — its trigger becomes reachable, its toll lands on the page |
| realm requirements met | `BREAKTHROUGH` — needs a confrontation phase and a permanent cost |
| realm behind the plan | `TRAJECTORY` — an arc between here and there must supply it |
| ≥ 40 unspent points | `INVENTORY` — force a scene requiring what he has not bought |

It also reports **divergence**: if he is ahead of or behind the ladder the plan
assumed, it says so, and says whether to escalate the coming arcs or rebuild
them. `plot build --sync` regenerates and projects into `engine/arcs.json`.

That is the loop the request asked for: the plan proposes, his state disposes.

## Casting

```
novel.py plot cast A07 --limit 4
```

Generates the bench an arc's phases actually call for — roles filtered by what
the arc licenses — with **random personalities** built from contradictory atoms
in `inspiration/lexicon.json`. Each carries the arc's own need string, so
`character introduce` has a sentence to check against. Nothing reaches the page
until introduced.

## Rebuilding

The skeleton is disposable. `plot build --seed N` reproduces one exactly;
omitting the seed rolls a new plot. Rebuilding mid-novel is expected — that is
what divergence is for. What survives a rebuild is everything real: the
continuity index, the registries, the system status and log.
