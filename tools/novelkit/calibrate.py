"""Compare the engine's tempo against genre architecture.

Two sources of truth, and the module is careful about which is which:

- `engine/genre-priors.json` — estimates from familiarity with the form. Wide
  ranges, honestly labelled, nobody measured them.
- `inspiration/structure-metrics.json` — real numbers, measured by
  `tools/analyze_structure.py` from text the author had the right to analyse.

Measurements beat priors wherever both exist.
"""

from __future__ import annotations

from . import store

PRIORS = store.ENGINE / "genre-priors.json"
METRICS = store.INSPIRATION / "structure-metrics.json"


def report() -> list[str]:
    priors = store.load(PRIORS)
    metrics = store.load(METRICS, {"sets": {}})
    tempo = store.load(store.TEMPO)
    arcs = store.load(store.ARCS)
    out, findings = [], []

    cs = priors["chapter_shape"]
    out.append("Tempo vs genre architecture")
    out.append("=" * 62)

    lo, hi = cs["words"]["typical_range"]
    ideal = tempo["chapter_target_words"]["ideal"]
    ok = lo <= ideal <= hi
    out.append(f" {'ok ' if ok else 'OFF'} chapter words         yours {ideal:<6} prior {lo}-{hi}")
    if not ok:
        findings.append(f"chapter_target_words.ideal ({ideal}) sits outside the genre range {lo}-{hi}")

    yours = tempo["cadence_rules"]["cliffhanger_ratio"]
    prior = cs["closing_move_distribution"]["hook_or_cliffhanger"]
    ok = abs(yours - prior) <= 0.1
    out.append(f" {'ok ' if ok else 'OFF'} cliffhanger ratio     yours {yours:<6} prior ~{prior}")
    if not ok:
        findings.append(
            f"cliffhanger_ratio {yours} is a novel's number; serials run ~{prior}. "
            "Readers arrive daily and need a reason to come back tomorrow.")

    lengths = [a["chapters"][1] - a["chapters"][0] + 1 for a in arcs["arcs"]]
    mlo, mhi = priors["arc_architecture"]["micro_arc_chapters"]["typical_range"]
    Mlo, Mhi = priors["arc_architecture"]["major_arc_chapters"]["typical_range"]
    total = max(a["chapters"][1] for a in arcs["arcs"])
    out.append(f"     arc lengths           yours {lengths}  (total {total} chapters)")
    out.append(f"                           prior micro {mlo}-{mhi}, major {Mlo}-{Mhi}")
    if all(l <= mhi for l in lengths):
        findings.append(
            f"every arc is micro-arc sized ({min(lengths)}-{max(lengths)} chapters) and the book ends at "
            f"{total}. That is a literary-novel architecture. A web serial usually nests micro-arcs of "
            f"{mlo}-{mhi} inside major arcs of {Mlo}-{Mhi}. Decide deliberately which you are writing.")

    nlo, nhi = priors["cast_and_world_expansion"]["named_character_introductions_per_micro_arc"]["typical_range"]
    yn = tempo["introduction_budget"]["named_characters_per_arc"]
    ok = nlo <= yn <= nhi
    out.append(f" {'ok ' if ok else 'OFF'} names per arc         yours {yn:<6} prior {nlo}-{nhi}")

    glo, ghi = priors["progression_cadence"]["gain_to_spend_window"]["typical_range"]
    ylo = tempo["seed_policy"]["payoff_window_chapters"]["min"]
    out.append(f"     gain-to-spend window  yours min {ylo:<2}   prior {glo}-{ghi}")

    ed = priors["cast_and_world_expansion"].get("measured_entity_dynamics")
    if ed:
        yn2 = tempo["introduction_budget"]["new_proper_nouns_per_chapter"]
        ok = ed["new_per_chapter_p90"] <= yn2 <= ed["new_per_chapter_p90"] + 3
        out.append(f" {'ok ' if ok else '   '} new proper nouns/ch   yours {yn2:<6} "
                   f"measured median {ed['new_per_chapter_median']}, p90 {ed['new_per_chapter_p90']}")
        out.append(f"     entity churn          measured {int(ed['single_chapter_share'] * 100)}% of named things "
                   f"appear in exactly one chapter")
        findings.append(
            f"measured cast philosophy differs from yours: {int(ed['single_chapter_share'] * 100)}% of named "
            f"entities appear once and never again, median span {ed['median_span_chapters']} chapters. Your "
            f"budget of {tempo['introduction_budget']['named_characters_per_arc']} named characters per arc "
            "enforces a small persistent cast; the reference serial names freely and drops most. Both work — "
            "but they are different books.")

    mp = priors["progression_cadence"].get("measured_payoff_window")
    if mp:
        hard = tempo["seed_policy"]["payoff_window_chapters"]["hard_max"]
        out.append(f"     seed rot threshold    yours {hard:<6} measured median long return "
                   f"{mp['median_long_return_chapters']}, p90 {mp['p90_long_return_chapters']}")
        if hard < mp["median_long_return_chapters"]:
            findings.append(
                f"seed rot fires at {hard} chapters, but the measured median long return is "
                f"{mp['median_long_return_chapters']} chapters and the p90 is {mp['p90_long_return_chapters']}. "
                "Your engine would force-retire exactly the deep plants the form is built on. Consider "
                "soft_max 40 / hard_max 120 if you are writing a serial.")

    ma = priors["arc_architecture"].get("measured_arc_length")
    if ma:
        out.append(f"     arc length            yours {lengths}  measured median "
                   f"{ma['median_chapters_between_boundaries']} (p10 {ma['p10']}, p90 {ma['p90']})")

    pa = priors.get("plot_architecture")
    if pa:
        yc = tempo["cadence_rules"]["max_consecutive_action_chapters"]
        out.append(f"     consecutive action    yours {yc:<6} measured max run "
                   f"{pa['run_length_max']['combat']}, combat self-transition "
                   f"{int(pa['self_transition']['combat'] * 100)}%")
        if yc < 5:
            findings.append(
                f"max_consecutive_action_chapters is {yc}; measured combat runs reach "
                f"{pa['run_length_max']['combat']} chapters with a {int(pa['self_transition']['combat'] * 100)}% "
                "self-transition rate. Three is a literary novel's limit — raise it or exempt declared set-pieces.")

    slo, shi = priors["progression_cadence"]["setback_ratio"]["typical_range"]
    out.append(f"     setback ratio         not tracked   prior {slo}-{shi}")
    findings.append(
        f"setback ratio is not in tempo.json. The genre's most common failure is a protagonist who never "
        f"ends a chapter worse off; {int(slo * 100)}-{int(shi * 100)}% of chapters should cost him something.")

    if metrics["sets"]:
        out.append("")
        out.append("Measured sets (real numbers, these beat priors)")
        out.append("-" * 62)
        for label, s in metrics["sets"].items():
            sm = s["summary"]
            out.append(f" {label}  ({sm['chapters_measured']} chapters, measured {s['measured']})")
            out.append(f"   words median {sm['words']['median']}  p10 {sm['words']['p10']}  p90 {sm['words']['p90']}")
            out.append(f"   dialogue ratio {sm['dialogue_ratio_median']}  "
                       f"avg paragraph {sm['avg_paragraph_words']} words")
            out.append(f"   openings {sm['opening_move_distribution']}")
            out.append(f"   closings {sm['closing_move_distribution']}")
    else:
        out.append("")
        out.append(" No measurements stored. Priors only — they are estimates, not data.")
        out.append(" Measure real text you have the right to analyse:")
        out.append("   tools/analyze_structure.py --dir <chapters> --label <name>")

    if findings:
        out.append("")
        out.append("Findings")
        out.append("-" * 62)
        for f in findings:
            out.append(f" • {f}")
    out.append("")
    out.append("Priors are estimates — see engine/genre-priors.json provenance before acting on them.")
    return out
