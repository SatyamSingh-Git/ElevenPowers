"""A stand-in reviewer describes each certified rule from the two files alone: one Sonnet 5.5 turn per rule,
no tools, in a folder holding only those files, blind to every stage request. Run once; used verbatim.

Usage: describe.py <case> <new scratch dir>. Writes descriptions.json and describer.jsonl next to this file."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from core.milestones.propose import propose  # noqa: E402
from core.process import run  # noqa: E402
from eval import subscription  # noqa: E402
from eval.multistage_cases import load, tree  # noqa: E402
from eval.rule_groups_run import certify  # noqa: E402

MODEL = 'claude-sonnet-5-5'
PROMPT = '''You are reviewing a proposal from a code tool. It noticed that two functions in this project share rare \
words and may keep the same rule, so that changing one may need the same change in the other. You accept it. Your \
description goes into the project's declarations file, and an AI coding agent is shown it whenever it changes either file.

Proposal: {a_function} in {a} and {b_function} in {b}; shared words: {shared}.

=== {a} ===
{a_text}
=== {b} ===
{b_text}

Write the description: one sentence of at most 200 characters that states the rule both functions keep, specific \
enough that someone changing either file knows what must stay consistent. Reply with the sentence only.'''


def tool_free(prompt):
    args = subscription.command('claude', 'claude', Path.cwd(), prompt, model=MODEL)
    args[args.index('--output-format') + 1] = 'stream-json'
    return args[:args.index('--tools')] + ['--tools', '', '--verbose']


def main():
    name, scratch = sys.argv[1], Path(sys.argv[2]).resolve()
    case = load(ROOT / 'eval' / 'multistage_v3' / name)
    certified = {e['id'] for e in certify(case, scratch / 'certify')}
    start = tree(case, 0, scratch / 'start')
    subprocess.run(['git', 'init', '-q'], cwd=start, check=True)
    subprocess.run(['git', 'add', '-A'], cwd=start, check=True, capture_output=True)
    proposals = [p for p in propose(start, limit=50)['proposals'] if p['entry']['id'] in certified]
    assert {p['entry']['id'] for p in proposals} == certified
    descriptions, log = {}, []
    for p in proposals:
        rule = p['entry']['id']
        (a, b), (fa, fb) = p['files'], p['functions']
        prompt = PROMPT.format(a=a, b=b, a_function=fa, b_function=fb, shared=', '.join(p['shared']),
                               a_text=(start / a).read_text(encoding='utf-8'), b_text=(start / b).read_text(encoding='utf-8'))
        folder = scratch / rule
        for path in (a, b):
            (folder / path).parent.mkdir(parents=True, exist_ok=True)
            (folder / path).write_bytes((start / path).read_bytes())
        done = run(tool_free(prompt), cwd=folder, timeout=300, shell=False)
        events = [json.loads(line) for line in done.stdout.splitlines() if line.strip().startswith('{')]
        init = next(e for e in events if e.get('type') == 'system' and e.get('subtype') == 'init')
        result = next(e for e in events if e.get('type') == 'result')
        descriptions[rule] = ' '.join(result['result'].split())
        log.append({'rule': rule, 'prompt': prompt, 'tools': init.get('tools'), 'model': init.get('model'),
                    'reply': result['result'], 'cost': result.get('total_cost_usd')})
        print(json.dumps({k: log[-1][k] for k in ('rule', 'tools', 'model', 'reply', 'cost')}), flush=True)
    Path(__file__).with_name('descriptions.json').write_text(json.dumps({name: descriptions}, indent=1), encoding='utf-8')
    Path(__file__).with_name('describer.jsonl').write_text('\n'.join(json.dumps(x) for x in log) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
