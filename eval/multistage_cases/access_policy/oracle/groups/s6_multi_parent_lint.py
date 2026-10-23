from warden import lint, parse_policy


def test_role_combining_parents_is_not_redundant():
    text = ("role viewer\nrole auditor\nrole lead inherits viewer, auditor\nrole senior inherits viewer\n"
            "allow viewer read **\nallow auditor list **\n")
    assert {(finding.code, finding.message) for finding in lint(parse_policy(text))} == {
        ("redundant-role", "role senior adds nothing to viewer"),
    }


def test_parents_count_as_inherited():
    text = "role viewer\nrole auditor\nrole lead inherits viewer, auditor\nallow lead read **\n"
    assert [finding.code for finding in lint(parse_policy(text))] == []
