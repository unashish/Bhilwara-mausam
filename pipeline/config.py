"""Settings for the Bhilwara forecast: tehsils, thresholds and data choices.

To add or move a tehsil, edit TEHSILS below. `lat`/`lon` is the point the
forecast is read at (the tehsil's centre). `row`/`col` is where its box sits in
the 4-column grid on the website (row 1 = north, col 1 = west).
"""

# Tehsil centres: area centroids of the 2011 sub-district boundaries, except
# Bijoliya (town location). Hindi names are what farmers see.
TEHSILS = [
    {"id": "asind",      "hi": "आसींद",     "en": "Asind",      "lat": 25.721, "lon": 74.360, "row": 1, "col": 1},
    {"id": "hurda",      "hi": "हुरड़ा",     "en": "Hurda (Gulabpura)", "lat": 25.812, "lon": 74.586, "row": 1, "col": 2},
    {"id": "shahpura",   "hi": "शाहपुरा",    "en": "Shahpura",   "lat": 25.690, "lon": 74.901, "row": 1, "col": 3},
    {"id": "mandal",     "hi": "मांडल",      "en": "Mandal",     "lat": 25.503, "lon": 74.301, "row": 2, "col": 1},
    {"id": "banera",     "hi": "बनेड़ा",     "en": "Banera",     "lat": 25.585, "lon": 74.674, "row": 2, "col": 2},
    {"id": "jahazpur",   "hi": "जहाजपुर",    "en": "Jahazpur",   "lat": 25.584, "lon": 75.248, "row": 2, "col": 4},
    {"id": "raipur",     "hi": "रायपुर",     "en": "Raipur",     "lat": 25.355, "lon": 74.166, "row": 3, "col": 1},
    {"id": "bhilwara",   "hi": "भीलवाड़ा",   "en": "Bhilwara",   "lat": 25.300, "lon": 74.612, "row": 3, "col": 2},
    {"id": "kotri",      "hi": "कोटड़ी",     "en": "Kotri",      "lat": 25.371, "lon": 74.953, "row": 3, "col": 3},
    {"id": "sahara",     "hi": "सहाड़ा",     "en": "Sahara (Gangapur)", "lat": 25.201, "lon": 74.249, "row": 4, "col": 1},
    {"id": "mandalgarh", "hi": "मांडलगढ़",   "en": "Mandalgarh", "lat": 25.202, "lon": 75.227, "row": 4, "col": 3},
    {"id": "bijoliya",   "hi": "बिजौलिया",   "en": "Bijoliya",   "lat": 25.160, "lon": 75.330, "row": 4, "col": 4},
]

DISTRICT_HI = "भीलवाड़ा"

# Area cut out of the global files (a little wider than the district).
BBOX = {"north": 26.25, "south": 24.75, "west": 73.75, "east": 75.75}

# Number of days shown (today + 6).
N_DAYS = 7

# India Standard Time is UTC+5:30. A "day" on the site runs from midnight to
# midnight IST, which we approximate with the 18 UTC model steps (23:30 IST).
IST_OFFSET_MIN = 330
DAY_BOUNDARY_UTC_HOUR = 18

# --- Rain rules -------------------------------------------------------------
# A member counts as "rain" if its daily total is at least this (IMD rainy day).
RAINY_DAY_MM = 2.5
# Box is green ("हाँ") when this share of the 51 members or more say rain.
YES_THRESHOLD_PCT = 50

# IMD 24-hour rainfall categories (mm, lower bound) and their Hindi words.
RAIN_CATEGORIES = [
    (0.0,   "सूखा"),
    (0.1,   "बूँदाबाँदी"),
    (2.5,   "हल्की बारिश"),
    (15.6,  "मध्यम बारिश"),
    (64.5,  "भारी बारिश"),
    (115.6, "बहुत भारी बारिश"),
    (204.5, "अत्यधिक भारी बारिश"),
]

# --- Warning rules (our own estimate, not official IMD warnings) ------------
HEAVY_RAIN_MM = 64.5          # heavy rain
HEAVY_RAIN_ALERT_PCT = 30     # warn if this share of members exceed it
HEAT_C = 40.0                 # day temperature at or above -> heat warning
SEVERE_HEAT_C = 45.0
COLD_NIGHT_C = 5.0            # night temperature at or below -> cold warning
FROST_C = 2.0                 # -> frost (पाला) warning
STRONG_WIND_KMH = 40.0        # 10 m wind speed at or above -> wind warning

ATTRIBUTION = (
    "Adapted from ECMWF IFS ensemble and high-resolution forecast open data "
    "by ECMWF, licensed under CC BY 4.0 (https://data.ecmwf.int/forecasts/). "
    "Processed into tehsil summaries; warnings are our own estimate, not "
    "official IMD warnings."
)
