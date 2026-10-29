"""Checking responses against the questionnaire they answer."""
from ..model.errors import Issue


class Validator:
    def __init__(self, survey):
        self.survey = survey

    def check(self, response):
        """Every problem with one response, in questionnaire order."""
        issues = []
        for question_id in response.answers:
            if not self.survey.has_question(question_id):
                issues.append(Issue(response.respondent, question_id, f'{question_id}: not a question in {self.survey.id}'))
        for question in self.survey.questions:
            value = response.answers.get(question.id)
            if value is None:
                if question.required:
                    issues.append(Issue(response.respondent, question.id, f'{question.id}: answer required'))
                continue
            message = getattr(self, f'_check_{question.type}')(question, value)
            if message:
                issues.append(Issue(response.respondent, question.id, message))
        return issues

    def _check_single(self, question, value):
        if not question.has_option(value):
            return f'{question.id}: unknown option {value}'
        return None

    def _check_multi(self, question, value):
        for code in value:
            if not question.has_option(code):
                return f'{question.id}: unknown option {code}'
        if len(set(value)) < len(value):
            return f'{question.id}: an option is chosen twice'
        if question.max_choices is not None and len(value) > question.max_choices:
            return f'{question.id}: more than {question.max_choices} options chosen'
        return None

    def _check_scale(self, question, value):
        if not question.low <= value <= question.high:
            return f'{question.id}: {value} is outside {question.low}..{question.high}'
        return None

    def _check_text(self, question, value):
        if len(value) > question.max_length:
            return f'{question.id}: answer longer than {question.max_length} characters'
        return None


def validate(survey, responses):
    """The responses without problems, and the problems found in the rest."""
    validator = Validator(survey)
    valid, issues = [], []
    for response in responses:
        found = validator.check(response)
        if found:
            issues.extend(found)
        else:
            valid.append(response)
    return valid, issues
