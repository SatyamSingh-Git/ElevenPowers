"""Power of a task-level paired vacuity comparison, simulated before any spending."""
import pytest


def test_no_effect_rejects_at_most_alpha():
    from eval.vacuity_power import power
    value = power(tasks=25, replicates=2, vanilla_vacuity=0.22, odds_ratio=1.0, resolve=0.92,
                  heterogeneity=1.0, simulations=4000, seed=1)
    assert value["rejection_rate"] <= 0.05


def test_a_large_effect_on_many_tasks_is_usually_detected():
    from eval.vacuity_power import power
    value = power(tasks=60, replicates=3, vanilla_vacuity=0.22, odds_ratio=0.2, resolve=0.92,
                  heterogeneity=0.5, simulations=2000, seed=2)
    assert value["rejection_rate"] >= 0.8


def test_more_tasks_never_buy_less_power_at_the_same_effect():
    from eval.vacuity_power import power
    small, large = (power(tasks=t, replicates=2, vanilla_vacuity=0.22, odds_ratio=0.31, resolve=0.92,
                          heterogeneity=1.0, simulations=3000, seed=3)["rejection_rate"] for t in (16, 48))
    assert large > small


def test_unresolved_runs_cannot_be_vacuous_and_shrink_the_evidence():
    from eval.vacuity_power import power
    resolved, unresolved = (power(tasks=40, replicates=2, vanilla_vacuity=0.22, odds_ratio=0.2, resolve=r,
                                  heterogeneity=0.5, simulations=2000, seed=4)["rejection_rate"] for r in (0.95, 0.3))
    assert resolved > unresolved


@pytest.mark.parametrize("bad", [{"tasks": 0}, {"replicates": 0}, {"vanilla_vacuity": 1.2}, {"odds_ratio": -1}])
def test_invalid_design_is_refused(bad):
    from eval.vacuity_power import power
    design = dict(tasks=10, replicates=2, vanilla_vacuity=0.2, odds_ratio=0.5, resolve=0.9,
                  heterogeneity=1.0, simulations=10, seed=0) | bad
    with pytest.raises(ValueError):
        power(**design)


def test_signed_rank_keeps_the_null_at_alpha_and_is_not_weaker_than_sign():
    from eval.vacuity_power import power
    design = dict(tasks=40, replicates=3, vanilla_vacuity=0.22, resolve=0.92, heterogeneity=1.0, simulations=2000)
    null = power(**design, odds_ratio=1.0, seed=5, test="signed-rank")["rejection_rate"]
    sign, ranked = (power(**design, odds_ratio=0.31, seed=6, test=t)["rejection_rate"] for t in ("sign", "signed-rank"))
    assert null <= 0.06 and ranked >= sign
