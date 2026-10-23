"""The in-memory ledger: a chart of accounts and the transactions posted to it."""
from .accounts import Chart
from .money import DEFAULT_CURRENCY, currency_digits
from .transactions import make_transaction


class Ledger:
    """Accounts and transactions in a single currency.

    Balances are signed the same way postings are: debits positive, credits
    negative. A liability with more credits than debits has a negative balance.
    """

    def __init__(self, currency=DEFAULT_CURRENCY):
        currency_digits(currency)
        self.currency = currency
        self.chart = Chart()
        self._transactions = []
        self._balances = {}

    def open(self, name):
        account = self.chart.open(name)
        self._balances[name] = 0
        return account

    def post(self, txn):
        """Add a transaction built by make_transaction; every account must be open."""
        for account in txn.accounts:
            self.chart.get(account)
        self._transactions.append(txn)
        for posting in txn.postings:
            self._balances[posting.account] += posting.amount
        return txn

    def record(self, date, description, postings):
        return self.post(make_transaction(date, description, postings))

    @property
    def transactions(self):
        return tuple(self._transactions)

    def balance(self, name):
        self.chart.get(name)
        return self._balances[name]

    def balances(self):
        """Every open account's balance, in account name order."""
        return {account.name: self._balances[account.name] for account in self.chart}

    def subtotal(self, prefix):
        """Combined balance of `prefix` and every account below it."""
        return sum(self._balances[account.name] for account in self.chart.under(prefix))

    def postings(self, name):
        """(transaction, amount) for each transaction touching `name`, oldest first."""
        self.chart.get(name)
        return [(txn, txn.amount_for(name)) for txn in self._transactions if txn.touches(name)]
