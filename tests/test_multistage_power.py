"""Power for multi-stage v2: counts per conversation, analysed per case."""
import pytest

from eval.multistage_power import exact_signed_rank, power


def test_the_exact_signed_rank_matches_its_smallest_attainable_value():
    assert exact_signed_rank([1, 2, 3, 4, 5, 6, 7, 8]) == pytest.approx(2 / 256)
    assert exact_signed_rank([-1, -2, -3, -4, -5, -6, -7, -8]) == pytest.approx(2 / 256)


def test_no_evidence_gives_no_rejection():
    assert exact_signed_rank([]) == 1.0
    assert exact_signed_rank([0, 0, 0]) == 1.0
    assert exact_signed_rank([1, -1]) == 1.0


def test_tied_magnitudes_share_their_rank():
    # Ranks 1.5, 1.5, 3: only the all-positive and all-negative flips reach 6.
    assert exact_signed_rank([2, 2, 5]) == pytest.approx(2 / 8)


def test_equal_means_of_thirds_tie_despite_float_rounding():
    # 1 - 2/3 is 0.33333333333333337 and 1/3 is 0.3333333333333333: the same mean difference.
    assert exact_signed_rank([-(1 / 3), 1 - 2 / 3, 0.5, 0.7]) == pytest.approx(
        exact_signed_rank([-(1 / 3), 1 / 3, 0.5, 0.7]))
    assert exact_signed_rank([-(1 / 3), 1 / 3, 0.5, 0.7]) == pytest.approx(3 / 8)


def test_no_effect_rejects_at_about_alpha_or_less():
    got = power(cases=8, replicates=3, rate=0.5, ratio=1.0, heterogeneity=0.5, simulations=400, seed=1)
    assert got["rejection_rate"] <= 0.05


def test_a_strong_effect_is_found():
    got = power(cases=8, replicates=3, rate=2.0, ratio=0.1, heterogeneity=0.5, simulations=200, seed=1)
    assert got["rejection_rate"] >= 0.8
    assert got["conversations"] == 48


@pytest.mark.parametrize("change", [{"cases": 0}, {"ratio": 0}, {"rate": -1}, {"replicates": 0}])
def test_an_impossible_design_is_refused(change):
    arguments = dict(cases=8, replicates=2, rate=0.5, ratio=0.5, heterogeneity=0.5, simulations=10, seed=1) | change
    with pytest.raises(ValueError):
        power(**arguments)
