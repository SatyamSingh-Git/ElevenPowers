"""Money is held in pence and shown in pounds."""
import re

from ..errors import refuse

AMOUNT = re.compile(r'£?(\d+)(?:\.(\d{1,2}))?')


def parse_money(text):
    """Pence for '2', '2.5', '2.50' or '£2.50'."""
    match = AMOUNT.fullmatch(text.strip())
    if not match:
        raise refuse('bad_amount', text=text)
    pounds, pence = match.groups()
    return int(pounds) * 100 + int((pence or '0').ljust(2, '0'))


def format_money(pence):
    sign = '-' if pence < 0 else ''
    pence = abs(pence)
    return f'{sign}£{pence // 100}.{pence % 100:02d}'


def plain_amount(pence):
    """Pounds with two decimals and no currency sign, as files store them."""
    return f'{pence // 100}.{pence % 100:02d}'
