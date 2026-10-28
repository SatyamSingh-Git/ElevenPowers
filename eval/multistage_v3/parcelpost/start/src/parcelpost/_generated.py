"""Carrier rate card and zone chart.

Generated from the carrier's published rate card. Do not edit by hand: when the
carrier issues a new card, regenerate this file from it.
"""

CARD_VERSION = "2026-Q3"

# Service code -> (display name, transit time in business days).
SERVICES = {
    "economy": ("Economy", 5),
    "ground": ("Ground", 3),
    "express": ("Express", 1),
}

# Postcode area -> zone, measured from the Birmingham depot.
ZONE_CHART = {
    "B": 1, "CV": 1, "DY": 1, "WS": 1, "WV": 1,
    "DE": 2, "GL": 2, "HR": 2, "LE": 2, "NG": 2, "NN": 2, "OX": 2, "ST": 2, "SY": 2, "TF": 2,
    "WR": 2,
    "BA": 3, "BS": 3, "CB": 3, "CH": 3, "L": 3, "LN": 3, "LU": 3, "M": 3, "MK": 3, "PE": 3,
    "S": 3, "SN": 3, "WA": 3,
    "BD": 4, "BN": 4, "CF": 4, "CM": 4, "CO": 4, "CT": 4, "E": 4, "EC": 4, "GU": 4, "HU": 4,
    "IP": 4, "LS": 4, "ME": 4, "N": 4, "NP": 4, "NR": 4, "NW": 4, "PO": 4, "RG": 4, "SE": 4,
    "SO": 4, "SS": 4, "SW": 4, "W": 4, "WC": 4, "YO": 4,
    "BH": 5, "CA": 5, "DH": 5, "DT": 5, "EX": 5, "LA": 5, "LL": 5, "NE": 5, "PL": 5, "SA": 5,
    "SR": 5, "TQ": 5, "TR": 5, "TS": 5,
    "AB": 6, "BT": 6, "DD": 6, "EH": 6, "FK": 6, "G": 6, "HS": 6, "IV": 6, "KW": 6, "KY": 6,
    "PA": 6, "PH": 6, "ZE": 6,
}

# Base postage in pence: per service, weight bands as (up to grams, prices for zones 1 to 6).
BASE_RATES = {
    "economy": (
        (1000, (330, 350, 375, 410, 450, 505)),
        (2000, (375, 400, 430, 470, 510, 575)),
        (5000, (465, 495, 535, 585, 640, 715)),
        (10000, (600, 640, 695, 760, 825, 920)),
        (20000, (815, 870, 945, 1035, 1125, 1255)),
        (30000, (1070, 1145, 1240, 1355, 1475, 1645)),
    ),
    "ground": (
        (1000, (395, 420, 450, 495, 540, 610)),
        (2000, (450, 480, 520, 565, 615, 690)),
        (5000, (560, 600, 650, 710, 770, 860)),
        (10000, (720, 775, 840, 915, 995, 1110)),
        (20000, (980, 1055, 1145, 1250, 1360, 1515)),
        (30000, (1290, 1385, 1500, 1640, 1785, 1990)),
    ),
    "express": (
        (1000, (695, 740, 790, 850, 920, 1040)),
        (2000, (790, 840, 900, 970, 1050, 1185)),
        (5000, (980, 1045, 1120, 1210, 1310, 1475)),
        (10000, (1260, 1345, 1440, 1555, 1685, 1895)),
        (20000, (1715, 1830, 1960, 2120, 2295, 2580)),
        (30000, (2260, 2410, 2585, 2795, 3025, 3400)),
    ),
}

# Pence per started kilogram of billable weight above the top band.
EXTRA_KG_PENCE = {
    "economy": 38,
    "ground": 45,
    "express": 80,
}
