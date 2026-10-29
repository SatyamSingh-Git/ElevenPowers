"""A plain-text overview of a survey's results: one line per question, then the scores."""
from .formatting import MEAN_DECIMALS, format_number, format_percent, format_score


def summary(results, decimals=1):
    survey = results.survey
    count = f'Responses: {results.responses}'
    if results.weighted:
        count += ' (weighted)'
    lines = [survey.title, '=' * len(survey.title), count, '']
    for question in survey.questions:
        lines.append(f'{question.id}  {_headline(results.tables[question.id], decimals)}')
    if results.scores:
        lines += ['', 'Scores']
        for result in results.scores.values():
            lines.append(f'  {result.title}: {format_score(result.mean, result.rule, decimals)} (n={result.base})')
    return '\n'.join(lines) + '\n'


def _headline(table, decimals):
    if not table.base:
        return 'no answers'
    if table.mean is not None:
        return f'mean {format_number(table.mean, MEAN_DECIMALS)} (n={table.base})'
    if not table.rows:
        return f'{table.base} answers'
    top = table.rows[0]
    return f'most chosen: {top.label} ({format_percent(top.percent, decimals)}%, n={table.base})'
