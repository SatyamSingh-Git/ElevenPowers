"""How numbers look in tables, exports and reports."""

MEAN_DECIMALS = 2

# Scores whose rule yields a share are shown as a percentage, and NPS with its sign.
SCORE_STYLES = {
    'top_box': 'share',
    'nps': 'signed',
}


def format_percent(value, decimals=1):
    return f'{value:.{decimals}f}'


def format_number(value, decimals=1):
    """Whole numbers without decimals, anything else rounded to `decimals`."""
    if float(value).is_integer():
        return str(int(value))
    return f'{value:.{decimals}f}'


def format_score(value, rule, decimals=1):
    if value is None:
        return '-'
    style = SCORE_STYLES.get(rule)
    if style == 'share':
        return f'{format_percent(100 * value, decimals)}%'
    if style == 'signed':
        return f'{value:+.0f}'
    return format_number(value, MEAN_DECIMALS)
