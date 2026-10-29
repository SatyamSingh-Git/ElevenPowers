"""Which seats of a performance can still be sold, and finding seats together."""
from ..errors import BoxOfficeError


def seat_states(store, code, now):
    """Every seat of the venue mapped to free, held or sold for performance `code` at `now`."""
    store.performance(code)
    states = {seat.id: "free" for seat in store.venue().seats()}
    for hold in store.load_holds().values():
        if hold.performance == code and hold.is_active(now):
            for seat in hold.seats:
                states[seat] = "held"
    for order in store.load_orders().values():
        if order.performance == code:
            for line in order.active_lines():
                states[line.seat] = "sold"
    return states


def best_available(store, code, count, now, section=None):
    """The first run of `count` free seats side by side in one row.

    Sections and rows are searched in seat-map order, which runs from the best
    seats in the house to the worst, so the first run found is the best one.
    """
    venue = store.venue()
    if section is None:
        sections = venue.sections
    else:
        found = venue.section(section)
        if found is None:
            raise BoxOfficeError("unknown-section", section=section)
        sections = [found]
    states = seat_states(store, code, now)
    for candidate in sections:
        for seats in candidate.rows.values():
            run = []
            for seat in seats:
                if states[seat.id] != "free":
                    run = []
                    continue
                if run and seat.number != run[-1].number + 1:
                    run = []
                run.append(seat)
                if len(run) == count:
                    return [seat.id for seat in run]
    raise BoxOfficeError("not-enough-seats", count=count)


def section_summary(store, code, now):
    """For each section, how many of its seats are free, held and sold."""
    states = seat_states(store, code, now)
    summary = {}
    for section in store.venue().sections:
        counts = {"free": 0, "held": 0, "sold": 0}
        for seat in section.seats():
            counts[states[seat.id]] += 1
        summary[section.name] = counts
    return summary


def free_count(store, code, now):
    return sum(1 for state in seat_states(store, code, now).values() if state == "free")
