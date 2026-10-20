"""
Print every variable available in MESACLIP GDEX for a given member,
grouped by component and frequency.  One file per variable, so we
just list the unique variable names from the directory contents.

Usage:
    python code/list_mesaclip_variables.py
    python code/list_mesaclip_variables.py --case b.e13.BHISTC5.ne120_t12.cesm-ihesp-hires1.0.46-1920-2005.003
"""

import argparse
from pathlib import Path
import netCDF4 as nc

GDEX = Path("/glade/campaign/collections/gdex/data/d651007")

DEFAULT_CASE = (
    "b.e13.BHISTC5.ne120_t12.cesm-ihesp-hires1.0.46-1920-2005.010"
)

STREAMS = [
    ("cam.h2",  "atm/proc/tseries/hour_6",   "6-hourly ATM (instantaneous)"),
    ("cam.h4",  "atm/proc/tseries/hour_6",    "6-hourly ATM (means)"),
    ("pop.h.nday1", "ocn/proc/tseries/day_1", "daily OCN"),
    ("cice.h1", "ice/proc/tseries/day_1",     "daily ICE"),
]


def list_vars(case: str) -> None:
    case_dir = GDEX / case
    print(f"Case: {case}\n")

    for tag, subdir, label in STREAMS:
        d = case_dir / subdir
        if not d.exists():
            print(f"  [{label}]  directory not found: {d}\n")
            continue

        # variable name is between the tag and the date range in the filename
        # e.g. <case>.<tag>.<VARNAME>.<dates>.nc
        prefix = f"{case}.{tag}."
        names = set()
        for f in d.iterdir():
            stem = f.stem  # strip .nc
            if stem.startswith(prefix):
                rest = stem[len(prefix):]          # VARNAME.dates
                varname = rest.rsplit(".", 1)[0]    # drop dates
                names.add(varname)

        print(f"  [{label}]  {len(names)} variables:")
        for v in sorted(names):
            print(f"    {v}")

        # peek at one file to get units and long_name
        if names:
            sample_var = sorted(names)[0]
            files = sorted(d.glob(f"{prefix}{sample_var}.*.nc"))
            if files:
                with nc.Dataset(files[0]) as ds:
                    grid = getattr(ds, "ne", None) or getattr(ds, "title", "")
                    print(f"\n  Grid info from first {tag} file:")
                    for attr in ("ne", "nlat", "nlon", "title", "source", "case"):
                        val = getattr(ds, attr, None)
                        if val:
                            print(f"    {attr}: {val}")
        print()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--case", default=DEFAULT_CASE)
    args = p.parse_args()
    list_vars(args.case)


if __name__ == "__main__":
    main()
