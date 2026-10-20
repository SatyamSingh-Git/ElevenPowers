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
