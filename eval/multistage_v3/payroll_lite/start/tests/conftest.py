import pytest

from payroll.config import load_settings
from payroll.storage.files import DataDir

SETTINGS = """[company]
name = Test Bakery
pay_frequency = weekly
first_period_start = 2026-01-05
"""


@pytest.fixture
def data(tmp_path):
    (tmp_path / "payroll.ini").write_text(SETTINGS, encoding="utf-8")
    return DataDir(tmp_path)


@pytest.fixture
def settings(data):
    return load_settings(data.root)
