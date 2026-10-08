"""Daily job: download ECMWF data and write the website's forecast.json.

    python -m pipeline.run                     # download + build
    python -m pipeline.run --skip-fetch        # build from files in --raw
"""

import argparse
import logging

from . import fetch, process


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--raw", default="raw", help="folder for downloaded GRIB files")
    p.add_argument("--out", default="docs/forecast.json")
    p.add_argument("--skip-fetch", action="store_true")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if not args.skip_fetch:
        fetch.fetch(args.raw)
    data = process.build(args.raw)
    process.write(data, args.out)
    yes = sum(t["days"][0]["rain"] for t in data["tehsils"])
    logging.info("wrote %s (run %s): %d/%d tehsils rain on day 1",
                 args.out, data["model_run"], yes, len(data["tehsils"]))


if __name__ == "__main__":
    main()
