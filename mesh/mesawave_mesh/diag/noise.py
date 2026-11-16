"""Element-size scatter and 6-valent share: ours vs Ali's. usage: noise.py OURS_ptb.mat SIZEFX.nc [ALI.msh]"""
import sys
import numpy as np, scipy.io as sio, netCDF4, pandas as pd
from scipy.interpolate import RegularGridInterpolator

def read_msh(path):
    with open(path) as f:
        for line in f:
            if line.startswith("$Nodes"):
                nn = int(next(f)); break
    p = pd.read_csv(path, sep=r"\s+", skiprows=5, nrows=nn, header=None).values[:, 1:3]
    e = pd.read_csv(path, sep=r"\s+", skiprows=5 + nn + 3, header=None, usecols=[1, 6, 7, 8], comment="$").values
    t = e[e[:, 0] == 2, 1:].astype(np.int64) - 1
    return p.astype(float), t

def stats(p, t, name, sel=None):
    l, f = np.deg2rad(p[:, 0]), np.deg2rad(p[:, 1])
    x = np.c_[np.cos(f)*np.cos(l), np.cos(f)*np.sin(l), np.sin(f)] * 6371.0
    a, b, c = x[t[:, 0]], x[t[:, 1]], x[t[:, 2]]
    A = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    s = np.sqrt(4 * A / np.sqrt(3))  # nominal resolution
    n = len(p)
    k = np.bincount(t.ravel(), minlength=n).astype(float)
    m1 = np.bincount(t.ravel(), np.repeat(s, 3), minlength=n) / np.maximum(k, 1)
    m2 = np.bincount(t.ravel(), np.repeat(s**2, 3), minlength=n) / np.maximum(k, 1)
    cv = np.sqrt(np.maximum(m2 - m1**2, 0)) / m1
    e = np.sort(np.r_[t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]], axis=1)
    ue, cnt = np.unique(e, axis=0, return_counts=True)
    bnd = np.zeros(n, bool); bnd[ue[cnt == 1].ravel()] = True
    deg = np.bincount(ue.ravel(), minlength=n)
    ok = ~bnd & (k > 0) if sel is None else ~bnd & sel
    # triangle ratio to the mean of its 3 nodes' neighbourhoods
    r = s / m1[t].mean(axis=1)
    rt = r[ok[t].all(axis=1)]
    print(f"{name}: interior nodes {ok.sum():,}; degree 6: {np.mean(deg[ok]==6):.0%}, 5: {np.mean(deg[ok]==5):.0%}, "
          f"7: {np.mean(deg[ok]==7):.0%}, other {np.mean((deg[ok]<5)|(deg[ok]>7)):.1%}")
    print(f"   triangle size / local mean: p5 {np.percentile(rt,5):.2f} p50 {np.percentile(rt,50):.2f} p95 {np.percentile(rt,95):.2f}"
          f"   per-node CV of incident triangle sizes: median {np.median(cv[ok]):.3f}")
    return s, ok, t

d = sio.loadmat(sys.argv[1]); p, t = d["p"], d["t"].astype(np.int64) - 1
with netCDF4.Dataset(sys.argv[2]) as nc:
    F = RegularGridInterpolator((nc["lat"][:], nc["lon"][:]), np.asarray(nc["h"][:]) / 1e3, bounds_error=False, fill_value=None)
h = F(np.c_[p[:, 1], p[:, 0]])
stats(p, t, "ours, all")
s, ok, _ = stats(p, t, "ours, open ocean (target 25 km)", h >= 24.99)
so = s[(h[t] >= 24.99).all(axis=1)]
print(f"   open-ocean triangle nominal size km: p5 {np.percentile(so,5):.1f} p25 {np.percentile(so,25):.1f} "
      f"p50 {np.percentile(so,50):.1f} p75 {np.percentile(so,75):.1f} p95 {np.percentile(so,95):.1f}")
if len(sys.argv) > 3:
    pa, ta = read_msh(sys.argv[3])
    stats(pa, ta, "Ali wu025r004, all")
