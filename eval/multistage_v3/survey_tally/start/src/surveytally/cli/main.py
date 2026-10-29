"""The surveytally command line.

Most commands work on a project folder made by `surveytally init`. Exit status
is 0 on success, 1 when a file or setting cannot be used, 2 for a mistake in
the command itself and 3 when imported or validated responses have problems.
"""
import argparse
from collections import Counter
from pathlib import Path
import sys

from .. import __version__
from ..files.csv_responses import read_responses
from ..files.json_responses import read_json_responses
from ..files.store import Project
from ..files.survey_file import load_survey
from ..files.targets_file import read_targets
from ..model.errors import ConfigError, ProjectError, ResponseFileError, ScoringError, SurveyError, WeightingError
from ..reports.banner import banner_table
from ..reports.codebook import write_codebook
from ..reports.compare import compare, format_changes
from ..reports.export import EXPORT_FORMATS, export_crosstab, export_frequencies, export_scores
from ..reports.formatting import format_percent
from ..reports.progress import progress_report
from ..reports.render import render_text
from ..reports.responses_export import write_json_responses, write_responses
from ..reports.summary import summary
from ..reports.tables import Table, crosstab_table, frequency_table, scores_table
from ..services.analysis import analyse
from ..services.cleaning import clean
from ..services.coding import code_answers, read_codeframe
from ..services.crosstab import crosstab
from ..services.filters import parse_condition, select
from ..services.quality import item_nonresponse, quality_flags
from ..services.scoring import check_definitions, compute_scores
from ..services.significance import significance
from ..services.tally import frequencies
from ..services.validation import validate
from ..services.weighting import compute_weights, describe, efficiency
from .config import load_settings

JSON_LINES_SUFFIXES = ('.jsonl', '.ndjson')

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_INVALID = 3

FAILURES = (ConfigError, ProjectError, ResponseFileError, ScoringError, SurveyError, WeightingError, OSError)


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except FAILURES as error:
        print(f'error: {error}', file=sys.stderr)
        return EXIT_ERROR


def build_parser():
    parser = argparse.ArgumentParser(prog='surveytally', description='Import survey responses and tabulate them.')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    commands = parser.add_subparsers(dest='command', required=True)

    command = commands.add_parser('init', help='start a project folder for a survey')
    command.add_argument('folder')
    command.add_argument('survey', help='survey file (JSON)')
    command.set_defaults(handler=cmd_init)

    command = commands.add_parser('import', help='add responses from a response file (CSV or JSON lines)')
    command.add_argument('folder')
    command.add_argument('responses', help='response file')
    command.add_argument('--replace', action='store_true', help='drop the responses imported before')
    command.set_defaults(handler=cmd_import)

    command = commands.add_parser('validate', help='check a response file without importing it')
    command.add_argument('survey', help='survey file (JSON)')
    command.add_argument('responses', help='response file (CSV or JSON lines)')
    command.set_defaults(handler=cmd_validate)

    command = commands.add_parser('status', help='what a project folder holds')
    command.add_argument('folder')
    command.set_defaults(handler=cmd_status)

    command = commands.add_parser('check', help='check a survey file and list its questions')
    command.add_argument('survey', help='survey file (JSON)')
    command.set_defaults(handler=cmd_check)

    command = commands.add_parser('codebook', help='write the codes every question uses')
    command.add_argument('survey', help='survey file (JSON)')
    command.add_argument('out')
    command.add_argument('--format', choices=EXPORT_FORMATS, default='csv')
    command.set_defaults(handler=cmd_codebook)

    command = commands.add_parser('progress', help='responses per day, and quota cells against a goal')
    command.add_argument('folder')
    command.add_argument('--targets', help='targets CSV file to read quotas from')
    command.add_argument('--goal', type=int, help='number of completes wanted')
    command.set_defaults(handler=cmd_progress)

    command = commands.add_parser('quality', help='flag straightliners and respondents who skip most questions')
    command.add_argument('folder')
    command.set_defaults(handler=cmd_quality)

    command = commands.add_parser('weight', help='compute weights from population targets')
    command.add_argument('folder')
    command.add_argument('targets', help='targets CSV file')
    command.add_argument('--cap', type=float, help='largest weight allowed after trimming')
    command.set_defaults(handler=cmd_weight)

    command = commands.add_parser('tally', help='print frequency tables')
    _analysis_options(command)
    command.add_argument('--question', action='append', help='only this question; repeat for more')
    command.set_defaults(handler=cmd_tally)

    command = commands.add_parser('crosstab', help='break one question down by another')
    _analysis_options(command)
    command.add_argument('row', help='question shown in the rows')
    command.add_argument('column', help='question shown in the columns')
    command.add_argument('--out', help='write the table to this file instead of printing it')
    command.add_argument('--format', choices=EXPORT_FORMATS)
    command.add_argument('--significance', action='store_true', help='mark significant differences between columns')
    command.set_defaults(handler=cmd_crosstab)

    command = commands.add_parser('banner', help='one question by several others, side by side')
    _analysis_options(command)
    command.add_argument('row', help='question shown in the rows')
    command.add_argument('columns', nargs='+', help='questions shown across the top')
    command.add_argument('--significance', action='store_true', help='mark significant differences between columns')
    command.set_defaults(handler=cmd_banner)

    command = commands.add_parser('export', help='write every frequency table to a file')
    _analysis_options(command)
    command.add_argument('out')
    command.add_argument('--format', choices=EXPORT_FORMATS)
    command.add_argument('--scores', help='also write the scores to this file')
    command.set_defaults(handler=cmd_export)

    command = commands.add_parser('scores', help='print the scores the survey defines')
    _analysis_options(command)
    command.set_defaults(handler=cmd_scores)

    command = commands.add_parser('summary', help='print a one-line result per question')
    _analysis_options(command)
    command.set_defaults(handler=cmd_summary)

    command = commands.add_parser('code', help='code the answers to a free-text question with a codeframe')
    _analysis_options(command)
    command.add_argument('question')
    command.add_argument('codeframe', help='codeframe CSV file')
    command.set_defaults(handler=cmd_code)

    command = commands.add_parser('export-responses',
                                  help='write the accepted responses as a response file (CSV, or JSON lines for .jsonl)')
    command.add_argument('folder')
    command.add_argument('out')
    command.add_argument('--labels', action='store_true', help='write answer labels instead of codes')
    command.set_defaults(handler=cmd_export_responses)

    command = commands.add_parser('compare', help='compare two exported frequency tables (CSV)')
    command.add_argument('before')
    command.add_argument('after')
    command.add_argument('--decimals', type=int, default=1)
    command.add_argument('--threshold', type=float, default=0.0, help='hide changes smaller than this many points')
    command.set_defaults(handler=cmd_compare)
    return parser


