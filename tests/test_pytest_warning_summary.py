"""Real quiet pytest output must survive warning and failure headings."""
import pytest
from core.evidence import Kind, SourceScan
from core.parsers import parse


@pytest.mark.parametrize('summary,code,passed,failed', [
    ('399 passed, 107 warnings in 4.00s',0,399,0),
    ('1 failed, 2 passed, 1 warning in 0.14s',1,2,1),
    ('================ 2 passed, 1 warning in 0.14s ================',0,2,0),
    ('================ 2 errors in 0.14s ================',2,0,2),
])
def test_warning_heading_cannot_mask_real_final_counts(tmp_path,summary,code,passed,failed):
    output='============================== warnings summary ===============================\nwarning detail\n'+summary+'\n'
    suite=[r for r in parse('python -m pytest tests -q',output,code,tmp_path,
           snapshot=(SourceScan(),'')) if r.kind is Kind.SUITE][0]
    assert (suite.passed,suite.failed)==(passed,failed)


def test_heading_without_execution_never_counts_as_tests(tmp_path):
    suite=[r for r in parse('python -m pytest tests -q',
        '============================== warnings summary ===============================\n',0,tmp_path,
        snapshot=(SourceScan(),'')) if r.kind is Kind.SUITE][0]
    assert suite.passed==0 and suite.failed==0
