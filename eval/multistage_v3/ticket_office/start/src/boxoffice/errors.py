"""The error the box office raises when it refuses a request.

Every refusal carries a stable `code` that callers branch on and a message for
the person at the counter. The messages live in one table so that the command
line and the services always say the same thing.
"""

MESSAGES = {
    "bad-seatmap": "seat map line {line}: {problem}",
    "no-venue": "no venue installed; run the venue command first",
    "unknown-section": "unknown section {section}",
    "unknown-seat": "unknown seat {seat}",
    "duplicate-seat": "seat {seat} is named twice",
    "seat-unavailable": "seat {seat} is not available",
    "bad-performance-code": "performance codes use A-Z, 0-9 and '-', got {code}",
    "unknown-performance": "unknown performance {code}",
    "duplicate-performance": "performance {code} already exists",
    "performance-has-orders": "performance {code} has orders; cancel it instead",
    "missing-price": "performance {code} has no price for tier {tier}",
    "unknown-tier": "the venue has no tier {tier}",
    "performance-started": "performance {code} has already started",
    "performance-cancelled": "performance {code} is cancelled",
    "no-seats": "name at least one seat",
    "too-many": "at most {limit} tickets per order",
    "not-enough-seats": "no block of {count} seats available",
    "unknown-hold": "unknown hold {hold}",
    "hold-expired": "hold {hold} has expired",
    "hold-closed": "hold {hold} is no longer active",
    "not-in-hold": "seat {seat} is not in hold {hold}",
    "unknown-concession": "unknown concession {name}",
    "unknown-payment": "unknown payment method {name}",
    "unknown-order": "unknown order {order}",
    "not-in-order": "seat {seat} is not in order {order}",
    "refund-closed": "refunds close {hours} hours before the performance",
    "seat-count": "an exchange needs {count} seats",
    "exchange-refunded": "order {order} has refunded seats and cannot be exchanged",
    "bad-email": "not an email address: {email}",
    "unknown-customer": "no customer with email {email}",
    "duplicate-customer": "a customer with email {email} already exists",
    "already-waiting": "{email} is already waiting for {code}",
    "not-waiting": "{email} is not waiting for {code}",
    "unknown-backup": "no backup named {name}",
    "backup-exists": "a backup named {name} already exists",
}


class BoxOfficeError(Exception):
    def __init__(self, code, /, **details):
        self.code = code
        self.details = details
        super().__init__(MESSAGES[code].format(**details))

    @property
    def message(self):
        return str(self)