def _analysis_options(command):
    command.add_argument('folder')
    command.add_argument('--decimals', type=int, help='decimals for percentages')
    command.add_argument('--unweighted', action='store_true', help='ignore the project weights')
    command.add_argument('--where', action='append', default=[],
                         help='only responses matching a condition such as region=north; repeat to narrow further')


def _open(args):
    """The project, its responses (narrowed by --where), its weights unless --unweighted, and its settings."""
    project = Project(args.folder)
    settings = load_settings(args.folder)
    weights = None if args.unweighted else project.weights()
    if args.decimals is None:
        args.decimals = settings.decimals
    conditions = [parse_condition(project.survey, text) for text in args.where]
    return project, select(project.responses(), conditions), weights, settings


def _read(survey, path):
    if Path(path).suffix.lower() in JSON_LINES_SUFFIXES:
        return read_json_responses(survey, path)
    return read_responses(survey, path)


def cmd_init(args):
    survey = load_survey(args.survey)
    Project.create(args.folder, survey)
    print(f'created project {args.folder} for survey {survey.id} ({len(survey.questions)} questions)')
    return EXIT_OK


def cmd_import(args):
    project = Project(args.folder)
    settings = load_settings(args.folder)
    survey = project.survey
    incoming = _read(survey, args.responses)
    valid, issues = validate(survey, incoming)
    existing = [] if args.replace else project.responses()
    cleaned = clean(valid, min_seconds=settings.min_seconds, existing=existing)
    project.replace_responses(cleaned.kept)
    print(f'read {len(incoming)} responses: {len(valid)} valid, {len(incoming) - len(valid)} rejected')
    print(f'the project now holds {len(cleaned.kept)} responses '
          f'({len(cleaned.duplicates)} replaced by a later submission, {len(cleaned.speeders)} speeders dropped)')
    if project.has_weights():
        project.clear_weights()
        print('weights removed: run surveytally weight again')
    for issue in issues:
        print(f'  {issue}')
    return EXIT_INVALID if issues else EXIT_OK


def cmd_validate(args):
    survey = load_survey(args.survey)
    responses = _read(survey, args.responses)
    valid, issues = validate(survey, responses)
    for issue in issues:
        print(issue)
    print(f'{len(valid)} of {len(responses)} responses are valid')
    return EXIT_INVALID if issues else EXIT_OK


def cmd_weight(args):
    project = Project(args.folder)
    targets = read_targets(args.targets)
    options = {} if args.cap is None else {'cap': args.cap}
    weights = compute_weights(project.survey, project.responses(), targets, **options)
    project.save_weights(weights)
    found = describe(weights, **options)
    print(f'weighted {found.respondents} respondents: weights {found.smallest:.2f} to {found.largest:.2f}, '
          f'{found.trimmed} trimmed')
    print(f'effective sample size {found.effective_size:.0f} (efficiency {efficiency(weights):.0%})')
    return EXIT_OK


