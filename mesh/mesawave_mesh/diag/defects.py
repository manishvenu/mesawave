"""Where are the non-6-valent nodes? usage: defects.py PTB.mat SIZEFX.nc OUT.png"""
import sys
import netCDF4
import numpy as np
import scipy.io as sio
from scipy.interpolate import RegularGridInterpolator
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

R = 6371.0
d = sio.loadmat(sys.argv[1]); p, t = d["p"], d["t"].astype(np.int64) - 1
lon, lat = p[:, 0], p[:, 1]; N = len(lon)
with netCDF4.Dataset(sys.argv[2]) as nc:
    F = RegularGridInterpolator((nc["lat"][:], nc["lon"][:]), nc["h"][:] / 1e3, bounds_error=False, fill_value=None)
tgt = F(np.c_[lat, lon])
e = np.sort(np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1)
eu, cnt = np.unique(e, axis=0, return_counts=True)
bnd = np.zeros(N, bool); bnd[eu[cnt == 1].ravel()] = True
deg = np.bincount(eu.ravel(), minlength=N)
oo = (tgt >= 24.99) & ~bnd
d5, d7 = oo & (deg == 5), oo & (deg == 7)
print(f"open-ocean interior {oo.sum():,}: deg5 {d5.sum():,} deg7 {d7.sum():,}")
# lon histogram of defects in |lat|<60 open ocean
m = (d5 | d7) & (np.abs(lat) < 60)
hst, edges = np.histogram(lon[m], bins=360, range=(-180, 180))
print("defects per 1-deg lon bin (|lat|<60): median %d; top bins:" % np.median(hst))
for i in np.argsort(hst)[::-1][:8]:
    print(f"   lon {edges[i]:7.1f}..{edges[i+1]:7.1f}: {hst[i]}")
np.savez(sys.argv[3].replace(".png", ".npz"), lon=lon, lat=lat, deg=deg, oo=oo, tgt=tgt)

fig = plt.figure(figsize=(16, 15), constrained_layout=True)
gs = fig.add_gridspec(2, 3, height_ratios=[1.1, 1])
ax = fig.add_subplot(gs[0, :])
ax.scatter(lon[d5], lat[d5], s=0.5, c="tab:blue", label="5 neighbours", rasterized=True)
ax.scatter(lon[d7], lat[d7], s=0.5, c="tab:red", label="7 neighbours", rasterized=True)
ax.set_xlim(-180, 180); ax.set_ylim(-80, 90); ax.legend(markerscale=10, loc="lower left")
ax.set_title("open-ocean (25 km) interior nodes that are not 6-valent")
boxes = [(-6, 6, -6, 6, "lon 0 seam"), (-150, -130, -5, 10, "open N/S Pacific"), (-40, -20, -66, -52, "Southern Ocean fan")]
for x0, x1, y0, y1, nm in boxes:
    ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], "k-", lw=1)
for k, (x0, x1, y0, y1, nm) in enumerate(boxes):
    a = fig.add_subplot(gs[1, k])
    sel = np.all((lon[t] > x0 - 1) & (lon[t] < x1 + 1) & (lat[t] > y0 - 1) & (lat[t] < y1 + 1), axis=1)
    tt = t[sel]; ee = np.unique(np.sort(np.vstack([tt[:, [0, 1]], tt[:, [1, 2]], tt[:, [2, 0]]]), axis=1), axis=0)
    a.add_collection(LineCollection(np.stack([p[ee[:, 0]], p[ee[:, 1]]], 1), lw=0.3, colors="0.6"))
    for msk, c in [(deg == 5, "tab:blue"), (deg == 7, "tab:red")]:
        q = msk & (lon > x0) & (lon < x1) & (lat > y0) & (lat < y1)
        a.plot(lon[q], lat[q], "o", ms=3, c=c)
    a.set_xlim(x0, x1); a.set_ylim(y0, y1); a.set_title(nm)
fig.savefig(sys.argv[3], dpi=110)
