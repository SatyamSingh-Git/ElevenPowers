"""Independent machine outcomes cannot be inferred from a passing summary."""
import json
import pytest
from eval.impact_behavior import classify, qualification


def junit(body):
    return ('<testsuites><testsuite>'+body+'</testsuite></testsuites>').encode()


def test_junit_pass_assertion_and_setup_failure_are_distinct():
    assert classify(0,junit('<testcase name="one"/>'),'pytest')['status']=='pass'
    failed=classify(1,junit('<testcase name="one"><failure message="AssertionError">assert 1 == 2</failure></testcase>'),'pytest')
    assert failed['status']=='assertion-fail' and failed['failed']==1
    setup=classify(1,junit('<testcase name="one"><error>ImportError</error></testcase>'),'pytest')
    assert setup['status']=='incomplete'
    assert classify(0,junit(''),'pytest')['status']=='incomplete'
    assert classify(0,junit('<testcase><failure>AssertionError</failure></testcase>'),'pytest')['status']=='incomplete'


def test_jest_counts_match_actual_assertions_and_exit():
    value={'numPassedTests':1,'numFailedTests':0,'numPendingTests':0,'testResults':[
        {'assertionResults':[{'status':'passed','fullName':'works'}]}]}
    assert classify(0,json.dumps(value).encode(),'jest')['status']=='pass'
    value['numPassedTests']=500
    assert classify(0,json.dumps(value).encode(),'jest')['status']=='incomplete'
    value.update(numPassedTests=0,numFailedTests=1)
    value['testResults'][0]['assertionResults'][0].update(status='failed',failureMessages=['Cannot find module'])
    assert classify(1,json.dumps(value).encode(),'jest')['status']=='incomplete'
    value['testResults'][0]['assertionResults'][0]['failureMessages']=['expect(received).toEqual(expected)\nExpected: 1\nReceived: 2']
    value['testResults'][0]['assertionResults'][0]['failureDetails']=[{'matcherResult':{'name':'toEqual','pass':False}}]
    assert classify(1,json.dumps(value).encode(),'jest')['status']=='assertion-fail'


def test_only_independently_qualified_faults_enter_detection_denominator():
    runs={'unchanged':{'status':'pass'},'equivalent':{'status':'pass'},'fault':{'status':'assertion-fail'}}
    assert qualification(runs)
    for missing in runs:
        assert not qualification({k:v for k,v in runs.items() if k!=missing})
    runs['equivalent']['status']='incomplete'
    assert not qualification(runs)


def test_junit_declared_errors_and_counts_cannot_be_ignored():
    value=b'<testsuites><testsuite tests="2" errors="1" failures="0" skipped="0"><testcase name="one"/></testsuite></testsuites>'
    assert classify(0,value,'pytest')['status']=='incomplete'


def test_runtime_error_mentioning_assertion_or_matcher_is_not_an_assertion_result():
    value=junit('<testcase><failure message="ValueError: expected AssertionError from callback">raise ValueError("AssertionError")</failure></testcase>')
    assert classify(1,value,'pytest')['status']=='incomplete'
    report={'numPassedTests':0,'numFailedTests':1,'numPendingTests':0,'testResults':[
        {'assertionResults':[{'status':'failed','fullName':'runtime error',
            'failureMessages':['TypeError: expect(value) could not initialize'],'failureDetails':[{}]}]}]}
    assert classify(1,json.dumps(report).encode(),'jest')['status']=='incomplete'


def test_actual_pytest_runtime_error_is_not_a_qualified_fault(tmp_path):
    import os
    from eval.impact_behavior import execute
    root=tmp_path/'project';root.mkdir()
    reports=tmp_path/'reports';reports.mkdir()
    (root/'test_runtime.py').write_text('def test_runtime():\n    raise ValueError("expected AssertionError from callback")\n',encoding='utf-8')
    result=execute(root,['test_runtime.py'],'pytest',None,reports,'actual',dict(os.environ))
    assert result['status']=='incomplete'
    assert result['exit_code']==1 and result['failed']==1
