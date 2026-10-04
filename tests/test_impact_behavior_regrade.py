import copy
import hashlib

from eval.impact_behavior_regrade import regrade


def sample(root):
    directory=root/'case'; directory.mkdir()
    runs={}
    for label, code, message in [('unchanged',0,''),('equivalent',0,''),('fault',1,'assert 1 == 2')]:
        body='<testcase name="one">'+(f'<failure message="{message}"/>' if message else '')+'</testcase>'
        data=('<testsuite>'+body+'</testsuite>').encode()
        (directory/(label+'.xml')).write_bytes(data)
        (directory/(label+'.txt')).write_text('producer output')
        runs[label]={'status':'incomplete','exit_code':code,'producer':'pytest','report':label+'.xml',
            'report_sha256':hashlib.sha256(data).hexdigest(),
            'output_sha256':hashlib.sha256(b'producer output').hexdigest()}
    return {'controller':{'version':'old'},'experiments':[{'id':'case','runs':runs,
        'selected_fault':{'final':{**runs['fault'],'after_seal':{'complete':True}}},
        'seals':{v:{'before':{'complete':True},'after':{'complete':True}} for v in runs}}]}


def test_saved_producer_regrade_preserves_identity_without_execution(tmp_path):
    result=sample(tmp_path); original=copy.deepcopy(result)
    revised=regrade(result,tmp_path)
    assert result==original
    assert revised['controller']=={'version':'old'}
    assert revised['qualified']==1 and revised['detected']=={'final':1}
    assert revised['experiments'][0]['original_runs']['fault']['status']=='incomplete'


def test_changed_reports_output_and_failed_seals_cannot_qualify(tmp_path):
    result=sample(tmp_path)
    (tmp_path/'case/fault.xml').write_text('<testsuite><testcase/></testsuite>')
    assert regrade(result,tmp_path)['qualified']==0
    result['experiments'][0]['runs']['fault']['report']='../fault.xml'
    assert regrade(result,tmp_path)['qualified']==0
    result['experiments'][0]['runs']['unchanged']['output_sha256']='a'*64
    revised=regrade(result,tmp_path)
    assert revised['experiments'][0]['runs']['unchanged']['status']=='incomplete'


def test_saved_source_seal_gaps_remain_unqualified(tmp_path):
    result=sample(tmp_path)
    result['experiments'][0]['seals']['equivalent']['after']['complete']=False
    assert regrade(result,tmp_path)['qualified']==0
