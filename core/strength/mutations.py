"""Apply engine mutations only inside the private copy; restore on every path."""
import io
import tokenize
from .baseline import outcomes
from .execution import execute
from .isolation import safe_file
from .model import Observation


def run_candidate(candidate, copied, command, budget, seconds, *, original=None):
    status = 'not_run'
    try:
        budget.attempt()
    except TimeoutError:
        return Observation(candidate.id, candidate.path, candidate.line, candidate.operator, status)
    target = safe_file(copied, candidate.path)
    source_bytes = target.read_bytes()
    try:
        encoding = 'utf-8'
        if target.suffix == '.py':
            encoding, _ = tokenize.detect_encoding(io.BytesIO(source_bytes).readline)
            try:
                compile(candidate.content, candidate.path, 'exec')
            except (SyntaxError, ValueError):
                return Observation(candidate.id, candidate.path, candidate.line, candidate.operator, 'invalid')
        target.write_bytes(candidate.content.encode(encoding))
        execution = execute(command, copied, budget, seconds, original=original)
        if execution.status != 'complete':
            status = 'error' if execution.status == 'isolation_error' else execution.status
        else:
            passed, failed, errors = outcomes(command, execution, copied)
            if errors:
                status = 'invalid'
            elif execution.returncode == 0 and passed > 0 and failed == 0:
                status = 'undetected'
            elif execution.returncode and failed > 0:
                status = 'detected'
            else:
                status = 'error'
    except (OSError, UnicodeError, ValueError):
        status = 'error'
    finally:
        # Source restoration is private. A failure propagates so no later mutation
        # can accidentally run on a prior mutation's source.
        target.write_bytes(source_bytes)
    return Observation(candidate.id, candidate.path, candidate.line, candidate.operator, status)
