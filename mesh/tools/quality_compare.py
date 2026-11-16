"""Triangle quality (1 = equilateral) by zone, and a map of the open-ocean triangles below a
threshold, for several ptb meshes. usage: quality_compare.py SIZEFX.nc OUT.png A_ptb.mat [B_ptb.mat ...]
"""
import sys

import netCDF4
import numpy as np
import scipy.io as sio
from scipy.interpolate import RegularGridInterpolator
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

with netCDF4.Dataset(sys.argv[1]) as nc:
    F = RegularGridInterpolator((nc["lat"][:], nc["lon"][:]), np.asarray(nc["h"][:]) / 1e3,
                                bounds_error=False, fill_value=None)
paths = sys.argv[3:]
fig, axs = plt.subplots(len(paths), 1, figsize=(14, 6.5 * len(paths)), constrained_layout=True)
for ax, path in zip(np.atleast_1d(axs), paths):
    d = sio.loadmat(path)
    p, t = d["p"], d["t"].astype(np.int64) - 1
    lo, la = np.deg2rad(p[:, 0]), np.deg2rad(p[:, 1])
    x = np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]
    a, b, c = x[t[:, 0]], x[t[:, 1]], x[t[:, 2]]
    A = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    s2 = (np.sum((b - a) ** 2, 1) + np.sum((c - b) ** 2, 1) + np.sum((a - c) ** 2, 1))
    q = 4 * np.sqrt(3) * A / s2
    cen = p[t].mean(axis=1)                    # fine away from the dateline
    tgt = F(np.c_[cen[:, 1], cen[:, 0]])
    name = path.split("/")[-1].replace("_ptb.mat", "")
    print(f"== {name}: {len(t):,} triangles, mean quality {q.mean():.4f}")
    for zn, m in [("open ocean (25 km)", tgt >= 24.99), ("everything else", tgt < 24.99)]:
        print(f"   {zn:20s} mean {q[m].mean():.4f}  p1 {np.percentile(q[m], 1):.3f}  "
              f"p5 {np.percentile(q[m], 5):.3f}  p50 {np.median(q[m]):.4f}  below 0.95: {np.mean(q[m] < 0.95):.2%}")
    low = (tgt >= 24.99) & (q < 0.97)
    ax.scatter(cen[low, 0], cen[low, 1], s=0.3, c=q[low], cmap="viridis", vmin=0.85, vmax=0.97, rasterized=True)
    ax.set_xlim(-180, 180); ax.set_ylim(-80, 90)
    ax.set_title(f"{name}: open-ocean triangles with quality < 0.97 ({low.sum():,})")
fig.savefig(sys.argv[2], dpi=100)
