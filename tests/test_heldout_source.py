"""Repository selection follows the frozen rule on metadata shaped like real PyPI responses."""
import pytest

WHEEL = [{"packagetype": "bdist_wheel", "filename": "pkg-1.0-py3-none-any.whl"}]
COMPILED = [{"packagetype": "bdist_wheel", "filename": "pkg-1.0-cp312-cp312-manylinux_2_17_x86_64.whl"},
            {"packagetype": "sdist", "filename": "pkg-1.0.tar.gz"}]


def meta(*, expression=None, license="", classifiers=(), urls=None, files=WHEEL):
    return {"info": {"license_expression": expression, "license": license, "classifiers": list(classifiers),
                     "project_urls": urls if urls is not None else {"Source": "https://github.com/owner/pkg"}},
            "urls": files}


METADATA = {
    "good": meta(expression="MIT"),
    "dual": meta(license="Dual License", classifiers=["License :: OSI Approved :: Apache Software License"],
                 urls={"Homepage": "https://github.com/dateutil/dateutil"}),
    "issues-only": meta(license="MIT", urls={"Bug Tracker": "https://github.com/yaml/pkg/issues"}),
    "nogit": meta(expression="MIT", urls={"Homepage": "https://example.org/pkg"}),
    "compiled": meta(expression="BSD-3-Clause", files=COMPILED),
    "gpl": meta(license="GPL-3.0-or-later", classifiers=["License :: OSI Approved :: GNU General Public License v3 (GPLv3)"]),
    "mpl": meta(license="MPL-2.0", classifiers=["License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)"]),
    "compound": meta(expression="BSD-3-Clause AND CC0-1.0"),
    "click": meta(expression="BSD-3-Clause"),
}
RANKING = {"rows": [{"project": name, "download_count": 100 - i} for i, name in
                    enumerate(["good", "dual", "issues-only", "nogit", "compiled", "gpl", "mpl", "compound", "click", "missing"])]}


def rows(limit=10):
    from eval.heldout_source import select
    return select(RANKING, METADATA.get, limit=limit, exclude={"click"})


def test_accepted_repositories_follow_rank_order_and_normalise_to_owner_and_name():
    accepted = [(r["project"], r["repo"]) for r in rows() if r["verdict"] == "accepted"]
    assert accepted == [("good", "https://github.com/owner/pkg"),
                        ("dual", "https://github.com/dateutil/dateutil"),
                        ("issues-only", "https://github.com/yaml/pkg")]


@pytest.mark.parametrize("project, reason", [
    ("nogit", "no GitHub source"), ("compiled", "not pure Python"), ("gpl", "licence not permissive"),
    ("mpl", "licence not permissive"), ("compound", "licence not permissive"), ("click", "excluded"),
    ("missing", "metadata unavailable"),
])
def test_each_rejection_keeps_its_reason(project, reason):
    (row,) = [r for r in rows() if r["project"] == project]
    assert (row["verdict"], row["reason"]) == ("rejected", reason)


def test_limit_counts_ranked_projects_not_accepted_ones():
    assert [r["rank"] for r in rows(limit=4)] == [1, 2, 3, 4]


@pytest.mark.parametrize("found, accepted", [
    (meta(classifiers=["License :: OSI Approved :: MIT License",
                       "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"]), True),
    (meta(expression="MIT OR GPL-3.0-only"), True),
    (meta(expression="MIT AND GPL-3.0-only"), False),
    (meta(expression="(Apache-2.0 OR MIT) AND BSD-3-Clause"), True),
])
def test_a_dual_licence_is_usable_under_its_permissive_option(found, accepted):
    from eval.heldout_source import select
    (row,) = select({"rows": [{"project": "p"}]}, {"p": found}.get, limit=1, exclude=set())
    assert (row["verdict"] == "accepted") is accepted


@pytest.mark.parametrize("urls, repo", [
    ({"Funding": "https://github.com/sponsors/Kludex", "Source": "https://github.com/Kludex/starlette"},
     "https://github.com/Kludex/starlette"),
    ({"Funding": "https://github.com/sponsors/Kludex"}, ""),
])
def test_a_sponsor_page_is_not_a_repository(urls, repo):
    from eval.heldout_source import _repo
    assert _repo({"project_urls": urls}) == repo
