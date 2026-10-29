"""Quality flags, open-end coding, codebooks and fieldwork progress."""
import csv

from surveytally.model.responses import Response
from surveytally.reports.codebook import codebook_rows, write_codebook
from surveytally.reports.progress import daily_counts, quota_cells
from surveytally.services.coding import code_answers, read_codeframe
from surveytally.services.quality import item_nonresponse, quality_flags, straightliners


def test_straightliners_and_skippers(customer_survey):
    responses = [
        Response('R1', {'satisfaction': 3, 'ease': 3, 'recommend': 3, 'contact': 'email'}),
        Response('R2', {'satisfaction': 4, 'ease': 2, 'recommend': 9, 'contact': 'post', 'comments': 'ok'}),
    ]
    assert [str(flag) for flag in quality_flags(customer_survey, responses)] == []
    assert [str(flag) for flag in straightliners(customer_survey, responses, min_items=3)] == [
        'R1: gave 3 to all 3 scale questions']
    responses.append(Response('R3', {'contact': 'phone'}))
    assert [str(flag) for flag in quality_flags(customer_survey, responses)] == ['R3: skipped 5 of 6 questions']
    assert item_nonresponse(customer_survey, responses)['comments'] == 2 / 3


def test_codeframe_codes_answers(write_file, customer_survey):
    frame = write_file('frame.csv', (
        'code,label,keyword\n'
        'price,Price,price\nprice,Price,expensive\nstaff,Staff,staff\n'
    ))
    responses = [
        Response('R1', {'comments': 'Too expensive'}),
        Response('R2', {'comments': 'Friendly staff, fair price'}),
        Response('R3', {'comments': 'Nothing to add'}),
        Response('R4', {}),
    ]
    rows = code_answers(customer_survey, responses, 'comments', read_codeframe(frame))
    assert [(row.code, row.count) for row in rows] == [('price', 2), ('staff', 1), ('', 1)]
    assert rows[0].percent == 200 / 3


def test_codebook_lists_every_code(tmp_path, customer_survey):
    rows = codebook_rows(customer_survey)
    assert ['contact', 'single', 'email', 'Email'] in rows
    assert ['recommend', 'scale', '10', 'Extremely likely'] in rows
    assert ['comments', 'text', '', '(free text, up to 500 characters)'] in rows
    path = tmp_path / 'codebook.csv'
    write_codebook(customer_survey, path)
    with path.open(newline='', encoding='utf-8') as handle:
        assert next(csv.reader(handle)) == ['question', 'type', 'code', 'label']


def test_progress_by_day_and_quota():
    responses = [Response('R1', {'region': 'north'}, '2026-03-02'), Response('R2', {'region': 'north'}, '2026-03-01'),
                 Response('R3', {'region': 'south'}, '2026-03-02'), Response('R4', {'region': 'south'})]
    assert [(day.date, day.count, day.cumulative) for day in daily_counts(responses)] == [
        ('2026-03-01', 1, 1), ('2026-03-02', 2, 3), ('(no date)', 1, 4)]
    cells = quota_cells(responses, {'region': {'north': 0.25, 'south': 0.75}}, goal=8)
    assert [(cell.option, cell.quota, cell.achieved, cell.filled) for cell in cells] == [
        ('north', 2, 2, True), ('south', 6, 2, False)]
