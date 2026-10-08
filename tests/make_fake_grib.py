"""Write small fake ECMWF-like GRIB files to test the pipeline offline.

The fields cover only the Bhilwara area (not the globe) but use the same grid
spacing, parameters, member numbers and steps as the real open data. A rain
band moves from east to west over the first two days, and day 4 is hot.

    python -m tests.make_fake_grib raw_test
"""

import datetime as dt
import json
import sys
from pathlib import Path

import eccodes
import numpy as np

from pipeline import fetch

LAT_N, LAT_S, LON_W, LON_E, D = 27.0, 24.0, 73.0, 76.0, 0.25
LATS = np.arange(LAT_N, LAT_S - 1e-9, -D)
LONS = np.arange(LON_W, LON_E + 1e-9, D)
GLAT, GLON = np.meshgrid(LATS, LONS, indexing="ij")

PARAM_IDS = {"tp": 228, "2t": 167, "10u": 165, "10v": 166}


def new_field(name, member, step, values, ens):
    gid = eccodes.codes_grib_new_from_samples("regular_ll_sfc_grib2")
    eccodes.codes_set(gid, "Ni", len(LONS))
    eccodes.codes_set(gid, "Nj", len(LATS))
    eccodes.codes_set(gid, "latitudeOfFirstGridPointInDegrees", LAT_N)
    eccodes.codes_set(gid, "latitudeOfLastGridPointInDegrees", LATS[-1])
    eccodes.codes_set(gid, "longitudeOfFirstGridPointInDegrees", LON_W)
    eccodes.codes_set(gid, "longitudeOfLastGridPointInDegrees", LONS[-1])
    eccodes.codes_set(gid, "iDirectionIncrementInDegrees", D)
    eccodes.codes_set(gid, "jDirectionIncrementInDegrees", D)
    eccodes.codes_set(gid, "jScansPositively", 0)
    accum = name == "tp"
    if ens:
        eccodes.codes_set(gid, "productDefinitionTemplateNumber", 11 if accum else 1)
        eccodes.codes_set(gid, "typeOfEnsembleForecast", 3 if member else 1)
        eccodes.codes_set(gid, "numberOfForecastsInEnsemble", 51)
        eccodes.codes_set(gid, "perturbationNumber", member)
    elif accum:
        eccodes.codes_set(gid, "productDefinitionTemplateNumber", 8)
    eccodes.codes_set(gid, "paramId", PARAM_IDS[name])
    eccodes.codes_set(gid, "stepUnits", 1)
    if accum:
        eccodes.codes_set(gid, "stepRange", f"0-{step}")
    else:
        eccodes.codes_set(gid, "forecastTime", step)
    eccodes.codes_set_values(gid, values.ravel())
    return gid


def rain_rate(hours, member, rng):
    """mm per hour over the grid at `hours` after the run."""
    centre_lon = 75.8 - 0.035 * hours + rng.normal(0, 0.15)
    strength = max(0.0, rng.normal(1.0, 0.5))
    band = np.exp(-((GLON - centre_lon) / 0.35) ** 2)
    active = 1.0 if 4 <= hours <= 42 else 0.0
    return active * strength * 1.2 * band


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    run = dt.datetime(2026, 10, 7, 12, tzinfo=dt.timezone.utc)
    bounds = fetch.day_boundaries(run.hour)
    rng = np.random.default_rng(1)

    with open(out / "ens_tp.grib2", "wb") as f:
        for member in range(51):
            acc, last = np.zeros_like(GLAT), 0
            mrng = np.random.default_rng(100 + member)
            for step in [s for s in bounds if s > 0]:
                for h in range(last, step):
                    acc += rain_rate(h, member, mrng) / 1000.0
                last = step
                gid = new_field("tp", member, step, acc, ens=True)
                eccodes.codes_write(gid, f)
                eccodes.codes_release(gid)

    with open(out / "hres.grib2", "wb") as f:
        acc, last = np.zeros_like(GLAT), 0
        for step in fetch.hres_steps(bounds[-1]):
            for h in range(last, step):
                acc += rain_rate(h, 0, rng) / 1000.0
            last = step
            ist_hour = (run.hour + step + 5.5) % 24
            day = (step + 12 + 5.5) / 24
            heat = 6.0 if 3.0 <= day < 4.0 else 0.0
            t = 273.15 + 27 + heat + 7 * np.cos((ist_hour - 15) / 24 * 2 * np.pi) \
                - 1.5 * (GLAT - 25.5)
            for name, vals in (("tp", acc), ("2t", t),
                               ("10u", np.full_like(GLAT, 3.0)),
                               ("10v", np.full_like(GLAT, 2.0))):
                gid = new_field(name, 0, step, vals, ens=False)
                eccodes.codes_write(gid, f)
                eccodes.codes_release(gid)

    (out / "run.json").write_text(json.dumps({
        "run": run.isoformat(), "source": "fake", "day_boundaries": bounds}))
    print("fake data written to", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "raw_test")
