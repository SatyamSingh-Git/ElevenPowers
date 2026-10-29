# Generated from the manufacturers' maintenance schedules (2026-03 issue).
# Do not edit by hand; regenerate it from the schedule export instead.

CATALOG_VERSION = "2026.03"

# code: (name, interval in miles, interval in months, vehicle classes)
# An interval of 0 means the service has no limit of that kind.
SERVICE_CATALOG = {
    "AIR-BRAKE": ("Air brake adjustment", 10000, 3, ("heavy",)),
    "AIR-FILTER": ("Engine air filter", 15000, 0, ("light", "medium", "heavy")),
    "BATTERY": ("Battery load check", 0, 12, ("light", "medium", "heavy")),
    "BRAKE-INSP": ("Brake inspection", 15000, 12, ("light", "medium", "heavy")),
    "COOLANT": ("Coolant flush", 60000, 48, ("light", "medium", "heavy")),
    "DOT-ANNUAL": ("DOT annual inspection", 0, 12, ("heavy",)),
    "DPF": ("Diesel particulate filter clean", 100000, 24, ("heavy",)),
    "OIL": ("Engine oil and filter", 7500, 6, ("light", "medium", "heavy")),
    "TIRE-ROT": ("Tyre rotation", 6000, 0, ("light", "medium")),
    "TRANS": ("Transmission fluid", 60000, 0, ("light", "medium", "heavy")),
    "WIPERS": ("Wiper blades", 0, 12, ("light", "medium")),
}
