"""List what the mediator sends each model, from a coupler history file.

usage: python coupler_fields.py CPL_HI [CPL_HI_TEST]

CPL_HI is a mediator history file (`<case>.cpl.hi.<date>.nc`), written when the case
sets HIST_OPTION/HIST_N. Its `<comp>Exp_<field>` variables are what the mediator sends
to <comp>; `<comp>Imp_<field>` are what <comp> sends the mediator.

With one file, prints each model's received fields with min, max and the share of
points that are zero or >= 1e29 (CDEPS/shr spval). With two, prints the fields the
reference (first) file has and the test (second) file lacks, per model.
"""

import sys

import netCDF4
import numpy as np

COMPS = ("atm", "ocn", "ice", "wav")


def fields(path, kind="Exp"):
    """{comp: {field: values}} for `<comp><kind>_<field>` variables in `path`."""
    d = netCDF4.Dataset(path)
    d.set_auto_mask(False)
    out = {c: {} for c in COMPS}
    for name, var in d.variables.items():
        comp, _, fld = name.partition(f"{kind}_")
        if comp in out and fld and fld not in ("lon", "lat"):
            out[comp][fld] = np.asarray(var[:], dtype=np.float64).ravel()
    return out


def describe(path):
    for comp, flds in fields(path).items():
        if not flds:
            continue
        print(f"\n{comp}: {len(flds)} fields received")
        print(f"  {'field':24s} {'min':>11s} {'max':>11s} {'zero':>6s} {'spval':>6s}")
        for fld, v in sorted(flds.items()):
            spval = np.abs(v) >= 1e29
            ok = v[~spval & np.isfinite(v)]
            lo, hi = (ok.min(), ok.max()) if ok.size else (np.nan, np.nan)
            print(f"  {fld:24s} {lo:11.4g} {hi:11.4g} {np.mean(v == 0):6.0%} {np.mean(spval):6.0%}"
                  + ("  NaN" if np.isnan(v).any() else ""))


def compare(ref, test):
    r, t = fields(ref), fields(test)
    for comp in COMPS:
        if not r[comp]:
            continue
        missing = sorted(set(r[comp]) - set(t[comp]))
        extra = sorted(set(t[comp]) - set(r[comp]))
        print(f"\n{comp}: reference {len(r[comp])}, test {len(t[comp])}")
        print(f"  missing in test: {' '.join(missing) or 'none'}")
        if extra:
            print(f"  only in test:    {' '.join(extra)}")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        describe(sys.argv[1])
    else:
        compare(sys.argv[1], sys.argv[2])
