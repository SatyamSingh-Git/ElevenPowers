"""A workspace is one folder holding a household's books."""
import json
from pathlib import Path

from ..errors import BudgetError, ValidationError

SETTINGS_DEFAULTS = {
    "currency": "GBP",
    "report_format": "text",
    "extra_categories": {},
}


class Workspace:
    def __init__(self, root):
        self.root = Path(root)

    @property
    def settings_path(self):
        return self.root / "settings.json"

    @property
    def transactions_path(self):
        return self.root / "transactions.csv"

    @property
    def accounts_path(self):
        return self.root / "accounts.json"

    @property
    def rules_path(self):
        return self.root / "rules.json"

    @property
    def budgets_path(self):
        return self.root / "budgets.json"

    @property
    def recurring_path(self):
        return self.root / "recurring.json"

    @property
    def goals_path(self):
        return self.root / "goals.json"

    @property
    def closed_dir(self):
        return self.root / "closed"

    def closed_month_path(self, month):
        return self.closed_dir / f"{month}.json"

    def is_closed(self, month):
        return self.closed_month_path(month).is_file()

    def create(self, currency):
        if self.settings_path.exists():
            raise BudgetError(f"already a budget folder: {self.root}")
        self.root.mkdir(parents=True, exist_ok=True)
        self.closed_dir.mkdir(exist_ok=True)
        write_json(self.settings_path, {**SETTINGS_DEFAULTS, "currency": currency.upper()})

    def require(self):
        if not self.settings_path.is_file():
            raise BudgetError(f"not a budget folder: {self.root} (run init first)")
        return self

    def settings(self):
        stored = read_json(self.settings_path, {})
        unknown = sorted(set(stored) - set(SETTINGS_DEFAULTS))
        if unknown:
            raise ValidationError(f"unknown setting: {unknown[0]}")
        return {**SETTINGS_DEFAULTS, **stored}

    def save_settings(self, settings):
        write_json(self.settings_path, settings)


def read_json(path, default):
    """The JSON stored at `path`, or `default` when there is no such file."""
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise BudgetError(f"{path.name} is not valid JSON (line {error.lineno}: {error.msg})") from None


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
