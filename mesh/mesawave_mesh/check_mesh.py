"""Check an OceanMesh2D mesh against the target size raster.

usage: python check_mesh.py PREFIX_ptb.mat SIZEFX.nc SCALE OUT.png
"""
import sys

import netCDF4
import numpy as np
import scipy.io as sio
from scipy.interpolate import RegularGridInterpolator

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = 6371.0
ptb, sizefile, scale, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]

d = sio.loadmat(ptb)
p, t, b = d["p"], d["t"].astype(np.int64) - 1, d["b"].ravel()
lon, lat = p[:, 0], p[:, 1]
N = lon.size

lam, phi = np.deg2rad(lon), np.deg2rad(lat)
xyz = np.c_[np.cos(phi) * np.cos(lam), np.cos(phi) * np.sin(lam), np.sin(phi)]
e = np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]])
L = 2 * R * np.arcsin(np.clip(np.linalg.norm(xyz[e[:, 0]] - xyz[e[:, 1]], axis=1) / 2, 0, 1))
h = (np.bincount(e[:, 0], L, N) + np.bincount(e[:, 1], L, N)) / \
    (np.bincount(e[:, 0], minlength=N) + np.bincount(e[:, 1], minlength=N))
a, bb, c = xyz[t[:, 0]], xyz[t[:, 1]], xyz[t[:, 2]]
area = 0.5 * np.linalg.norm(np.cross(bb - a, c - a), axis=1).sum() * R**2

with netCDF4.Dataset(sizefile) as nc:
    F = RegularGridInterpolator((nc["lat"][:], nc["lon"][:]), nc["h"][:] / 1e3, bounds_error=False, fill_value=None)
target = scale * F(np.c_[lat, lon])
ratio = h / target

print(f"nodes {N:,}  triangles {len(t):,}  ocean area {area/1e6:.1f} M km2")
print(f"lat {lat.min():.2f}..{lat.max():.2f}; nodes south of 79S: {np.sum(lat < -79)}")
print(f"depth min {b.min():.1f} m; nodes at the floor: {np.sum(b <= b.min() + 1e-6)}")
print("spacing / target (1 = on spec): p10 %.2f  p50 %.2f  p90 %.2f" % tuple(np.percentile(ratio, [10, 50, 90])))
for name, m in [("US 5 km bands", target <= 5.5 * scale), ("coast / TC (5.5-12.5 km)", (target > 5.5 * scale) & (target <= 12.5 * scale)),
                ("transition (12.5-24 km)", (target > 12.5 * scale) & (target < 24 * scale)), ("open ocean (25 km)", target >= 24 * scale)]:
    if m.any():
        print(f"  {name:26s} nodes {m.sum():>9,}  target {np.median(target[m]):6.1f} km  "
              f"actual {np.median(h[m]):6.1f} km  ratio {np.median(ratio[m]):.2f}")

fig, axs = plt.subplots(2, 1, figsize=(14, 13), constrained_layout=True)
sc = axs[0].scatter(lon, lat, c=h / scale, s=0.3 if N > 2e5 else 2, cmap="viridis", vmin=4, vmax=26, rasterized=True)
fig.colorbar(sc, ax=axs[0], label="node spacing / scale (km)")
axs[0].set_title(f"{ptb.split('/')[-1]}: {N:,} nodes (scale {scale:g})")
sc = axs[1].scatter(lon, lat, c=ratio, s=0.3 if N > 2e5 else 2, cmap="RdBu_r", vmin=0.5, vmax=1.5, rasterized=True)
fig.colorbar(sc, ax=axs[1], label="spacing / target")
axs[1].set_title("actual / target spacing (red: coarser than spec, blue: finer)")
for ax in axs:
    ax.set_xlim(-180, 180); ax.set_ylim(-90, 90)
fig.savefig(out, dpi=100)
