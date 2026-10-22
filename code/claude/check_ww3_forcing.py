"""Check what WW3 took in against what the mediator sent it.

usage: python check_ww3_forcing.py CPL_HI WW3_HI

CPL_HI is the mediator history (`<case>.cpl.hi.<date>.nc`, `wavExp_*` fields) and WW3_HI the
WW3 history at the same time (`<case>.ww3.hi.<date>.nc`), with `CUR AST WLV ICE IC1 IC5` and
`WND` in WW3's `type%field%list`. Each WW3 field is compared with what it is built from; a field
that matches was used, one that stays at WW3's constant default (ice thickness 0.5 m, floe
diameter 1000 m, water level 0) while the coupler field varies was dropped.
"""

import sys

import netCDF4
import numpy as np

# WW3 history name: (description, function of the coupler fields)
PAIRS = {
    "UAX": ("wind east", lambda c: c["Sa_u10m"]),
    "UAY": ("wind north", lambda c: c["Sa_v10m"]),
    "CX": ("current east", lambda c: c["So_u"]),
    "CY": ("current north", lambda c: c["So_v"]),
    "ICE": ("ice fraction", lambda c: c["Si_ifrac"]),
    "AS": ("air - sea temperature", lambda c: c["Sa_tbot"] - c["So_t"]),
    "ICEH": ("ice thickness", lambda c: c["Si_thick"]),
    "ICEF": ("floe diameter", lambda c: c.get("Si_floediam")),
    "WLV": ("water level", lambda c: c.get("So_h")),
}


def read(path, prefix=""):
    d = netCDF4.Dataset(path)
    d.set_auto_mask(False)
    out = {}
    for name, var in d.variables.items():
        if name.startswith(prefix) and var.ndim == 3:
            v = np.asarray(var[-1], dtype=np.float64)
            fill = getattr(var, "_FillValue", 1e30)
            out[name[len(prefix):]] = np.where((np.abs(v) >= 1e29) | np.isclose(v, fill), np.nan, v)
    return out


cpl = read(sys.argv[1], "wavExp_")
ww3 = read(sys.argv[2])
print(f"{'WW3':5s} {'meaning':22s} {'WW3 min':>9s} {'WW3 max':>9s} {'coupler max':>11s} {'max diff':>9s}  verdict")
for name, (desc, f) in PAIRS.items():
    if name not in ww3:
        print(f"{name:5s} {desc:22s} not in WW3 history")
        continue
    w = ww3[name]
    ref = f(cpl)
    ok = np.isfinite(w)
    if ref is None:
        ref_max, diff = "not sent", np.nanmax(np.abs(w[ok]))
        verdict = "not sent (WW3 default)" if np.ptp(w[ok]) == 0 else "varies without a coupler field"
    else:
        ok &= np.isfinite(ref)
        ref_max = f"{np.max(np.abs(ref[ok])):.3g}"
        diff = np.max(np.abs(w[ok] - ref[ok]))
        if np.ptp(w[ok]) == 0 and np.ptp(ref[ok]) > 0:
            verdict = "DROPPED: WW3 keeps a constant"
        elif diff <= 1e-3 * max(np.max(np.abs(ref[ok])), 1e-12):
            verdict = "used, matches"
        else:
            verdict = "differs"
    print(f"{name:5s} {desc:22s} {np.nanmin(w):9.3g} {np.nanmax(w):9.3g} {ref_max:>11s} {diff:9.3g}  {verdict}")
