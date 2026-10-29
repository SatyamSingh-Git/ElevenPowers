# Generated from the vendor sensor catalog, release 2026.03, by the catalog
# export job. Do not edit by hand: regenerate it when the catalog changes.

CATALOG_RELEASE = "2026.03"

SENSOR_KINDS = {
    "temperature": {
        "unit": "C",
        "accepts": ("C", "F"),
        "min": -20.0,
        "max": 60.0,
        "decimals": 1,
    },
    "humidity": {
        "unit": "%",
        "accepts": ("%",),
        "min": 0.0,
        "max": 100.0,
        "decimals": 0,
    },
    "soil_moisture": {
        "unit": "%",
        "accepts": ("%",),
        "min": 0.0,
        "max": 100.0,
        "decimals": 1,
    },
    "light": {
        "unit": "lux",
        "accepts": ("lux", "klux"),
        "min": 0.0,
        "max": 150000.0,
        "decimals": 0,
    },
}
