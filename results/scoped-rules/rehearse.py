"""$0 rehearsal: other agents' scoped rules through the real launchers. Usage: rehearse.py <new scratch dir>.

A scratch project carries all four formats. Through plugin/bin/ep_hook.py (Claude Code) and
plugin/bin/ep_host.py gemini, an edit of a matching file is briefed with the expected sources,
Claude is not handed its own `.claude/rules`, and a non-matching file gets no project rule."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
FILES = {
    '.claude/rules/api.md': '---\npaths:\n  - "src/api/**"\n---\nCLAUDE-RULE: validate every request body.\n',
    '.cursor/rules/api.mdc': '---\nglobs: src/api/**\nalwaysApply: false\n---\nCURSOR-RULE: use the shared client.\n',
    '.github/instructions/api.instructions.md': '---\napplyTo: "src/api/**/*.ts"\n---\nCOPILOT-RULE: keep handlers pure.\n',
    'src/api/AGENTS.md': 'AGENTS-RULE: never call the database from a handler.\n',
    'src/api/handler.ts': 'export {}\n',
    'lib/util.ts': 'export {}\n',
}


def project(folder):
    for name, text in FILES.items():
        (folder / name).parent.mkdir(parents=True, exist_ok=True)
        (folder / name).write_text(text, encoding='utf-8')
    subprocess.run(['git', 'init', '-q'], cwd=folder, check=True)
    return folder


def call(args, payload, folder):
    done = subprocess.run([sys.executable, *args], input=json.dumps(payload), capture_output=True, text=True,
                          cwd=ROOT, env={**os.environ, 'CLAUDE_PROJECT_DIR': str(folder)})
    return done.stdout


def brief(platform, folder, path):
    target = str(folder / path)
    if platform == 'claude':
        return call(['plugin/bin/ep_hook.py', 'PreToolUse'],
                    {'cwd': str(folder), 'tool_name': 'Edit', 'tool_input': {'file_path': target}}, folder)
    return call(['plugin/bin/ep_host.py', 'gemini', 'BeforeTool'],
                {'cwd': str(folder), 'session_id': 's', 'tool_name': 'replace',
                 'tool_input': {'file_path': target, 'old_string': 'a', 'new_string': 'b'}}, folder)


def main():
    scratch = Path(sys.argv[1]).resolve()
    if scratch.exists():
        raise SystemExit('new scratch dir required')
    said = {}
    for platform in ('claude', 'gemini'):
        folder = project(scratch / platform)
        said[platform] = {}
        for path in ('src/api/handler.ts', 'lib/util.ts'):
            # Once per file: a second call is rightly silent, the file being briefed already.
            text = brief(platform, folder, path)
            said[platform][path] = [tag for tag in ('CLAUDE-RULE', 'CURSOR-RULE', 'COPILOT-RULE', 'AGENTS-RULE')
                                    if tag in text]
    checks = {
        'claude gets two other agents\' rules, not its own':
            said['claude']['src/api/handler.ts'] == ['CURSOR-RULE', 'COPILOT-RULE'],
        'gemini gets the first two by source, Claude\'s included':
            said['gemini']['src/api/handler.ts'] == ['CLAUDE-RULE', 'CURSOR-RULE'],
        'a non-matching file gets no project rule, either host':
            said['claude']['lib/util.ts'] == [] and said['gemini']['lib/util.ts'] == [],
    }
    result = {'said': said, 'checks': checks}
    Path(__file__).with_name('rehearsal.json').write_text(json.dumps(result, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=1))
    print('rehearsal:', 'PASS' if all(checks.values()) else 'FAIL')


if __name__ == '__main__':
    main()
