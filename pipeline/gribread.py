"""Read ECMWF GRIB files and pull values at the tehsil points.

Every message in a file is one field (one parameter, one ensemble member, one
forecast step) on a regular lat/lon grid. We read it, bilinearly interpolate to
each tehsil centre, and throw the global field away, so memory stays small even
for hundreds of ensemble fields.
"""

from collections import defaultdict

import eccodes
import numpy as np


class PointSampler:
    """Bilinear interpolation weights for fixed points on one regular grid."""

    def __init__(self, gid, points):
        ni = eccodes.codes_get(gid, "Ni")
        nj = eccodes.codes_get(gid, "Nj")
        lat0 = eccodes.codes_get(gid, "latitudeOfFirstGridPointInDegrees")
        lon0 = eccodes.codes_get(gid, "longitudeOfFirstGridPointInDegrees")
        dlon = eccodes.codes_get(gid, "iDirectionIncrementInDegrees")
        dlat = eccodes.codes_get(gid, "jDirectionIncrementInDegrees")
        if eccodes.codes_get(gid, "jScansPositively") == 0:
            dlat = -dlat
        self.key = (ni, nj, lat0, lon0, dlon, dlat)
        self.shape = (nj, ni)

        idx, wts = [], []
        for lat, lon in points:
            fj = (lat - lat0) / dlat
            fi = ((lon - lon0) % 360.0) / dlon
            j0, i0 = int(np.floor(fj)), int(np.floor(fi))
            tj, ti = fj - j0, fi - i0
            j1, i1 = min(j0 + 1, nj - 1), (i0 + 1) % ni
            idx.append([(j0, i0), (j0, i1), (j1, i0), (j1, i1)])
            wts.append([(1 - tj) * (1 - ti), (1 - tj) * ti, tj * (1 - ti), tj * ti])
        self.idx = idx
        self.wts = np.array(wts)

    def sample(self, values):
        grid = values.reshape(self.shape)
        out = np.empty(len(self.idx))
        for k, corners in enumerate(self.idx):
            out[k] = sum(w * grid[j, i] for w, (j, i) in zip(self.wts[k], corners))
        return out


def to_standard_units(gid, name, values):
    """Rain -> mm, temperature -> deg C, wind stays m/s."""
    units = eccodes.codes_get(gid, "units")
    if name == "tp" and units == "m":
        return values * 1000.0          # metres of water -> mm
    if name == "2t" and units == "K":
        return values - 273.15
    return values                       # tp in kg m**-2 is already mm


def read_points(paths, points):
    """Return {(shortName, member, step_hours): np.array of values per point}.

    `member` is 0 for the control / high-resolution run and 1..50 for the
    perturbed ensemble members. `points` is a list of (lat, lon).
    """
    if isinstance(paths, str):
        paths = [paths]
    out = {}
    samplers = {}
    for path in paths:
        with open(path, "rb") as f:
            while True:
                gid = eccodes.codes_grib_new_from_file(f)
                if gid is None:
                    break
                try:
                    name = eccodes.codes_get(gid, "shortName")
                    try:
                        member = int(eccodes.codes_get(gid, "number"))
                    except eccodes.KeyValueNotFoundError:
                        member = 0
                    step = int(eccodes.codes_get(gid, "endStep"))
                    sampler = PointSampler(gid, points)
                    sampler = samplers.setdefault(sampler.key, sampler)
                    values = sampler.sample(eccodes.codes_get_values(gid))
                    out[(name, member, step)] = to_standard_units(gid, name, values)
                finally:
                    eccodes.codes_release(gid)
    return out


def by_param(fields):
    """Group read_points output as {name: {member: {step: values}}}."""
    tree = defaultdict(lambda: defaultdict(dict))
    for (name, member, step), vals in fields.items():
        tree[name][member][step] = vals
    return tree
