"""The held-out analysis is fixed before any outcome: per-task vacuity, signed-rank, replicates aggregated."""
import math


def run(task, arm, *, resolved=True, vacuous=False, state="graded", seconds=60.0, cost=0.5):
    return {"task": task, "arm": arm, "state": state, "resolved": resolved,
            "vacuous": vacuous if resolved else None, "seconds": seconds, "cost": cost}


def test_primary_statistic_matches_a_hand_computation():
    from eval.heldout_analyse import analyse
    from eval.vacuity_power import _signed_rank
    records = []
    # Per task: ordinary vacuous fraction minus assisted vacuous fraction.
    plan = {"t1": ([True, True], [False, False]),      # 1.0 - 0.0 = 1.0
            "t2": ([True, False], [False, False]),     # 0.5 - 0.0 = 0.5
            "t3": ([False, False], [True, False]),     # 0.0 - 0.5 = -0.5
            "t4": ([False, False], [False, False])}    # tie, dropped
    for task, (ordinary, assisted) in plan.items():
        records += [run(task, "ordinary", vacuous=v) for v in ordinary]
        records += [run(task, "assisted", vacuous=v) for v in assisted]

    value = analyse(records)

    assert value["primary"]["differences"] == {"t1": 1.0, "t2": 0.5, "t3": -0.5}
    assert value["primary"]["tied"] == 1 and value["primary"]["dropped_unresolved"] == 0
    assert math.isclose(value["primary"]["p"], _signed_rank([1.0, 0.5, -0.5]))


def test_duplicated_runs_of_a_task_do_not_change_the_number_of_tasks():
    from eval.heldout_analyse import analyse
    records = [run("t1", "ordinary", vacuous=True), run("t1", "assisted"), run("t2", "ordinary"), run("t2", "assisted", vacuous=True)]
    once, twice = analyse(records), analyse(records * 3)
    assert once["primary"]["differences"] == twice["primary"]["differences"]
    assert once["primary"]["p"] == twice["primary"]["p"]


def test_a_task_with_no_resolved_run_in_one_arm_is_dropped_and_counted():
    from eval.heldout_analyse import analyse
    records = [run("t1", "ordinary", vacuous=True), run("t1", "assisted", resolved=False)]
    value = analyse(records)
    assert value["primary"]["differences"] == {} and value["primary"]["dropped_unresolved"] == 1


def test_incomplete_runs_are_counted_but_never_graded():
    from eval.heldout_analyse import analyse
    records = [run("t1", "ordinary", vacuous=True), run("t1", "assisted", vacuous=False, state="timeout"),
               run("t1", "assisted")]
    value = analyse(records)
    assert value["runs"] == {"scheduled": 3, "graded": 2, "incomplete": 1}
    assert value["primary"]["differences"] == {"t1": 1.0}


def test_secondary_resolve_rate_is_reported_beside_never_instead():
    from eval.heldout_analyse import analyse
    records = [run("t1", "ordinary", resolved=False), run("t1", "assisted"),
               run("t2", "ordinary", resolved=False), run("t2", "assisted")]
    value = analyse(records)
    assert value["secondary"]["resolve"]["assisted_better"] == 2 and value["secondary"]["resolve"]["ordinary_better"] == 0
    assert "primary" in value and value["primary"]["differences"] == {}


def test_holm_adjusts_a_hand_computed_list():
    from eval.heldout_analyse import holm
    assert [round(p, 6) for p in holm([0.01, 0.04, 0.03, 0.2, 0.001])] == [0.04, 0.09, 0.09, 0.2, 0.005]
    assert holm([0.6, 0.5]) == [1.0, 1.0]


def test_the_four_arm_primaries_are_the_five_pairs_each_as_the_two_arm_analysis_would_compute():
    from eval.heldout_analyse import PAIRS, compare, four, holm
    plan = {"t1": {"ordinary": [True, True], "instructed": [False, True], "superpowers": [False, False], "assisted": [False, False]},
            "t2": {"ordinary": [True, False], "instructed": [False, False], "superpowers": [False, True], "assisted": [True, False]},
            "t3": {"ordinary": [True, True], "instructed": [True, True], "superpowers": [False, False], "assisted": [False, True]}}
    records = [run(task, arm, vacuous=v) for task, arms in plan.items() for arm, values in arms.items() for v in values]
    records.append(run("t1", "superpowers", state="plugins_unqualified", vacuous=True))
    value = four(records)
    assert PAIRS == (("ordinary", "instructed"), ("ordinary", "superpowers"), ("instructed", "assisted"),
                     ("superpowers", "assisted"), ("ordinary", "assisted"))
    assert list(value["primary"]) == [f"{a} - {b}" for a, b in PAIRS]
    assert value["primary"]["ordinary - instructed"]["differences"] == {"t1": 0.5, "t2": 0.5}
    # t1 and t2 tie; the unqualified superpowers run of t1 is not counted.
    assert value["primary"]["superpowers - assisted"]["differences"] == {"t3": -0.5}
    assert value["primary"]["superpowers - assisted"]["tied"] == 2
    raw = [compare(records, a, b)["p"] for a, b in PAIRS]
    assert [value["primary"][f"{a} - {b}"]["p"] for a, b in PAIRS] == raw
    assert [value["primary"][f"{a} - {b}"]["holm_p"] for a, b in PAIRS] == holm(raw)
    assert value["runs"] == {"scheduled": 25, "graded": 24, "incomplete": 1}


def test_the_four_arm_secondaries_count_patches_changing_a_test_per_arm():
    from eval.heldout_analyse import four
    records = [dict(run("t1", "ordinary", vacuous=True), changes_test=False),
               dict(run("t1", "assisted"), changes_test=True),
               dict(run("t1", "instructed", resolved=False), changes_test=True)]
    shares = four(records)["secondary"]["resolved_changing_a_test"]
    assert shares["ordinary"] == {"resolved": 1, "changing_a_test": 0}
    assert shares["assisted"] == {"resolved": 1, "changing_a_test": 1}
    assert shares["instructed"] == {"resolved": 0, "changing_a_test": 0}
