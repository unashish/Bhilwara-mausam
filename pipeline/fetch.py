"""Download the ECMWF IFS open data needed for the Bhilwara forecast.

Two downloads per run:
  * ensemble (51 members): total rain at each day boundary -> rain chance
  * high-resolution run: temperature, wind and rain every 3-6 hours
    -> day/night temperature, wind warning and the time of day rain falls

Only the 00 and 12 UTC runs are used because they reach 15 days; the 06/18
UTC ensemble runs stop earlier than the 7 days we show.
"""

import datetime as dt
import json
import logging
from pathlib import Path

from ecmwf.opendata import Client

from . import config

log = logging.getLogger(__name__)

SOURCES = ["ecmwf", "aws", "azure"]


def day_boundaries(run_hour):
    """Model steps (hours) at each IST day boundary for a run at `run_hour` UTC.

    The first boundary is 'now' for a 00 UTC run (today is partly over) or the
    18 UTC step for a 12 UTC run.
    """
    first = (config.DAY_BOUNDARY_UTC_HOUR - run_hour) % 24
    steps = [first + 24 * k for k in range(config.N_DAYS + 1)]
    if run_hour == 0:
        steps = [0] + steps[: config.N_DAYS]
    return steps


def hres_steps(max_step):
    steps = list(range(0, min(max_step, 144) + 1, 3))
    steps += list(range(150, max_step + 1, 6))
    return steps


def find_latest_run(client):
    """Newest 00/12 UTC run whose last needed ensemble step is published."""
    best = None
    for hour in (0, 12):
        last = day_boundaries(hour)[-1]
        try:
            when = client.latest(stream="enfo", type="pf", step=last, param="tp", time=hour)
        except Exception as exc:  # noqa: BLE001 - try the other run hour
            log.warning("no %02dz run found: %s", hour, exc)
            continue
        if best is None or when > best:
            best = when
    if best is None:
        raise RuntimeError("Could not find a recent ECMWF 00/12 UTC run")
    return best


def fetch(outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    errors = []
    for source in SOURCES:
        try:
            client = Client(source=source, model="ifs", resol="0p25")
            run = find_latest_run(client)
            log.info("using %s run %s", source, run.isoformat())
            bounds = day_boundaries(run.hour)
            ens_steps = [s for s in bounds if s > 0]
            client.retrieve(
                date=run.strftime("%Y%m%d"), time=run.hour, stream="enfo",
                type=["cf", "pf"], step=ens_steps, param="tp",
                target=str(outdir / "ens_tp.grib2"),
            )
            client.retrieve(
                date=run.strftime("%Y%m%d"), time=run.hour, stream="oper",
                type="fc", step=hres_steps(bounds[-1]),
                param=["2t", "10u", "10v", "tp"],
                target=str(outdir / "hres.grib2"),
            )
            meta = {"run": run.replace(tzinfo=dt.timezone.utc).isoformat(),
                    "source": source, "day_boundaries": bounds}
            (outdir / "run.json").write_text(json.dumps(meta))
            return meta
        except Exception as exc:  # noqa: BLE001 - fall back to a mirror
            log.warning("source %s failed: %s", source, exc)
            errors.append(f"{source}: {exc}")
    raise RuntimeError("All ECMWF sources failed: " + " | ".join(errors))
