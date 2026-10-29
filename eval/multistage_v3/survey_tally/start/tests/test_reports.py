from surveytally.model.responses import Response
from surveytally.reports.compare import compare, format_changes
from surveytally.reports.render import render_text
from surveytally.reports.summary import summary
from surveytally.reports.tables import Table
from surveytally.services.analysis import analyse


def test_summary_has_a_line_per_question(poll_survey):
    responses = [Response('R1', {'region': 'north', 'comments': 'Good'}), Response('R2', {'region': 'south'})]
    text = summary(analyse(poll_survey, responses))
    lines = text.splitlines()
    assert lines[:3] == ['Quick poll', '==========', 'Responses: 2']
    assert 'comments  1 answers' in lines
    assert 'contact  no answers' in lines


def test_weighted_summary_says_so(poll_survey):
    text = summary(analyse(poll_survey, [Response('R1', {'region': 'north'})], {'R1': 1.0}))
    assert 'Responses: 1 (weighted)' in text


def test_compare_reads_exported_tables(write_file):
    before = write_file('wave1.csv', (
        'question,option,count,percent\n'
        'region,north,20,40.0\nregion,south,30,60.0\nregion,(no answer),3,\n'
    ))
    after = write_file('wave2.csv', (
        'question,option,count,percent\n'
        'region,north,25,50.0\nregion,south,20,40.0\nregion,east,5,10.0\n'
    ))
    changes = {(change.question, change.option): change for change in compare(before, after)}
    assert changes[('region', 'north')].points == 10.0
    assert changes[('region', 'south')].points == -20.0
    assert changes[('region', 'east')].before is None
    assert ('region', '(no answer)') not in changes


def test_format_changes_hides_small_ones(write_file):
    before = write_file('wave1.csv', 'question,option,count,percent\nq,a,1,50.0\nq,b,1,50.0\n')
    after = write_file('wave2.csv', 'question,option,count,percent\nq,a,1,51.0\nq,b,1,49.0\n')
    assert format_changes(compare(before, after), threshold=2).splitlines() == ['question  option  before  after  change']


def test_text_tables_align_numbers():
    table = Table('T', ['Answer', 'Count'], [['Yes', '12'], ['No', '3']], ['Base: 15'])
    assert render_text(table).splitlines() == ['T', '-', 'Answer  Count', 'Yes        12', 'No          3', 'Base: 15']
