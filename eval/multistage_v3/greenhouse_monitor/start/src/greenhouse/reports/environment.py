"""Text for the light, climate, sensor and uptime views."""
from .formatting import table


def light_text(lights, target_dli):
    if not lights:
        return "Light: no light readings"
    rows = [
        [light.zone, f"{light.dli:.2f}", light.photoperiod, light.hours_measured,
         "short" if light.dli < target_dli else ""]
        for light in lights
    ]
    return "Light (DLI in mol/m2/day)\n" + table(["zone", "dli", "photoperiod h", "hours measured", ""], rows)


def climate_text(climate):
    if not climate:
        return "Climate: no zone has both temperature and humidity readings"
    rows = [
        [c.zone, f"{c.temperature:.1f}", f"{c.humidity:.0f}", f"{c.vpd:.2f}", f"{c.dew_point:.1f}", c.band]
        for c in climate
    ]
    return "Climate (daily means)\n" + table(["zone", "temp C", "rh %", "vpd kPa", "dew point C", "vpd"], rows)


def condensation_text(hours):
    if not hours:
        return "no condensation risk"
    return "\n".join(
        f"{r.zone} {r.hour:02d}:00 air {r.temperature:.1f} C, dew point {r.dew_point:.1f} C"
        for r in hours
    )


def degree_days_text(results, first, last):
    title = f"Growing degree days {first.isoformat()} to {last.isoformat()}"
    if not results:
        return f"{title}\nno zones"
    rows = [
        [r.zone, r.crop, f"{r.base:.1f}", f"{r.total:.1f}", r.days_counted, r.days_missing]
        for r in results
    ]
    return f"{title}\n" + table(["zone", "crop", "base C", "gdd", "days", "missing"], rows)


def sensors_text(infos, moved):
    if not infos:
        return "no sensors have reported"
    rows = [
        [i.sensor, i.zone, i.kind, i.count, i.last_seen.strftime("%Y-%m-%d %H:%M"),
         "-" if i.interval_minutes is None else f"{i.interval_minutes:.0f} min"]
        for i in infos
    ]
    lines = [table(["sensor", "zone", "kind", "readings", "last seen", "interval"], rows)]
    lines += [f"{sensor} moved: {' -> '.join(zones)}" for sensor, zones in moved.items()]
    return "\n".join(lines)


def uptime_text(gaps, shares):
    if not shares:
        return "no sensors reported that day"
    lines = [table(["sensor", "uptime %"], [[sensor, f"{share:.1f}"] for sensor, share in shares.items()])]
    lines += [
        f"gap {gap.sensor} {gap.start.strftime('%H:%M')}-{gap.end.strftime('%H:%M')} ({gap.minutes} min)"
        for gap in gaps
    ]
    return "\n".join(lines)
