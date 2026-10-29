"""The waiting list for performances that have sold out."""
from ..errors import BoxOfficeError
from ..model.customer import normalise_email
from .availability import free_count


class Waitlist:
    def __init__(self, store, clock):
        self.store = store
        self.clock = clock

    def join(self, code, email, seats):
        """Put `email` on the list for `seats` seats of `code`; returns their place in the queue."""
        self.store.performance(code)
        email = normalise_email(email)
        waiting = self.store.load_waitlist()
        queue = waiting.setdefault(code, [])
        if any(entry["email"] == email for entry in queue):
            raise BoxOfficeError("already-waiting", email=email, code=code)
        queue.append({"email": email, "seats": seats})
        self.store.save_waitlist(waiting)
        return len(queue)

    def leave(self, code, email):
        email = normalise_email(email)
        waiting = self.store.load_waitlist()
        queue = waiting.get(code, [])
        kept = [entry for entry in queue if entry["email"] != email]
        if len(kept) == len(queue):
            raise BoxOfficeError("not-waiting", email=email, code=code)
        waiting[code] = kept
        self.store.save_waitlist(waiting)

    def queue(self, code):
        return list(self.store.load_waitlist().get(code, []))

    def to_contact(self, code):
        """Who to ring now, in the order they joined: everyone whose party still fits.

        Someone further down the queue with a smaller party can be offered seats
        that are too few for the person ahead of them.
        """
        left = free_count(self.store, code, self.clock.now())
        chosen = []
        for entry in self.queue(code):
            if entry["seats"] <= left:
                chosen.append(entry)
                left -= entry["seats"]
        return chosen
