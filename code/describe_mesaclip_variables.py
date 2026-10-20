"""
Print all MESACLIP variables available in GDEX for a given member,
with units and long_name from the NetCDF metadata.

Usage:
    python code/describe_mesaclip_variables.py
    python code/describe_mesaclip_variables.py --case b.e13.BHISTC5.ne120_t12.cesm-ihesp-hires1.0.46-1920-2005.005
"""

import argparse
from pathlib import Path
import netCDF4 as nc

GDEX = Path("/glade/campaign/collections/gdex/data/d651007")

DEFAULT_CASE = (
    "b.e13.BHISTC5.ne120_t12.cesm-ihesp-hires1.0.46-1920-2005.010"
)

STREAMS = [
    ("cam.h2",      "atm/proc/tseries/hour_6", "6-hourly ATM instantaneous"),
    ("cam.h4",      "atm/proc/tseries/hour_6", "6-hourly ATM time means"),
    ("pop.h.nday1", "ocn/proc/tseries/day_1",  "daily OCN"),
    ("cice.h1",     "ice/proc/tseries/day_1",  "daily ICE"),
]


def describe_vars(case: str) -> None:
    case_dir = GDEX / case
    print(f"Case: {case}\n")

    for tag, subdir, label in STREAMS:
        d = case_dir / subdir
        if not d.exists():
            print(f"[{label}]  directory not found: {d}\n")
            continue

        prefix = f"{case}.{tag}."
        vars_found: dict[str, Path] = {}
        for f in d.iterdir():
            stem = f.stem
            if stem.startswith(prefix):
                varname = stem[len(prefix):].rsplit(".", 1)[0]
                if varname not in vars_found:
                    vars_found[varname] = f

        print(f"[{label}]  {len(vars_found)} variables:")
        print(f"  {'Variable':<20}  {'Units':<22}  Long name")
        print(f"  {'-'*20}  {'-'*22}  {'-'*50}")
        for v in sorted(vars_found):
            try:
                with nc.Dataset(vars_found[v]) as ds:
                    var = ds.variables.get(v)
                    units = getattr(var, "units", "?") if var is not None else "?"
                    longname = getattr(var, "long_name", "?") if var is not None else "?"
            except Exception:
                units, longname = "?", "?"
            print(f"  {v:<20}  {units:<22}  {longname}")
        print()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--case", default=DEFAULT_CASE,
                   help="MESACLIP case name (default: member 010 historical)")
    args = p.parse_args()
    describe_vars(args.case)


if __name__ == "__main__":
    main()
