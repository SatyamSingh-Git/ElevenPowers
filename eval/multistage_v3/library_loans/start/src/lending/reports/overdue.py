"""Everything out past its due date, worst first.

`accrued` is what the member would be charged if the copy came back today, so
staff can quote it at the desk or on the phone.
"""
from ..model.dates import days_late, format_date
from ..model.money import format_money
from ..services.policy import daily_fine

COLUMNS = ('barcode', 'title', 'card', 'due', 'days', 'accrued')


def overdue_rows(library):
    today = library.today()
    settings = library.settings
    rows = []
    for loan in library.loans.values():
        days = days_late(loan.due, today)
        if days <= 0:
            continue
        copy = library.catalogue.copy(loan.barcode)
        title = library.catalogue.title(copy.title_id)
        accrued = min(days * daily_fine(settings, title.material), settings.max_fine, copy.price)
        rows.append({'barcode': loan.barcode, 'title': title.title, 'card': loan.card,
                     'due': format_date(loan.due), 'days': days, 'accrued': format_money(accrued)})
    rows.sort(key=lambda row: (-row['days'], row['barcode']))
    return rows
