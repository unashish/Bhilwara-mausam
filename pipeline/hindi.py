"""All Hindi words used on the site, in one place so they are easy to change."""

WEEKDAYS = ["सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]
WEEKDAYS_SHORT = ["सोम", "मंगल", "बुध", "गुरु", "शुक्र", "शनि", "रवि"]
MONTHS = ["जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई",
          "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]
MONTHS_SHORT = ["जन", "फ़र", "मार्च", "अप्रै", "मई", "जून", "जुला",
                "अग", "सितं", "अक्टू", "नवं", "दिसं"]

YES = "हाँ"
NO = "नहीं"


def day_label(index, date):
    if index == 0:
        return "आज"
    if index == 1:
        return "कल"
    return WEEKDAYS_SHORT[date.weekday()]


def date_short(date):
    return f"{date.day} {MONTHS_SHORT[date.month - 1]}"


def date_long(date):
    return f"{WEEKDAYS[date.weekday()]}, {date.day} {MONTHS[date.month - 1]}"


def clock(hour):
    """Hour (0-23, IST) as a simple spoken time, e.g. 'दोपहर 2 बजे'."""
    if 4 <= hour < 12:
        part = "सुबह"
    elif 12 <= hour < 16:
        part = "दोपहर"
    elif 16 <= hour < 19:
        part = "शाम"
    else:
        part = "रात"
    h12 = hour % 12 or 12
    return f"{part} {h12} बजे"


def time_window(start_hour, end_hour):
    """e.g. 'दोपहर 2 से शाम 6 बजे तक'."""
    a = clock(start_hour).replace(" बजे", "")
    return f"{a} से {clock(end_hour)} तक"


def amount_range(lo, hi):
    lo, hi = int(round(lo)), int(round(hi))
    if hi <= 1:
        return "1 मिमी से कम"
    if lo == hi or lo <= 0:
        return f"लगभग {hi} मिमी"
    return f"{lo}–{hi} मिमी"


def updated_text(dt_ist):
    return f"{date_long(dt_ist)} · {clock(dt_ist.hour)} अपडेट"


ALERTS = {
    "heavy_rain": ("भारी बारिश हो सकती है",
                   "नदी-नाले पार न करें। कटी फसल और अनाज ढककर रखें।"),
    "very_heavy_rain": ("बहुत भारी बारिश का खतरा",
                        "निचले इलाकों से दूर रहें। पशुओं को ऊँची जगह बाँधें।"),
    "heat": ("तेज़ गर्मी",
             "दोपहर में धूप में काम न करें। पानी ज़्यादा पिएँ, पशुओं को छाँव दें।"),
    "severe_heat": ("लू का खतरा",
                    "दोपहर 12 से 4 बजे बाहर न निकलें। पशुओं को पानी और छाँव दें।"),
    "cold": ("ठंडी रात",
             "छोटे पौधों और पशुओं को ठंड से बचाएँ।"),
    "frost": ("पाला पड़ सकता है",
              "शाम को हल्की सिंचाई करें, खेत की मेड़ पर धुआँ करें।"),
    "wind": ("तेज़ हवा",
             "कच्ची छत और टीन बाँधकर रखें। ऊँचे पेड़ों के नीचे न रुकें।"),
}

OFFICIAL_NOTE = "यह हमारा अनुमान है। सरकारी चेतावनी के लिए मौसम विभाग (IMD) देखें।"


def speech(tehsil_hi, day_name, d):
    """One short paragraph the phone reads aloud for a tehsil and day."""
    parts = [f"{tehsil_hi}, {day_name}।"]
    if d["rain"]:
        parts.append(f"बारिश होगी। मौका {d['chance']} प्रतिशत।")
        if d.get("amount_word"):
            parts.append(f"{d['amount_word']}, {d['amount_text']}।")
        if d.get("when"):
            parts.append(f"{d['when']}।")
    else:
        parts.append(f"बारिश नहीं होगी। मौका सिर्फ़ {d['chance']} प्रतिशत।")
    if d.get("tmax") is not None:
        parts.append(f"दिन में {d['tmax']} डिग्री, रात में {d['tmin']} डिग्री।")
    for a in d.get("alerts", []):
        parts.append(f"सावधान, {a['title']}। {a['advice']}")
    return " ".join(parts)
