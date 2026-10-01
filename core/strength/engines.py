"""Optional engine boundaries; only metadata crosses into durable records."""
from dataclasses import dataclass
import json
from pathlib import Path
import tempfile
from .execution import execute
from .model import Observation


@dataclass(frozen=True)
class Candidate:
    id: str
    path: str
    line: int
    operator: str
    content: str

    def __post_init__(self):
        Observation(self.id, self.path, self.line, self.operator, 'not_run')
        if not isinstance(self.content, str) or len(self.content.encode('utf-8')) > 2 * 1024 * 1024:
            raise ValueError('invalid or oversized mutation source')


class Candidates(list):
    more = False


def generate(root, paths, command, budget):
    maximum = budget.maximum - budget.attempts
    if maximum <= 0:
        raise ValueError('mutation attempt budget exhausted')
    with tempfile.TemporaryDirectory(prefix='ep-engine-') as directory:
        request = Path(directory) / 'request.json'
        request.write_text(json.dumps({'paths': paths, 'maximum': maximum}), encoding='utf-8')
        result = execute([*command, str(request)], root, budget, 30, shell=False)
    if result.status != 'complete' or result.returncode:
        raise ValueError('optional mutation engine unavailable or producer incomplete (' + result.status + ')')
    try:
        data = json.loads(result.stdout)
        if not isinstance(data['version'], str) or len(data['version']) > 32 or type(data['more']) is not bool:
            raise ValueError('invalid engine metadata')
        items = Candidates(Candidate(**item) for item in data['candidates'])
        if len(items) > maximum or any(item.path not in paths for item in items):
            raise ValueError('engine exceeded selected scope or attempt count')
        items.more = data['more']
        return items, data['version']
    except (ValueError, TypeError, KeyError):
        raise ValueError('mutation engine returned invalid or incomplete output') from None


def cosmic(root, paths, python, budget):
    return generate(root, paths, [python, str(Path(__file__).with_name('cosmic_worker.py'))], budget)
