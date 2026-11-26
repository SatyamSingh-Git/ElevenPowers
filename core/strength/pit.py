"""PIT for the Java lines a change touched.

The borrow: PIT (pitest, Apache-2.0) chooses the mutations, mutates bytecode, picks the
tests that cover each mutant and runs them; gradle-pitest-plugin (Apache-2.0) does the
same from Gradle. What is added: running it through the project's own build tool without
touching its build files, and keeping only the mutants on changed lines as the same
observations the other engines produce. PIT runs its own selection of tests, not the
recorded command, which every Java record says.
"""
import os
from pathlib import Path
import re
import shutil
import tempfile
import xml.etree.ElementTree as ElementTree

from ..stress import BUILD_TOOL
from .execution import execute
from .model import Observation

PIT = '1.30.2'
JUNIT5 = '1.2.3'
GRADLE_PLUGIN = '1.19.0'
LIMITATION = ("Java mutants are run by PIT against the tests it selects from the build's test classpath, "
              'not by the recorded test command.')
PACKAGE = re.compile(r'^\s*package\s+([\w.]+)\s*;', re.MULTILINE)
REPORTS = ('target/pit-reports', 'build/reports/pitest')
WINDOWS = os.name == 'nt'
STATUS = {'KILLED': 'detected', 'TIMED_OUT': 'detected', 'MEMORY_ERROR': 'detected',
          'SURVIVED': 'undetected', 'NO_COVERAGE': 'undetected', 'NON_VIABLE': 'invalid',
          'NOT_STARTED': 'not_run', 'STARTED': 'not_run'}
# Applied to each project, not from the script's own scope: Gradle refuses that
# ("must be applied in a build script").
INIT = f"""initscript {{
    repositories {{ gradlePluginPortal() }}
    dependencies {{ classpath 'info.solidsoft.gradle.pitest:gradle-pitest-plugin:{GRADLE_PLUGIN}' }}
}}

allprojects {{ project ->
    project.plugins.withId('java') {{
        project.pluginManager.apply(info.solidsoft.gradle.pitest.PitestPlugin)
        project.pitest {{
            pitestVersion = '{PIT}'
            junit5PluginVersion = '{JUNIT5}'
            targetClasses = (project.findProperty('epPitTargets') ?: '').tokenize(',')
            outputFormats = ['XML']
            timestampedReports = false
            failWhenNoMutations = false
        }}
    }}
}}
"""


def tool(command):
    match = BUILD_TOOL.search(command)
    return match[0].lstrip(';&|( \t') if match else None


def _package(root, path):
    found = PACKAGE.search((root / path).read_text(encoding='utf-8', errors='replace'))
    return found[1] if found else ''


def targets(root, paths):
    return sorted({'.'.join(filter(None, (_package(root, p), Path(p).stem))) + '*' for p in paths})


def invocation(executable, targets, scratch):
    listed = ','.join(targets)
    if Path(executable).name.lower().startswith('gradle'):
        script = scratch / 'pit.gradle'
        script.write_text(INIT, encoding='utf-8')
        return ['--init-script', str(script), '--continue', 'pitest', f'-PepPitTargets={listed}']
    # PIT finds no JUnit 5 test without this plugin, and no class to mutate before test-compile.
    return ['-B', 'dependency:copy', f'-Dartifact=org.pitest:pitest-junit5-plugin:{JUNIT5}',
            f'-DoutputDirectory={scratch}', 'test-compile', f'org.pitest:pitest-maven:{PIT}:mutationCoverage',
            f'-DtargetClasses={listed}', '-DoutputFormats=XML', '-DtimestampedReports=false',
            '-DfailWhenNoMutations=false',
            f'-DadditionalClasspathElements={scratch / f"pitest-junit5-plugin-{JUNIT5}.jar"}']


def _reports(root):
    return [path for path in root.rglob('mutations.xml') if path.parent.as_posix().endswith(REPORTS)]


def observations(root, paths, regions):
    files = {(_package(root, p), Path(p).name): p for p in paths}
    found = []
    for report in _reports(root):
        for mutation in ElementTree.parse(report).getroot().iter('mutation'):
            text = {child.tag: (child.text or '') for child in mutation}
            package, _, name = text['mutatedClass'].rpartition('.')
            path = files.get((package, text['sourceFile']))
            line = int(text['lineNumber'])
            if path is None or not any(start <= line <= end for start, end in regions[path]):
                continue
            indexes = [index.text for index in mutation.iter('index')]
            mutator = text['mutator'].rpartition('.')[2]
            found.append((path, line, len(found), Observation(
                f"pit:{path}:{line}:{mutator}:{'-'.join(indexes)}", path, line, text['description'][:256] or mutator,
                STATUS.get(mutation.get('status'), 'error'), relevance='changed_lines',
                context=f"{name.replace('$', '.')}.{text['mutatedMethod']}"[:256])))
    return [item[3] for item in sorted(found, key=lambda item: item[:3])]


def _reason(output):
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if line.startswith('[ERROR] '):
            return line
        if line == '* What went wrong:' and index + 1 < len(lines):
            return lines[index + 1]
    return lines[-1] if lines else ''


def _reported(root):
    return {(mutation.findtext('mutatedClass').rpartition('.')[0], mutation.findtext('sourceFile'))
            for report in _reports(root) for mutation in ElementTree.parse(report).getroot().iter('mutation')}


def run(root, paths, regions, command, budget, maximum):
    name = tool(command)
    local = root / name
    if WINDOWS and not local.suffix:
        # The extensionless wrapper is the POSIX script, which Windows cannot start; cmd.exe finds the batch one.
        local = next((sibling for sibling in (local.with_suffix('.bat'), local.with_suffix('.cmd'))
                      if sibling.is_file()), local)
    executable = str(local.resolve()) if local.is_file() else shutil.which(name)
    if executable is None:
        return [], [f'PIT needs {name}, which was not found'], False
    for stale in _reports(root):
        stale.unlink()
    with tempfile.TemporaryDirectory(prefix='ep-pit-') as scratch:
        done = execute([executable, *invocation(name, targets(root, paths), Path(scratch))],
                       root, budget, 480, shell=False)
    if done.status != 'complete':
        return [], [f"PIT did not complete ({done.status.replace('_', ' ')})"], False
    if done.returncode:
        return [], [f'PIT did not complete (exit {done.returncode}: {_reason(done.stdout + done.stderr)[:200]})'], False
    if not _reports(root):
        return [], ['PIT did not complete (it wrote no report)'], False
    # PIT reports what it mutated, not what it skipped: a file it never saw would otherwise vanish.
    reported = _reported(root)
    issues = [f'PIT reported no mutant for {path}' for path in paths
              if (_package(root, path), Path(path).name) not in reported]
    found = observations(root, paths, regions)
    return found[:maximum], issues, len(found) > maximum
