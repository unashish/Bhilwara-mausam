"""Turn the downloaded GRIB files into docs/forecast.json for the website."""

import datetime as dt
import json
from pathlib import Path

import numpy as np

from . import config, hindi
from .gribread import by_param, read_points

IST = dt.timezone(dt.timedelta(minutes=config.IST_OFFSET_MIN))


def rain_word(mm):
    word = config.RAIN_CATEGORIES[0][1]
    for lower, name in config.RAIN_CATEGORIES:
        if mm >= lower:
            word = name
    return word


def accumulated(series, step):
    """Accumulated value at `step`; zero at the start of the forecast."""
    if step == 0:
        return 0.0
    return series[step]


def ensemble_daily_rain(tp_tree, b0, b1):
    """Array [members, points] of rain (mm) between steps b0 and b1."""
    members = sorted(tp_tree)
    rows = []
    for m in members:
        s = tp_tree[m]
        if b1 not in s or (b0 != 0 and b0 not in s):
            continue
        rows.append(accumulated(s, b1) - accumulated(s, b0))
    if not rows:
        raise ValueError(f"no ensemble rain for steps {b0}-{b1}")
    return np.clip(np.array(rows), 0.0, None)


def round5(pct):
    return int(5 * round(pct / 5.0))


def rain_timing(hres_tp, run, b0, b1, k):
    """Return Hindi text for the ~6 hour window with most rain, or None."""
    steps = sorted(s for s in hres_tp if b0 <= s <= b1)
    if b0 == 0 and 0 not in steps:
        steps = [0] + steps
    if len(steps) < 2:
        return None
    def acc(s):
        return 0.0 if s == 0 else float(hres_tp[s][k])

    pieces = []  # (start_step, end_step, mm)
    for a, b in zip(steps, steps[1:]):
        mm = acc(b) - acc(a)
        pieces.append((a, b, max(mm, 0.0)))
    best = None
    for i in range(len(pieces)):
        a = pieces[i][0]
        j, total = i, 0.0
        while j < len(pieces) and pieces[j][1] - a <= 6:
            total += pieces[j][2]
            j += 1
        if j == i:
            continue
        if best is None or total > best[2]:
            best = (a, pieces[j - 1][1], total)
    if best is None or best[2] < 0.5:
        return None
    def ist_hour(step):
        t = (run + dt.timedelta(hours=step)).astimezone(IST)
        return int(t.hour + t.minute / 60 + 0.5) % 24

    return hindi.time_window(ist_hour(best[0]), ist_hour(best[1]))


def build(raw_dir, now=None):
    raw = Path(raw_dir)
    meta = json.loads((raw / "run.json").read_text())
    run = dt.datetime.fromisoformat(meta["run"])
    bounds = meta["day_boundaries"]
    now = now or dt.datetime.now(dt.timezone.utc)

    points = [(t["lat"], t["lon"]) for t in config.TEHSILS]
    ens = by_param(read_points(str(raw / "ens_tp.grib2"), points))
    hres = by_param(read_points(str(raw / "hres.grib2"), points))
    ens_tp = ens["tp"]
    h_tp = hres["tp"][0]
    h_t2 = hres["2t"][0]
    h_u = hres["10u"][0]
    h_v = hres["10v"][0]

    days = []
    per_day = []  # computed arrays per day
    for d in range(config.N_DAYS):
        b0, b1 = bounds[d], bounds[d + 1]
        end_ist = (run + dt.timedelta(hours=b1)).astimezone(IST)
        date = end_ist.date()
        days.append({
            "date": date.isoformat(),
            "weekday": hindi.WEEKDAYS[date.weekday()],
            "weekday_short": hindi.WEEKDAYS_SHORT[date.weekday()],
            "date_short": hindi.date_short(date),
            "partial": b0 == 0,
        })
        daily = ensemble_daily_rain(ens_tp, b0, b1)
        steps = [s for s in sorted(h_t2) if b0 <= s <= b1]
        temps = np.array([h_t2[s] for s in steps])
        wind = np.array([np.hypot(h_u[s], h_v[s]) for s in steps]) * 3.6
        per_day.append((b0, b1, daily, temps, wind))

    tehsils = []
    for k, t in enumerate(config.TEHSILS):
        out_days = []
        for d, (b0, b1, daily, temps, wind) in enumerate(per_day):
            vals = daily[:, k]
            n = len(vals)
            wet = vals[vals >= config.RAINY_DAY_MM]
            chance = round5(100.0 * len(wet) / n)
            rain = chance >= config.YES_THRESHOLD_PCT
            item = {
                "rain": bool(rain),
                "chance": chance,
                "tmax": int(round(float(temps[:, k].max()))) if len(temps) else None,
                "tmin": int(round(float(temps[:, k].min()))) if len(temps) else None,
                "wind_kmh": int(round(float(wind[:, k].max()))) if len(wind) else None,
                "alerts": [],
            }
            if len(wet):
                median = float(np.median(wet))
                lo, hi = np.percentile(wet, [25, 75])
                item["amount_mm"] = round(median, 1)
                item["amount_word"] = rain_word(median)
                item["amount_text"] = hindi.amount_range(lo, hi)
            if rain and d <= 2:
                when = rain_timing(h_tp, run, b0, b1, k)
                if when:
                    item["when"] = when

            p_heavy = 100.0 * np.mean(vals >= config.HEAVY_RAIN_MM)
            p_vheavy = 100.0 * np.mean(vals >= 115.6)
            keys = []
            if p_vheavy >= config.HEAVY_RAIN_ALERT_PCT:
                keys.append("very_heavy_rain")
            elif p_heavy >= config.HEAVY_RAIN_ALERT_PCT:
                keys.append("heavy_rain")
            if item["tmax"] is not None:
                if item["tmax"] >= config.SEVERE_HEAT_C:
                    keys.append("severe_heat")
                elif item["tmax"] >= config.HEAT_C:
                    keys.append("heat")
                if item["tmin"] <= config.FROST_C:
                    keys.append("frost")
                elif item["tmin"] <= config.COLD_NIGHT_C:
                    keys.append("cold")
            if item["wind_kmh"] is not None and item["wind_kmh"] >= config.STRONG_WIND_KMH:
                keys.append("wind")
            for key in keys:
                title, advice = hindi.ALERTS[key]
                item["alerts"].append({"key": key, "title": title, "advice": advice})
            item["speech"] = hindi.speech(t["hi"], days[d]["weekday"], item)
            out_days.append(item)
        tehsils.append({
            "id": t["id"], "name": t["hi"], "name_en": t["en"],
            "lat": t["lat"], "lon": t["lon"], "row": t["row"], "col": t["col"],
            "days": out_days,
        })

    now_ist = now.astimezone(IST)
    return {
        "district": config.DISTRICT_HI,
        "updated": now.isoformat(timespec="minutes"),
        "updated_text": hindi.updated_text(now_ist),
        "model_run": run.isoformat(timespec="minutes"),
        "model": "ECMWF IFS (ENS 51 सदस्य + HRES)",
        "rules": {
            "rainy_day_mm": config.RAINY_DAY_MM,
            "yes_threshold_pct": config.YES_THRESHOLD_PCT,
        },
        "attribution": config.ATTRIBUTION,
        "official_note": hindi.OFFICIAL_NOTE,
        "days": days,
        "tehsils": tehsils,
    }


def write(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
