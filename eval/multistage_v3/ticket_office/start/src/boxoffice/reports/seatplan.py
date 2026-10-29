"""The seat plan on the counter screen: one line per row, one symbol per seat."""

SYMBOLS = {
    "free": ".",
    "held": "h",
    "sold": "x",
}


def render_seatplan(venue, states):
    """`states` maps each seat id to its state for one performance."""
    lines = [venue.name]
    for section in venue.sections:
        lines.append(f"{section.name} (tier {section.tier})")
        for row, seats in section.rows.items():
            marks = " ".join(SYMBOLS[states[seat.id]] for seat in seats)
            lines.append(f"  {row:<2} {seats[0].number:>3} {marks}")
    shown = set(states.values())
    lines.append("key: " + "  ".join(f"{symbol} {state}" for state, symbol in SYMBOLS.items() if state in shown))
    return "\n".join(lines)


def count_states(states):
    """How many seats are in each state, every state listed."""
    counted = {state: 0 for state in SYMBOLS}
    for state in states.values():
        counted[state] += 1
    return counted
