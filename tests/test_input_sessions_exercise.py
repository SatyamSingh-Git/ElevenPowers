"""The published ordinary-session exercise runs actual unrelated producers."""
def test_actual_session_fault_recovery_and_readonly_protocol(tmp_path):
    from eval.input_sessions import exercise
    result=exercise(tmp_path/'sessions')
    assert result['kind']=='external_input_sessions'
    assert len(result['cases'])==2
    for case in result['cases']:
        assert case['hosts']==['claude','codex','gemini','cursor','copilot']
        assert case['states']==['CURRENT','STALE','FAILED','CURRENT','INCOMPLETE','INCOMPLETE','CURRENT']
        assert case['counts']==[5,5,6,6,7,8,8,8,9,10,10]
        assert case['readonly'] and case['report_reads']==2
    assert result['runtime_fingerprint'] and result['limits']
