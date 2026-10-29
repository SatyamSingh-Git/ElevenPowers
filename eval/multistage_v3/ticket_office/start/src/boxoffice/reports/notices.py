"""Letters to customers whose performance was cancelled, ready to paste into an email."""
from ..clock import format_time
from ..model.money import format_pence


def cancellation_notices(performance, orders, customers, theatre):
    """One (email, text) pair per customer with an order for the cancelled `performance`.

    Orders without a customer in the book are left out; the counter rings those.
    """
    notices = []
    for order in sorted(orders.values(), key=lambda order: order.id):
        if order.performance != performance.code or order.customer not in customers:
            continue
        customer = customers[order.customer]
        refunded = sum(line.price for line in order.lines if line.refunded) + order.fee
        when = format_time(performance.starts).replace("T", " at ")
        text = "\n".join([
            f"Dear {customer.name},",
            "",
            f"We are sorry to tell you that {performance.title} on {when} has been cancelled.",
            f"We have refunded {format_pence(refunded)} for order {order.id}, including the booking fee,",
            f"to the {order.payment} you paid with.",
            "",
            theatre,
        ])
        notices.append((customer.email, text))
    return notices
