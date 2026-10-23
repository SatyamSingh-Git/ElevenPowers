from warden import lint, parse_policy


def test_parents_count_as_inherited():
    text = "role viewer\nrole auditor\nrole lead inherits viewer, auditor\nallow lead read **\n"
    assert [finding.code for finding in lint(parse_policy(text))] == []
