"""The pre-registered analysis of a multi-stage run, and joining a run with its continuation."""
import pytest

from eval import multistage_analyse as a


def _row(case, arm, replicate, lost=0, stale=0, comparable=True):
    return {'slot': f'{case}--{arm}--{replicate}', 'case': case, 'arm': arm, 'replicate': replicate,
            'state': 'completed' if comparable else 'incomplete', 'comparable': comparable,
            'lost': lost if comparable else None, 'stale': stale if comparable else None}


def test_a_continuation_fills_only_the_slots_the_first_batch_did_not_complete():
    first = [_row('c', 'superpowers', 0, lost=1), _row('c', 'elevenpowers', 0, comparable=False),
             _row('c', 'superpowers', 1, comparable=False)]
    continuation = [_row('c', 'superpowers', 0, lost=9), _row('c', 'elevenpowers', 0, lost=2),
                    _row('c', 'superpowers', 1, comparable=False)]
    merged = {row['slot']: row for row in a.merge(first, continuation)}
    assert merged['c--superpowers--0']['lost'] == 1
    assert merged['c--elevenpowers--0']['lost'] == 2
    assert merged['c--superpowers--1']['comparable'] is False
    assert len(merged) == 3


def test_every_case_better_with_elevenpowers_is_a_positive_difference_and_holm_doubles_the_smaller_p():
    rows = [_row(f'c{i}', arm, 0, lost=2 if arm == 'superpowers' else 0) for i in range(6)
            for arm in ('superpowers', 'elevenpowers')]
    result = a.analyse(rows)
    lost, stale = result['outcomes']['lost'], result['outcomes']['stale']
    assert (lost['better'], lost['worse'], lost['tied']) == (6, 0, 0)
    assert lost['p'] == pytest.approx(2 / 64)
    assert lost['p_holm'] == pytest.approx(4 / 64)
    assert stale['p'] == 1.0 and stale['p_holm'] == 1.0
    assert lost['totals'] == {'superpowers': 12, 'elevenpowers': 0}


def test_holm_never_adjusts_the_larger_p_below_the_smaller():
    rows = [_row(f'c{i}', arm, 0, lost=2 if arm == 'superpowers' else 0, stale=1 if arm == 'superpowers' else 0)
            for i in range(6) for arm in ('superpowers', 'elevenpowers')]
    outcomes = a.analyse(rows)['outcomes']
    assert outcomes['lost']['p_holm'] == outcomes['stale']['p_holm'] == pytest.approx(4 / 64)


def test_a_tie_is_counted_and_kept_out_of_the_ranks():
    rows = [_row('c', 'superpowers', 0, lost=1), _row('c', 'elevenpowers', 0, lost=1),
            _row('d', 'superpowers', 0, lost=0), _row('d', 'elevenpowers', 0, lost=2)]
    lost = a.analyse(rows)['outcomes']['lost']
    assert (lost['better'], lost['worse'], lost['tied']) == (0, 1, 1)
    assert lost['p'] == 1.0


def test_a_case_is_the_mean_over_its_replicates():
    rows = [_row('c', 'superpowers', 0, lost=3), _row('c', 'superpowers', 1, lost=0),
            _row('c', 'elevenpowers', 0, lost=1), _row('c', 'elevenpowers', 1, lost=1)]
    assert a.analyse(rows)['outcomes']['lost']['cases'] == {'c': 0.5}


def test_a_missing_conversation_is_reported_never_counted_as_zero():
    rows = [_row('c', 'superpowers', 0, lost=4), _row('c', 'elevenpowers', 0, comparable=False),
            _row('d', 'superpowers', 0, lost=1), _row('d', 'elevenpowers', 0, lost=0)]
    result = a.analyse(rows)
    assert result['conversations'] == {'scheduled': 4, 'comparable': 3,
                                       'missing': {'superpowers': 0, 'elevenpowers': 1}}
    assert result['outcomes']['lost']['cases'] == {'d': 1.0}
    assert result['outcomes']['lost']['totals'] == {'superpowers': 5, 'elevenpowers': 0}
