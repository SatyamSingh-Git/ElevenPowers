"""The refusals the library makes.

Every refusal carries a stable code, which scripts can rely on, and a message
for the person at the desk. The messages are listed in docs/reference.md.
"""

MESSAGES = {
    'unknown_member': 'no member with card {card}',
    'unknown_copy': 'no copy with barcode {barcode}',
    'unknown_title': 'no title with id {title}',
    'duplicate_member': 'card {card} is already registered',
    'cannot_leave': '{card} cannot leave: {reason}',
    'invalid_member': 'member {card}: {problem}',
    'on_loan': '{barcode} is already on loan',
    'not_on_loan': '{barcode} is not on loan',
    'not_in_transit': '{barcode} is not in transit',
    'wrong_branch': '{barcode} belongs to {branch}',
    'held_for_other': '{barcode} is being held for another member',
    'loan_limit': '{card} has reached the loan limit of {limit}',
    'member_blocked': '{card} owes {owed} and cannot borrow until it is paid',
    'renew_limit': '{barcode} has already been renewed {limit} times',
    'hold_limit': '{card} already has {limit} holds',
    'duplicate_hold': '{card} already has a hold on {title}',
    'bad_waiver': 'cannot waive {amount}: {card} owes {owed}',
    'bad_note': 'note not added: {problem}',
    'bad_amount': 'not an amount of money: {text}',
    'bad_date': 'not a date: {text}',
    'bad_setting': 'lending.ini option {name}: {problem}',
    'bad_catalogue': '{path}: {problem}',
    'bad_calendar': '{path} line {line}: {problem}',
    'bad_ledger': '{path} line {line}: {problem}',
    'bad_import': 'row {row}: {problem}',
}


class LendingError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def refuse(code, **fields):
    return LendingError(code, MESSAGES[code].format(**fields))
