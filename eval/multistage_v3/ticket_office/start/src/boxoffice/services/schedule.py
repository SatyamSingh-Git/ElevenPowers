"""Adding performances to the season, one at a time or from a schedule file."""
from ..errors import BoxOfficeError
from ..model.performance import Performance, check_code
from ..storage.schedule_import import read_schedule


class ScheduleService:
    def __init__(self, store):
        self.store = store

    def add(self, code, title, starts, prices):
        """Add one performance. Every tier of the venue needs a price, in pence."""
        return self.add_all([Performance(code, title, starts, dict(prices))])[0]

    def add_all(self, performances):
        """Add several performances, all of them or, when any is refused, none."""
        tiers = self.store.venue().tiers()
        existing = self.store.performances()
        for performance in performances:
            check_code(performance.code)
            if performance.code in existing:
                raise BoxOfficeError("duplicate-performance", code=performance.code)
            for tier in tiers:
                if tier not in performance.prices:
                    raise BoxOfficeError("missing-price", code=performance.code, tier=tier)
            existing[performance.code] = performance
        self.store.save_performances(existing)
        return performances

    def import_file(self, path):
        return self.add_all(read_schedule(path))

    def listing(self, since=None):
        """Performances in date order, optionally only those starting at or after `since`."""
        found = sorted(self.store.performances().values(), key=lambda performance: performance.starts)
        if since is not None:
            found = [performance for performance in found if performance.starts >= since]
        return found

    def remove(self, code):
        """Remove a performance added by mistake. One with orders has to be cancelled instead."""
        performances = self.store.performances()
        if code not in performances:
            raise BoxOfficeError("unknown-performance", code=code)
        if any(order.performance == code for order in self.store.load_orders().values()):
            raise BoxOfficeError("performance-has-orders", code=code)
        del performances[code]
        self.store.save_performances(performances)

    def reprice(self, code, prices):
        """Change the price of some tiers of `code`. Seats already sold keep what they cost."""
        performances = self.store.performances()
        performance = performances.get(code)
        if performance is None:
            raise BoxOfficeError("unknown-performance", code=code)
        tiers = self.store.venue().tiers()
        for tier in prices:
            if tier not in tiers:
                raise BoxOfficeError("unknown-tier", tier=tier)
        performance.prices.update(prices)
        self.store.save_performances(performances)
        return performance
