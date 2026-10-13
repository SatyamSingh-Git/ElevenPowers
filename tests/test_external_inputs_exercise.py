"""Controller-owned actual good/drifted/incomplete dependency acceptance."""


def test_actual_external_input_exercise_has_independent_outcomes(tmp_path):
    from eval.external_inputs import exercise
    result = exercise(tmp_path/'new')
    assert result['schema'] == 1 and result['readonly']
    assert [c['language'] for c in result['cases']] == ['python','javascript']
    for case in result['cases']:
        assert case['initial'] == 'passed' and case['unchanged'] == 'reused'
        assert case['independent_bad_exit'] != 0 and case['drift_action'] == 'run'
        assert case['drift'] == 'failed' and case['missing'] == 'incomplete'
        assert case['counts'] == [1,1,2,3,3]
