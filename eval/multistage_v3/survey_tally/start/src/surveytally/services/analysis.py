"""Everything a report needs about one set of responses, computed in one pass."""
from dataclasses import dataclass

from .scoring import compute_scores
from .tally import frequencies


@dataclass
class Results:
    survey: object
    responses: int
    weighted: bool
    tables: dict
    scores: dict


def analyse(survey, responses, weights=None):
    return Results(
        survey=survey,
        responses=len(responses),
        weighted=weights is not None,
        tables=frequencies(survey, responses, weights),
        scores=compute_scores(survey, responses, weights),
    )
