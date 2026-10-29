"""Consistency checks over the data directory, for after a crash or a hand edit."""
from collections import defaultdict


def check_data(store):
    """Problems found, one sentence each. An empty list means the data hangs together."""
    venue = store.venue()
    performances = store.performances()
    orders = store.load_orders()
    problems = []
    sold = defaultdict(list)
    for order in orders.values():
        if order.performance not in performances:
            problems.append(f"order {order.id}: unknown performance {order.performance}")
        for line in order.lines:
            seat = venue.seat(line.seat)
            if seat is None:
                problems.append(f"order {order.id}: unknown seat {line.seat}")
            elif seat.tier != line.tier:
                problems.append(f"order {order.id}: seat {line.seat} is tier {seat.tier}, not {line.tier}")
            if not line.refunded:
                sold[order.performance, line.seat].append(order.id)
    for (code, seat), ids in sorted(sold.items()):
        if len(ids) > 1:
            problems.append(f"{code}: seat {seat} is sold in {', '.join(ids)}")
    for hold in store.load_holds().values():
        if hold.performance not in performances:
            problems.append(f"hold {hold.id}: unknown performance {hold.performance}")
        for seat in hold.seats:
            if venue.seat(seat) is None:
                problems.append(f"hold {hold.id}: unknown seat {seat}")
        if hold.status == "sold" and hold.order not in orders:
            problems.append(f"hold {hold.id}: sold as unknown order {hold.order}")
    return problems
