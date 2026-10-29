"""Rendering tables as Markdown or as aligned plain text."""


def render_markdown(table):
    lines = [f'### {table.title}', '']
    lines.append('| ' + ' | '.join(_escape(cell) for cell in table.columns) + ' |')
    lines.append('|' + '|'.join([' --- '] + [' ---: '] * (len(table.columns) - 1)) + '|')
    for row in table.rows:
        lines.append('| ' + ' | '.join(_escape(cell) for cell in row) + ' |')
    if table.notes:
        lines.append('')
        lines.extend(f'_{note}_' for note in table.notes)
    return '\n'.join(lines)


def render_text(table):
    """The first column left-aligned, the others right-aligned, under an underlined title."""
    grid = [table.columns, *table.rows]
    widths = [max(len(row[index]) for row in grid) for index in range(len(table.columns))]
    lines = [table.title, '-' * len(table.title)]
    for row in grid:
        cells = [row[0].ljust(widths[0])] + [cell.rjust(width) for cell, width in zip(row[1:], widths[1:])]
        lines.append('  '.join(cells).rstrip())
    lines.extend(table.notes)
    return '\n'.join(lines)


def _escape(cell):
    return cell.replace('|', '\\|')


RENDERERS = {
    'markdown': render_markdown,
    'text': render_text,
}