def cmd_tally(args):
    project, responses, weights, _ = _open(args)
    tables = frequencies(project.survey, responses, weights)
    for question_id in args.question or project.survey.question_ids():
        if question_id not in tables:
            raise SurveyError(f'unknown question {question_id}')
        print(render_text(frequency_table(tables[question_id], args.decimals)))
        print()
    return EXIT_OK


def cmd_crosstab(args):
    project, responses, weights, settings = _open(args)
    result = crosstab(project.survey, responses, args.row, args.column, weights)
    if args.out:
        export_crosstab(result, args.out, args.format or settings.format, args.decimals)
        print(f'wrote {args.out}')
    else:
        marks = significance(result) if args.significance else None
        print(render_text(crosstab_table(result, args.decimals, marks=marks)))
    return EXIT_OK


def cmd_banner(args):
    project, responses, weights, _ = _open(args)
    table = banner_table(project.survey, responses, args.row, args.columns, weights, args.decimals,
                         letters=args.significance)
    print(render_text(table))
    return EXIT_OK


def cmd_export(args):
    project, responses, weights, settings = _open(args)
    results = analyse(project.survey, responses, weights)
    format = args.format or settings.format
    export_frequencies(results.tables, args.out, format, args.decimals)
    print(f'wrote {args.out}')
    if args.scores:
        export_scores(results.scores, args.scores, format, args.decimals)
        print(f'wrote {args.scores}')
    return EXIT_OK


def cmd_scores(args):
    project, responses, weights, _ = _open(args)
    scores = compute_scores(project.survey, responses, weights)
    if not scores:
        print(f'survey {project.survey.id} defines no scores')
        return EXIT_OK
    print(render_text(scores_table(scores, args.decimals)))
    return EXIT_OK


def cmd_summary(args):
    project, responses, weights, _ = _open(args)
    print(summary(analyse(project.survey, responses, weights), args.decimals), end='')
    return EXIT_OK


def cmd_export_responses(args):
    project = Project(args.folder)
    responses = project.responses()
    if Path(args.out).suffix.lower() in JSON_LINES_SUFFIXES:
        if args.labels:
            raise SurveyError('--labels only applies to CSV files')
        write_json_responses(project.survey, responses, args.out)
    else:
        write_responses(project.survey, responses, args.out, labels=args.labels)
    print(f'wrote {len(responses)} responses to {args.out}')
    return EXIT_OK


def cmd_compare(args):
    print(format_changes(compare(args.before, args.after), args.decimals, args.threshold), end='')
    return EXIT_OK


def cmd_status(args):
    project = Project(args.folder)
    survey, responses = project.survey, project.responses()
    print(f'survey {survey.id}: {survey.title}')
    print(f'{len(responses)} responses')
    dates = sorted(response.submitted for response in responses if response.submitted)
    if dates:
        print(f'submitted {dates[0]} to {dates[-1]}')
    weights = project.weights()
    if weights is None:
        print('not weighted')
    else:
        print(f'weighted: {len(weights)} weights, efficiency {efficiency(weights):.0%}')
    return EXIT_OK


def cmd_check(args):
    survey = load_survey(args.survey)
    kinds = Counter(question.type for question in survey.questions)
    print(f'{survey.id}: {survey.title}')
    print(f'{len(survey.questions)} questions ({", ".join(f"{count} {kind}" for kind, count in kinds.items())}), '
          f'{len(survey.scores)} scores')
    problems = check_definitions(survey)
    for problem in problems:
        print(f'  {problem}')
    return EXIT_ERROR if problems else EXIT_OK


def cmd_codebook(args):
    write_codebook(load_survey(args.survey), args.out, args.format)
    print(f'wrote {args.out}')
    return EXIT_OK


def cmd_progress(args):
    if (args.targets is None) != (args.goal is None):
        raise SurveyError('--targets and --goal go together')
    project = Project(args.folder)
    targets = read_targets(args.targets) if args.targets else None
    print(progress_report(project.responses(), targets, args.goal), end='')
    return EXIT_OK


def cmd_quality(args):
    project = Project(args.folder)
    responses = project.responses()
    flags = quality_flags(project.survey, responses)
    for flag in flags:
        print(flag)
    print(f'{len(flags)} flags in {len(responses)} responses')
    print('unanswered by question:')
    for question_id, share in item_nonresponse(project.survey, responses).items():
        print(f'  {question_id}: {format_percent(100 * share)}%')
    return EXIT_OK


def cmd_code(args):
    project, responses, weights, _ = _open(args)
    rows = code_answers(project.survey, responses, args.question, read_codeframe(args.codeframe), weights)
    table = Table(f'{args.question} coded', ['Code', 'Label', 'Count', '%'],
                  [[row.code, row.label, str(row.count), format_percent(row.percent, args.decimals)] for row in rows])
    print(render_text(table))
    return EXIT_OK
