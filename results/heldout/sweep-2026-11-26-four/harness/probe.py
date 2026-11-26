"""Does the instructed arm's CLAUDE.md reach the agent through the study's launcher? Asked both ways.

The init event lists no memory files, so delivery is asked: a workspace with the file must quote
it, one without must answer NONE. Usage: python probe.py OUT_DIR
"""
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, 'E:/ElevenPowers')
from eval import subscription
from eval.heldout_run import _tool_calls
from eval.plugins import INSTRUCTION, TOOLS

QUESTION = ("Quote this project's own instructions to you word for word, from any CLAUDE.md you were given. "
            "If you were given none, answer exactly NONE. Do not use any tools.")
out = Path(sys.argv[1])
results = {}
for name, memory in (('with', True), ('without', False)):
    work = out / name
    work.mkdir(parents=True, exist_ok=True)
    if memory:
        (work / 'CLAUDE.md').write_text(INSTRUCTION + '\n', encoding='utf-8')
    subprocess.run(['git', 'init', '-q'], cwd=work, check=True)
    command = subscription.command('claude', 'claude', work, QUESTION, model='claude-sonnet-5-5')
    command[command.index('--tools') + 1] = TOOLS
    done = subprocess.run(command, cwd=work, capture_output=True, text=True, encoding='utf-8', errors='replace',
                          timeout=300)
    (out / f'{name}.json').write_text(done.stdout, encoding='utf-8')
    result = json.loads(done.stdout)
    reply = result.get('result', '')
    results[name] = {'quoted': INSTRUCTION in reply, 'none': reply.strip().strip('.') == 'NONE',
                     'cost': result.get('total_cost_usd'), 'models': list(result.get('modelUsage', {})),
                     'reply': reply[:300]}
print(json.dumps(results, indent=2))
qualified = results['with']['quoted'] and results['without']['none'] and not results['without']['quoted']
print('delivery qualified' if qualified else 'delivery NOT qualified')
sys.exit(0 if qualified else 1)
