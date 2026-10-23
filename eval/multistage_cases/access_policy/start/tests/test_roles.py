import pytest

from warden.errors import RoleError
from warden.roles import MAX_CHAIN, RoleGraph


def graph(**parents):
    roles = RoleGraph()
    for name, parent in parents.items():
        roles.add(name, parent)
    return roles


def test_expand_follows_inheritance():
    roles = graph(viewer=None, editor="viewer", admin="editor", guest=None)
    assert roles.expand(["admin"]) == {"admin", "editor", "viewer"}
    assert roles.expand(["guest", "nobody"]) == {"guest"}


def test_ancestors_are_nearest_first():
    assert graph(viewer=None, editor="viewer", admin="editor").ancestors("admin") == ["admin", "editor", "viewer"]


def test_unknown_parent():
    with pytest.raises(RoleError, match="unknown role: ghost"):
        graph(editor="ghost").check()


def test_cycle_is_reported_in_order():
    with pytest.raises(RoleError) as caught:
        graph(a="b", b="c", c="a").check()
    assert str(caught.value) == "role cycle: a -> b -> c -> a"


def test_chain_limit():
    names = [f"r{i}" for i in range(MAX_CHAIN + 1)]
    roles = graph(**{name: (names[i - 1] if i else None) for i, name in enumerate(names)})
    with pytest.raises(RoleError, match=f"longer than {MAX_CHAIN} roles"):
        roles.check()


def test_duplicate_and_bad_names():
    roles = graph(viewer=None)
    with pytest.raises(RoleError, match="role viewer is defined twice"):
        roles.add("viewer")
    with pytest.raises(RoleError, match="bad role name: 9lives"):
        roles.add("9lives")
