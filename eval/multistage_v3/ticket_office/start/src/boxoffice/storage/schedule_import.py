"""Reads a season schedule from CSV: one performance per row, one price column per tier.

    code,title,starts,A,B
    HAM-0412E,Hamlet,2026-04-12T19:30,32.00,24.00
"""
import csv

from ..clock import parse_time
from ..model.money import parse_price
from ..model.performance import Performance

FIXED_COLUMNS = ("code", "title", "starts")


class ScheduleError(ValueError):
    pass


def read_schedule(path):
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        for name in FIXED_COLUMNS:
            if name not in columns:
                raise ScheduleError(f"{path}: no {name} column")
        tiers = [name for name in columns if name not in FIXED_COLUMNS]
        return [_performance(path, number, row, tiers) for number, row in enumerate(reader, 2)]


def _performance(path, number, row, tiers):
    try:
        starts = parse_time(row["starts"])
        prices = {tier: parse_price(row[tier]) for tier in tiers if (row[tier] or "").strip()}
    except ValueError as error:
        raise ScheduleError(f"{path} line {number}: {error}") from None
    return Performance(row["code"].strip(), row["title"].strip(), starts, prices)
