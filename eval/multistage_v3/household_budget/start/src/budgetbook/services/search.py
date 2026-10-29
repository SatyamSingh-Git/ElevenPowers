"""Finding transactions by payee, category, account or month."""
from ..rules.matchers import MATCHERS


def find_transactions(transactions, payee="", category=None, account="", month=None):
    """Matching transactions, newest first.

    `category` "" finds uncategorised transactions; None does not filter.
    """
    payee_matches = MATCHERS["contains"]
    found = [
        transaction for transaction in transactions
        if (not payee or payee_matches(payee, transaction.payee))
        and (category is None or transaction.category == category)
        and (not account or transaction.account == account)
        and (month is None or transaction.date in month)
    ]
    return sorted(found, key=lambda transaction: (transaction.date, transaction.id), reverse=True)
