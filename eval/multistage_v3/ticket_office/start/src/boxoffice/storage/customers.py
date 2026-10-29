"""The customer book, kept in customers.json and keyed by email address."""
import json
from pathlib import Path

from ..errors import BoxOfficeError
from ..model.customer import Customer, normalise_email

CUSTOMERS_FILE = "customers.json"


class CustomerBook:
    def __init__(self, root):
        self.path = Path(root) / CUSTOMERS_FILE

    def all(self):
        if not self.path.is_file():
            return {}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return {email: Customer.from_dict(email, fields) for email, fields in data.items()}

    def get(self, email):
        customer = self.all().get(normalise_email(email))
        if customer is None:
            raise BoxOfficeError("unknown-customer", email=email)
        return customer

    def add(self, email, name, phone="", mailing_list=False):
        email = normalise_email(email)
        customers = self.all()
        if email in customers:
            raise BoxOfficeError("duplicate-customer", email=email)
        customer = Customer(email, name.strip(), phone.strip(), mailing_list)
        customers[email] = customer
        self._save(customers)
        return customer

    def update(self, email, *, name=None, phone=None, mailing_list=None):
        customers = self.all()
        customer = customers.get(normalise_email(email))
        if customer is None:
            raise BoxOfficeError("unknown-customer", email=email)
        if name is not None:
            customer.name = name.strip()
        if phone is not None:
            customer.phone = phone.strip()
        if mailing_list is not None:
            customer.mailing_list = mailing_list
        self._save(customers)
        return customer

    def search(self, text):
        return sorted((c for c in self.all().values() if c.matches(text)), key=lambda c: (c.name.lower(), c.email))

    def mailing_list(self):
        return sorted(c.email for c in self.all().values() if c.mailing_list)

    def _save(self, customers):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {email: customers[email].to_dict() for email in sorted(customers)}
        self.path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
