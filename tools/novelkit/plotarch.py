"""Plot architecture, measured.

Not plot. The *organisation* of plot: what kind of chapter follows what kind,
how long runs of one type last, how conflict density oscillates, where the cast
turns over, and how far setups travel before they pay off.

Everything here consumes per-chapter numbers and entity sets and produces
counts, probabilities and positions. No events, no names, no summaries.
"""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict

TYPES = ["combat", "training", "negotiation", "travel", "revelation"]


def classify_chapters(rates: list[dict]) -> list[str]:
    """Label each chapter by which plot register is most elevated relative to
    that register's own corpus norm. Comparing a register to itself avoids the
    trap where a naturally common register wins every chapter."""
    norms = {}
    for t in TYPES:
        series = [r.get(t, 0.0) for r in rates]
        mean = statistics.mean(series) or 1.0
        sd = statistics.pstdev(series) or 1.0
        norms[t] = (mean, sd)
    out = []
    for r in rates:
        best, best_z = None, float("-inf")
        for t in TYPES:
            mean, sd = norms[t]
            z = (r.get(t, 0.0) - mean) / sd
            if z > best_z:
                best, best_z = t, z
        out.append(best if best_z > 0.15 else "mixed")
    return out


def transition_matrix(labels: list[str]) -> dict:
    """P(next type | current type). The single most informative view of plot
    architecture: it says what the form thinks should follow a fight."""
    counts = defaultdict(Counter)
    for a, b in zip(labels, labels[1:]):
        counts[a][b] += 1
    matrix = {}
    for a, row in counts.items():
        total = sum(row.values())
        matrix[a] = {b: round(n / total, 3) for b, n in row.most_common()}
        matrix[a]["_n"] = total
    return matrix


def run_lengths(labels: list[str]) -> dict:
    runs = defaultdict(list)
    cur, n = labels[0], 1
    for lab in labels[1:]:
        if lab == cur:
            n += 1
        else:
            runs[cur].append(n)
            cur, n = lab, 1
    runs[cur].append(n)
    return {t: {"runs": len(v), "median": statistics.median(v), "max": max(v),
                "share_length_1": round(sum(1 for x in v if x == 1) / len(v), 3)}
            for t, v in sorted(runs.items())}


def autocorrelation(series: list[float], max_lag: int = 30) -> list[dict]:
    """Rhythm. A peak at lag k means the density recurs every k chapters."""
    n = len(series)
    mean = statistics.mean(series)
    denom = sum((x - mean) ** 2 for x in series) or 1.0
    out = []
    for lag in range(1, min(max_lag, n // 4) + 1):
        num = sum((series[i] - mean) * (series[i + lag] - mean) for i in range(n - lag))
        out.append({"lag": lag, "r": round(num / denom, 4)})
    return out


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / max(1, len(a | b))


def cast_turnover(entity_sets: list[set], window: int = 10, threshold: float = 0.12) -> dict:
    """Arc boundaries, found by cast replacement. When the set of named things
    in the last N chapters barely overlaps the next N, the story has moved."""
    sims = []
    for i in range(window, len(entity_sets) - window):
        before = set().union(*entity_sets[i - window:i])
        after = set().union(*entity_sets[i:i + window])
        sims.append((i + 1, _jaccard(before, after)))
    if not sims:
        return {}
    values = [s for _, s in sims]
    boundaries, last = [], -999
    # The 5th percentile of observed overlap, not a fixed constant: a constant
    # below the series minimum silently detects nothing, which is how this
    # first reported zero boundaries across 3,204 chapters.
    floor = statistics.quantiles(values, n=20)[0] if len(values) >= 20 else min(values)
    floor = min(floor, threshold) if threshold > floor else floor
    for pos, s in sims:
        if s <= floor and pos - last >= window:
            boundaries.append({"chapter": pos, "overlap": round(s, 3)})
            last = pos
    gaps = [b["chapter"] - a["chapter"] for a, b in zip(boundaries, boundaries[1:])]
    return {
        "window": window,
        "median_overlap": round(statistics.median(values), 3),
        "boundary_threshold": round(floor, 3),
        "boundaries_detected": len(boundaries),
        "median_gap_between_boundaries": int(statistics.median(gaps)) if gaps else None,
        "p10_gap": int(statistics.quantiles(gaps, n=10)[0]) if len(gaps) >= 10 else None,
        "p90_gap": int(statistics.quantiles(gaps, n=10)[-1]) if len(gaps) >= 10 else None,
        "first_boundaries": boundaries[:12],
    }


def return_gaps(entity_sets: list[set], long_gap: int = 20) -> dict:
    """Setup and payoff, measured. An entity that vanishes for 40 chapters and
    returns is a plant being cashed. The distribution of those gaps is the
    novel's memory."""
    seen = defaultdict(list)
    for i, s in enumerate(entity_sets):
        for e in s:
            seen[e].append(i)
    gaps = []
    for positions in seen.values():
        gaps.extend(b - a for a, b in zip(positions, positions[1:]) if b - a > 1)
    longs = [g for g in gaps if g >= long_gap]
    if not gaps:
        return {}
    return {
        "total_absences": len(gaps),
        "median_absence_chapters": int(statistics.median(gaps)),
        "long_returns": len(longs),
        "long_return_share": round(len(longs) / len(gaps), 3),
        "median_long_return": int(statistics.median(longs)) if longs else None,
        "p90_long_return": int(statistics.quantiles(longs, n=10)[-1]) if len(longs) >= 10 else None,
        "max_return_gap": max(gaps),
        "note": f"A 'long return' is an entity absent {long_gap}+ chapters that reappears — the measurable "
                "signature of a setup being paid off.",
    }


def analyse(rates: list[dict], entity_sets: list[set], words: list[int]) -> dict:
    labels = classify_chapters(rates)
    conflict = [r.get("combat", 0.0) for r in rates]
    ac = autocorrelation(conflict)
    top = sorted(ac, key=lambda x: -x["r"])[:5]
    return {
        "chapter_type_distribution": {k: round(v / len(labels), 3)
                                      for k, v in Counter(labels).most_common()},
        "transition_matrix": transition_matrix(labels),
        "run_lengths": run_lengths(labels),
        "conflict_rhythm": {
            "autocorrelation_peaks": top,
            "note": "r is the correlation of combat density with itself at lag k. Values near zero mean "
                    "confrontation is scheduled by story need, not by a repeating cycle.",
        },
        "cast_turnover": cast_turnover(entity_sets),
        "setup_payoff": return_gaps(entity_sets),
    }
