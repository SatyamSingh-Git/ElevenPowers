class ManualClock:
    """Milliseconds that only move when told to.

    It is the default so that a log never reads the wall clock behind its
    caller's back; services pass their own clock.
    """

    def __init__(self, now=0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, ms):
        if ms < 0:
            raise ValueError('a clock cannot go backwards')
        self.now += ms
        return self.now
