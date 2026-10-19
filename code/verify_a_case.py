"""Compare what the coupler received in the MESACLIP A case with the GDEX source.

usage: python verify_a_case.py RUNDIR

Reads the coupler's auxiliary history (`atm6h`, `ocn1d`), which the case turns on with
`histaux_*` lines in its user_nl_cpl (see ~/croc_cases/mesaclip_a_hist/user_nl_cpl).
Hard-coded for HIST member 010, starting 1950-01-01.
"""

import glob
import sys

import netCDF4
import numpy as np

RUN = sys.argv[1]
CASE = "b.e13.BHISTC5.ne120_t12.cesm-ihesp-hires1.0.46-1920-2005.010"
GDEX = f"/glade/campaign/collections/gdex/data/d651007/{CASE}"
RHOFW, RDAIR, CPDAIR = 1000.0, 287.04213, 1004.64  # shr_const values (approx; reported diffs are relative)
VIS = 0.28 / 0.59


def cam(hist, var, day):
    """CAM field at model day `day` (days since 1920-01-01), from the 1950 file."""
    f = glob.glob(f"{GDEX}/atm/proc/tseries/hour_6/{CASE}.cam.{hist}.{var}.1950010100-*.nc")[0]
    d = netCDF4.Dataset(f)
    i = int(np.argmin(np.abs(d["time"][:] - day)))
    assert abs(d["time"][i] - day) < 1e-6, (var, day, d["time"][i])
    return np.asarray(d[var][i], dtype=np.float64).ravel()


def pop(var, day):
    f = sorted(glob.glob(f"{GDEX}/ocn/proc/tseries/day_1/{CASE}.pop.h.nday1.{var}.1950*.nc"))[0]
    d = netCDF4.Dataset(f)
    d.set_auto_mask(False)
    t = d["time"][:] - 711750 + 10950  # days since 0000-01-01 -> days since 1920-01-01
    i = int(np.argmin(np.abs(t - day)))
    assert abs(t[i] - day) < 1e-6, (var, day, t[i])
    return np.asarray(d[var][i], dtype=np.float64).ravel()


def rel(a, b, mask=None):
    m = np.isfinite(b) if mask is None else mask & np.isfinite(b)
    return np.max(np.abs(a[m] - b[m])) / max(np.max(np.abs(b[m])), 1e-30)


def report(name, got, candidates, mask=None):
    """Print the best-matching candidate (label, array) and its max relative diff."""
    errs = [(rel(got, ref, mask), label) for label, ref in candidates]
    err, label = min(errs)
    flag = "OK " if err < 1e-5 else "BAD"
    print(f"  {flag} {name:12s} max rel diff {err:.1e}  vs {label}")


# ---- atmosphere: every 6 h, instantaneous
f = sorted(glob.glob(f"{RUN}/*atm6h*.nc"))[0]
d = netCDF4.Dataset(f)
times = d["time"][:]
units = d["time"].units
print(f"atm aux file {f.split('/')[-1]}: {len(times)} times, {units}")
base = netCDF4.date2num(netCDF4.num2date(0, units, "noleap"), "days since 1920-01-01", "noleap")
for k in [0, len(times) // 2]:
    day = base + times[k]
    print(f"time {netCDF4.num2date(times[k], units, 'noleap')}  (day {day:.2f} since 1920)")
    g = lambda fld: np.asarray(d[f"atmImp_{fld}"][k], dtype=np.float64).ravel()
    T, q, p = cam("h2", "TREFHT", day), cam("h2", "QREFHT", day), cam("h2", "PS", day)
    for fld, var in [("Sa_u", "UBOT"), ("Sa_v", "VBOT"), ("Sa_z", "ZBOT"), ("Sa_pslv", "PSL"),
                     ("Sa_tbot", "TREFHT"), ("Sa_shum", "QREFHT"), ("Sa_pbot", "PS")]:
        report(fld, g(fld), [(f"h2 {var}", cam("h2", var, day))])
    report("Sa_ptem", g("Sa_ptem"), [("T(1e5/p)^(R/cp)", T * (1e5 / p) ** (RDAIR / CPDAIR))])
    report("Sa_dens", g("Sa_dens"), [("p/(R T (1+0.608q))", p / (RDAIR * T * (1 + 0.608 * q)))])
    # h4 means: window ending at `day` or at `day + 0.25` (nearest-rule tie at window edges)
    for fld, fn in [
        ("Faxa_lwdn", lambda w: cam("h4", "FLDS", w)),
        ("Faxa_swvdf", lambda w: cam("h4", "SOLSD", w)),
        ("Faxa_swndf", lambda w: cam("h4", "SOLLD", w)),
        ("Faxa_swvdr", lambda w: np.maximum(0, cam("h4", "FSDS", w) - cam("h4", "SOLSD", w) - cam("h4", "SOLLD", w)) * VIS),
        ("Faxa_swndr", lambda w: np.maximum(0, cam("h4", "FSDS", w) - cam("h4", "SOLSD", w) - cam("h4", "SOLLD", w)) * (1 - VIS)),
        ("Faxa_rainc", lambda w: np.maximum(0, cam("h4", "PRECC", w) - cam("h4", "PRECSC", w)) * RHOFW),
        ("Faxa_rainl", lambda w: np.maximum(0, cam("h4", "PRECT", w) - cam("h4", "PRECC", w) - cam("h4", "PRECSL", w)) * RHOFW),
        ("Faxa_snowc", lambda w: cam("h4", "PRECSC", w) * RHOFW),
        ("Faxa_snowl", lambda w: cam("h4", "PRECSL", w) * RHOFW),
    ]:
        cands = [(f"h4 mean ending {w - day:+.2f} d", fn(w)) for w in (day, day + 0.25) if w > 10950]
        report(fld, g(fld), cands)

# ---- ocean: daily, instantaneous at 00Z
f = sorted(glob.glob(f"{RUN}/*ocn1d*.nc"))[0]
d = netCDF4.Dataset(f)
times = d["time"][:]
units = d["time"].units
print(f"\nocn aux file {f.split('/')[-1]}: {len(times)} times, {units}")
for k in [1, len(times) - 1]:
    day = base + times[k]
    print(f"time {netCDF4.num2date(times[k], units, 'noleap')}  (day {day:.2f} since 1920)")
    sst_prev, sst_next = pop("SST", day), pop("SST", day + 1)
    # POP land points hold -1, not a fill value, so use POP's own land mask (KMT)
    grid = netCDF4.Dataset(glob.glob(f"{GDEX}/ocn/proc/tseries/day_1/{CASE}.pop.h.nday1.SST.1950*.nc")[0])
    ocean = np.asarray(grid["KMT"][:]).ravel() > 0
    g = lambda fld: np.asarray(d[f"ocnImp_{fld}"][k], dtype=np.float64).ravel()
    report("So_t", g("So_t"), [("SST+273.15, day ending", sst_prev + 273.15), ("SST+273.15, next day", sst_next + 273.15)], ocean)
    for fld, var in [("So_u", "U1_1"), ("So_v", "V1_1")]:
        report(fld, g(fld), [(f"{var}*0.01, day ending", pop(var, day) * 0.01), (f"{var}*0.01, next day", pop(var, day + 1) * 0.01)], ocean)
