"""The rules every stay must meet, whether it is quoted, booked or imported."""
from ..errors import ValidationError


def check_length(settings, nights):
    if nights > settings.max_stay_nights:
        raise ValidationError(f"Stays are limited to {settings.max_stay_nights} nights")


def check_stay(hotel, settings, *, room_type, arrival, departure, adults, rate_plan):
    kind = hotel.room_type(room_type)
    plan = hotel.rate_plan(rate_plan)
    if departure <= arrival:
        raise ValidationError("Departure must be after arrival")
    if arrival < hotel.business_date:
        raise ValidationError(
            f"Arrival {arrival.isoformat()} is before the business date {hotel.business_date.isoformat()}")
    nights = (departure - arrival).days
    check_length(settings, nights)
    if nights < plan.min_nights:
        raise ValidationError(f"Rate plan {plan.code} requires at least {plan.min_nights} nights")
    if not 1 <= adults <= kind.max_adults:
        raise ValidationError(f"Room type {kind.code} holds at most {kind.max_adults} adults")
