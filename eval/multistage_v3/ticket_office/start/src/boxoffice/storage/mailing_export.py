"""Exports the mailing list as CSV for the newsletter service."""
import csv

COLUMNS = ("email", "name", "first_name")


def export_mailing_list(customers, path):
    """Write every customer who agreed to hear from us to `path`; returns how many."""
    chosen = sorted((c for c in customers.values() if c.mailing_list), key=lambda c: c.email)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        for customer in chosen:
            first_name = customer.name.split()[0] if customer.name.split() else ""
            writer.writerow([customer.email, customer.name, first_name])
    return len(chosen)
