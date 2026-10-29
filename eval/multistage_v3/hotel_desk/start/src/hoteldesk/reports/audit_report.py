"""The night audit report the auditor files with the day's paperwork."""
from ..money import format_money
from .tables import amount_line


def audit_report_text(hotel, result):
    stats = result.statistics
    lines = [
        f"{hotel.name}",
        f"Night audit for {result.business_date.isoformat()}",
        "",
        f"Rooms sold: {stats['sold']} of {stats['available']}",
        f"Occupancy: {stats['occupancy'] * 100:.1f}%",
        amount_line("ADR", format_money(stats["adr"]), 32),
        amount_line("RevPAR", format_money(stats["revpar"]), 32),
        "",
        amount_line("Room revenue", format_money(result.room_revenue), 32),
        amount_line("Tax", format_money(result.tax_revenue), 32),
        amount_line("Other revenue", format_money(result.other_revenue), 32),
        amount_line("Payments", format_money(result.payments), 32),
        "",
        f"Room charges posted: {len(result.room_charges)}",
        f"No-shows: {', '.join(result.no_shows) or 'none'}",
    ]
    if result.extended:
        lines.append(f"Stays extended past departure: {', '.join(result.extended)}")
    return "\n".join(lines)
