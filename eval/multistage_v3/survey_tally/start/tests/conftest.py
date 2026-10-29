import pytest

from surveytally.files.survey_file import survey_from_dict

CUSTOMER = {
    'id': 'customer-2026',
    'title': 'Customer survey 2026',
    'questions': [
        {'id': 'contact', 'type': 'single', 'text': 'How should we contact you?',
         'options': [{'code': 'phone', 'label': 'Phone'}, {'code': 'email', 'label': 'Email'},
                     {'code': 'post', 'label': 'Post'}]},
        {'id': 'channels', 'type': 'multi', 'text': 'Which channels have you used?',
         'options': ['web', 'app', 'phone', 'store']},
        {'id': 'satisfaction', 'type': 'scale', 'text': 'I am satisfied with the service', 'preset': 'agree5'},
        {'id': 'ease', 'type': 'scale', 'text': 'How easy was it?', 'low': 1, 'high': 5},
        {'id': 'recommend', 'type': 'scale', 'text': 'Would you recommend us?', 'preset': 'likely11'},
        {'id': 'comments', 'type': 'text', 'text': 'Anything else?'},
    ],
    'scores': [
        {'name': 'overall', 'rule': 'mean', 'items': ['satisfaction', 'ease'], 'label': 'Overall'},
        {'name': 'happy', 'rule': 'top_box', 'items': ['satisfaction', 'ease']},
        {'name': 'nps', 'rule': 'nps', 'items': ['recommend'], 'label': 'NPS'},
    ],
}

POLL = {
    'id': 'poll',
    'title': 'Quick poll',
    'questions': [
        {'id': 'region', 'type': 'single', 'text': 'Region', 'options': ['north', 'south', 'east', 'west']},
        {'id': 'contact', 'type': 'single', 'text': 'Preferred contact',
         'options': [{'code': 'phone', 'label': 'Phone'}, {'code': 'email', 'label': 'Email'}]},
        {'id': 'channels', 'type': 'multi', 'text': 'Channels used', 'options': ['web', 'app', 'store']},
        {'id': 'comments', 'type': 'text', 'text': 'Comments'},
    ],
}


@pytest.fixture
def customer_survey():
    return survey_from_dict(CUSTOMER)


@pytest.fixture
def poll_survey():
    return survey_from_dict(POLL)


@pytest.fixture
def write_file(tmp_path):
    def write(name, text):
        path = tmp_path / name
        path.write_text(text, encoding='utf-8')
        return path
    return write
