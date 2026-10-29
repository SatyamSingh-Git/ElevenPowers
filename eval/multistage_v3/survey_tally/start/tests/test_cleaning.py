from surveytally.model.responses import Response
from surveytally.services.cleaning import clean, latest_per_respondent


def test_latest_submission_wins():
    old = Response('R1', {'region': 'north'}, '2026-03-01')
    new = Response('R1', {'region': 'south'}, '2026-03-04')
    other = Response('R2', {'region': 'east'}, '2026-03-02')
    kept, duplicates = latest_per_respondent([new, other, old])
    assert kept == [new, other]
    assert duplicates == [old]


def test_later_in_the_file_wins_on_equal_dates():
    first, second = Response('R1', {'region': 'north'}), Response('R1', {'region': 'west'})
    kept, _ = latest_per_respondent([first, second])
    assert kept == [second]


def test_speeders_are_dropped_after_merging():
    existing = [Response('R1', {}, '2026-03-01', 400)]
    incoming = [Response('R1', {}, '2026-03-02', 30), Response('R2', {}, '2026-03-02', 500)]
    cleaned = clean(incoming, min_seconds=60, existing=existing)
    assert [response.respondent for response in cleaned.kept] == ['R2']
    assert [response.duration for response in cleaned.speeders] == [30]
    assert len(cleaned.duplicates) == 1
