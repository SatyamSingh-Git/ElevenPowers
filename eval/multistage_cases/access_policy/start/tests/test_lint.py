from warden import lint, parse_policy


def findings(text):
    return [(finding.code, finding.message) for finding in lint(parse_policy(text))]


def test_clean_policy():
    assert findings("role viewer\nrole editor inherits viewer\nallow viewer read **\nallow editor write **\n") == []


def test_role_findings():
    text = "role viewer\nrole editor inherits viewer\nrole guest\nallow viewer read **\n"
    assert findings(text) == [
        ("redundant-role", "role editor adds nothing to viewer"),
        ("unused-role", "role guest is never used"),
    ]


def test_shadowed_by_inherited_deny():
    text = ("role viewer\nrole editor inherits viewer\n"
            "deny viewer * reports/**\nallow editor write reports/*.csv\n")
    assert findings(text) == [("shadowed-rule", "rule 2 can never apply: rule 1 denies it")]


def test_conditional_deny_does_not_shadow():
    text = ("role viewer\nrole editor inherits viewer\n"
            "deny viewer * reports/** when resource.locked == true\nallow editor write reports/*.csv\n")
    assert findings(text) == []


def test_duplicate():
    text = "role viewer\nallow viewer read,list **\nallow viewer list,read **\n"
    assert findings(text) == [("duplicate-rule", "rule 2 repeats rule 1")]
