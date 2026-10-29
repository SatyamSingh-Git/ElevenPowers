from surveytally.model.responses import Response
from surveytally.services.validation import validate


def messages(survey, answers):
    _, issues = validate(survey, [Response('R1', answers)])
    return [issue.message for issue in issues]


def test_valid_answers_pass(customer_survey):
    answers = {'contact': 'post', 'channels': ('web', 'store'), 'ease': 5, 'recommend': 0, 'comments': 'ok'}
    assert messages(customer_survey, answers) == []


def test_unknown_options(customer_survey):
    assert messages(customer_survey, {'contact': 'fax'}) == ['contact: unknown option fax']
    assert messages(customer_survey, {'channels': ('web', 'fax')}) == ['channels: unknown option fax']


def test_scale_range(customer_survey):
    assert messages(customer_survey, {'ease': 6}) == ['ease: 6 is outside 1..5']
    assert messages(customer_survey, {'recommend': 11}) == ['recommend: 11 is outside 0..10']


def test_free_text_limit(customer_survey):
    assert messages(customer_survey, {'comments': 'x' * 500}) == []
    assert messages(customer_survey, {'comments': 'x' * 501}) == ['comments: answer longer than 500 characters']


def test_required_questions(poll_survey):
    poll_survey.question('region').required = True
    assert messages(poll_survey, {'contact': 'email'}) == ['region: answer required']


def test_invalid_responses_are_kept_apart(poll_survey):
    good, bad = Response('R1', {'region': 'north'}), Response('R2', {'region': 'mars'})
    valid, issues = validate(poll_survey, [good, bad])
    assert valid == [good]
    assert [str(issue) for issue in issues] == ['R2: region: unknown option mars']
