"""Native host launcher: ep_host.py PLATFORM EVENT, JSON on stdin/stdout."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.hosts.bridge import run
from core.hosts.readiness import ingress
from core.milestones.delivery import collect, emitted


def main() -> int:
    try:
        if len(sys.argv) not in {3, 4} or (len(sys.argv) == 4 and sys.argv[3] != '--replay'):
            raise ValueError("usage: ep_host.py PLATFORM EVENT")
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("hook input must be a JSON object")
        with ingress('replay' if len(sys.argv) == 4 else 'host'), collect():
            response, code = run(sys.argv[1], sys.argv[2], payload)
            print(json.dumps(response), flush=True)
            emitted(response)
        return code
    except (ValueError, OSError) as exc:
        print(f"ElevenPowers host event not processed: {exc}", file=sys.stderr)
        print("{}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
