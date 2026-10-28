"""Business days: the carrier collects and delivers Monday to Friday."""
from datetime import timedelta


def is_business_day(day):
    return day.weekday() < 5


def next_business_day(day):
    day += timedelta(days=1)
    while not is_business_day(day):
        day += timedelta(days=1)
    return day


def add_business_days(day, count):
    for _ in range(count):
        day = next_business_day(day)
    return day


def ship_date(booked_at, cutoff):
    """The day the carrier collects a parcel booked at `booked_at`."""
    day = booked_at.date()
    if is_business_day(day) and booked_at.time() < cutoff:
        return day
    return next_business_day(day)
