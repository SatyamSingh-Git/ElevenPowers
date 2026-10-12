from test_patchproof_openapi import engine


def test_two_unrelated_real_contract_projects(tmp_path, engine):
    from eval.openapi_contracts import exercise
    value = exercise(tmp_path / 'exercise', engine)
    assert value['model_calls'] == 0 and value['coding_benefit'] == 'not_measured'
    assert len(value['projects']) == 2
    for project in value['projects']:
        assert project['states'] == ['current', 'failed', 'incomplete', 'stale', 'absent']
        assert project['independent_head_matches'] and project['independent_input_matches']
