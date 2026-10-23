import pytest

SALES = """region,product,units,amount
East,Widget,3,1200.50
West,Gadget,1,-150.25
East,Gadget,2,300

North,Widget,5,"1,000.00"
West,Widget,4,99.75
"""


@pytest.fixture
def write_csv(tmp_path):
    def write(text, name="data.csv", encoding="utf-8"):
        path = tmp_path / name
        path.write_bytes(text.encode(encoding))
        return path
    return write


@pytest.fixture
def sales(write_csv):
    return write_csv(SALES, "sales.csv")
