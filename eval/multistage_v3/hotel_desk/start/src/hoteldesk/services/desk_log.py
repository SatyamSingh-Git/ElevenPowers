"""Wake-up calls and lost property, as the night desk logs them."""
from datetime import timedelta

from ..errors import InvalidState, NotFound, ValidationError
from ..model.desk_log import DISPOSED, HELD, RETURNED, LostItem, WakeUpCall

# Unclaimed property is kept this long before it may be disposed of.
LOST_ITEM_HOLD_DAYS = 90


def book_wake_up(hotel, clock, room_number, at):
    room = hotel.room(room_number)
    if not room.occupied:
        raise InvalidState(f"Room {room.number} is not occupied")
    if at <= clock.now():
        raise ValidationError(f"Wake-up time {at.isoformat(timespec='minutes')} has already passed")
    call = WakeUpCall(room.number, at)
    hotel.wake_up_calls.append(call)
    return call


def calls_due(hotel, clock, minutes=15):
    """Calls not yet made that fall due within the next `minutes`, earliest first."""
    now = clock.now()
    until = now + timedelta(minutes=minutes)
    return sorted((call for call in hotel.wake_up_calls if not call.done and call.at <= until),
                  key=lambda call: (call.at, call.room))


def mark_called(hotel, clock, room_number):
    due = [call for call in calls_due(hotel, clock) if call.room == room_number]
    if not due:
        raise NotFound(f"No wake-up call due for room {room_number}")
    due[0].done = True
    return due[0]


def clear_finished_calls(hotel):
    hotel.wake_up_calls = [call for call in hotel.wake_up_calls if not call.done]


def log_lost_item(hotel, where, description):
    if not description.strip():
        raise ValidationError("Describe the item")
    number = max((item.number for item in hotel.lost_items), default=0) + 1
    item = LostItem(number, hotel.business_date, where, description.strip())
    hotel.lost_items.append(item)
    return item


def _held_item(hotel, number):
    for item in hotel.lost_items:
        if item.number == number:
            if item.status != HELD:
                raise InvalidState(f"Item {number} is already {item.status}")
            return item
    raise NotFound(f"No lost item {number}")


def return_item(hotel, number, to):
    item = _held_item(hotel, number)
    item.status = RETURNED
    item.returned_to = to
    return item


def dispose_unclaimed(hotel):
    """Mark items held longer than the hold period as disposed; returns them."""
    cutoff = hotel.business_date - timedelta(days=LOST_ITEM_HOLD_DAYS)
    disposed = [item for item in hotel.lost_items if item.status == HELD and item.found_on < cutoff]
    for item in disposed:
        item.status = DISPOSED
    return disposed
