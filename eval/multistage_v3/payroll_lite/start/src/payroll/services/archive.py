"""`payroll archive`: one zip with everything behind a year's pay, for the accountant to keep."""
from pathlib import Path
import zipfile

from payroll.errors import PayrollError
from payroll.services.payrun import list_runs

# A fixed timestamp keeps the same year's archive byte-for-byte the same however often it is made.
ARCHIVED_AT = (2000, 1, 1, 0, 0, 0)


def archive_year(data, year, out):
    """Writes the runs paid in `year`, with their timesheets and bank files; returns the names stored."""
    runs = [run for run in list_runs(data) if run.period.pay_date.year == year]
    if not runs:
        raise PayrollError(f"no pay runs were paid in {year}")
    files = []
    for run in runs:
        for path in (data.run(run.period.id), data.timesheet(run.period.id), data.bank_file(run.period.id)):
            if path.exists():
                files.append(path)
    names = []
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            name = path.relative_to(data.root).as_posix()
            info = zipfile.ZipInfo(name, date_time=ARCHIVED_AT)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
            names.append(name)
    return names
