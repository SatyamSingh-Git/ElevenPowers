"""A stand-in reviewer reads each case's 50 proposals at stage 0 and keeps the pairs it would certify: one
tool-free Sonnet 5.5 turn per case, blind to every stage, run once, used verbatim.

Usage: review.py <new scratch dir>. Writes reviewed.json and reviewer.jsonl next to this file."""
import ast
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'results' / 'rule-groups-described'))
from core.milestones.propose import propose  # noqa: E402
from describe import tool_free  # noqa: E402
from eval.multistage_cases import load, tree  # noqa: E402
from eval.rule_groups_run import certify  # noqa: E402

LIMIT, MAX_LINES = 50, 60
PROMPT = '''You maintain this project and are reviewing a code tool's proposals. Each proposal is two functions in \
different files that share rare words, which may mean they keep the same rule, so that a change to one needs the same \
change in the other. Certify only the pairs you judge really do keep one rule. Certified pairs become declared rules: \
whenever an AI coding agent edits one of the files, it is reminded of the other.

{proposals}

Reply with a JSON array of the numbers of the proposals you certify, for example [2, 7]. Reply with the array only.'''


def source(root, path, name):
    text = (root / path).read_text(encoding='utf-8')
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            lines = text.splitlines()[node.lineno - 1:node.end_lineno]
            return '\n'.join(lines[:MAX_LINES] + ([f'    ... ({len(lines) - MAX_LINES} more lines)'] if len(lines) > MAX_LINES else []))
    return f'(function {name} not found)'


def block(number, p, root):
    (a, b), (fa, fb) = p['files'], p['functions']
    return (f"#{number}: {a} :: {fa}  <->  {b} :: {fb}\nshared words: {', '.join(p['shared'])}\n"
            f"--- {a} ---\n{source(root, a, fa)}\n--- {b} ---\n{source(root, b, fb)}")


def accepted(reply, count):
    found = re.findall(r'\[[\d,\s]*\]', reply)
    if not found:
        return None
    numbers = json.loads(found[-1])
    return sorted(set(numbers)) if all(isinstance(n, int) and 1 <= n <= count for n in numbers) else None


def main():
    scratch = Path(sys.argv[1]).resolve()
    rows, log = [], []
    for folder in sorted(p for p in (ROOT / 'eval' / 'multistage_v3').iterdir() if (p / 'case.json').exists()):
        case = load(folder)
        certified = {e['id'] for e in certify(case, scratch / case['id'] / 'certify')}
        start = tree(case, 0, scratch / case['id'] / 'start')
        subprocess.run(['git', 'init', '-q'], cwd=start, check=True)
        subprocess.run(['git', 'add', '-A'], cwd=start, check=True, capture_output=True)
        proposals = propose(start, limit=LIMIT)['proposals']
        prompt = PROMPT.format(proposals='\n\n'.join(block(i, p, start) for i, p in enumerate(proposals, 1)))
        empty = scratch / case['id'] / 'reviewer'
        empty.mkdir(parents=True)
        # On stdin: about 53k characters, past Windows' 32,767-character command line (WinError 206).
        args = tool_free('')
        done = subprocess.run(args[:2] + args[3:], input=prompt, cwd=empty, capture_output=True, text=True,
                              encoding='utf-8', timeout=600)
        events = [json.loads(line) for line in done.stdout.splitlines() if line.strip().startswith('{')]
        init = next((e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init'), {})
        result = next((e for e in events if e.get('type') == 'result'), {})
        kept = accepted(result.get('result') or '', len(proposals))
        ids = [proposals[n - 1]['entry']['id'] for n in kept or []]
        rows.append({'case': case['id'], 'proposals': len(proposals), 'parsed': kept is not None, 'kept': ids,
                     'certified': sorted(certified), 'certified_kept': sorted(certified & set(ids))})
        log.append({'case': case['id'], 'tools': init.get('tools'), 'model': init.get('model'), 'prompt_chars': len(prompt),
                    'reply': result.get('result'), 'cost': result.get('total_cost_usd'), 'exit': done.returncode})
        print(json.dumps({**{k: rows[-1][k] for k in ('case', 'parsed')}, 'kept': len(ids),
                          'certified_kept': f"{len(rows[-1]['certified_kept'])} of {len(certified)}",
                          'tools': init.get('tools'), 'cost': result.get('total_cost_usd')}), flush=True)
    Path(__file__).with_name('reviewed.json').write_text(json.dumps(rows, indent=1), encoding='utf-8')
    Path(__file__).with_name('reviewer.jsonl').write_text('\n'.join(json.dumps(x) for x in log) + '\n', encoding='utf-8')
    recall = sum(len(r['certified_kept']) for r in rows)
    print(f"recall {recall} of {sum(len(r['certified']) for r in rows)}; kept per case "
          f"{[len(r['kept']) for r in rows]}; cost ${sum(x['cost'] or 0 for x in log):.2f}")


if __name__ == '__main__':
    main()
