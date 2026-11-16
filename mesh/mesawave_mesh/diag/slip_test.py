"""Uniform-h whole-sphere test: rows all starting at -180 (current) vs per-row phase that scatters
the row-count slips (golden-ratio longitudes). Distmesh force law in 3D, spherical Delaunay = hull.
usage: slip_test.py H_KM NIT OUT.png"""
import sys
import numpy as np
from scipy.spatial import ConvexHull
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = 6378.137
h, nit, out = float(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
rows = np.arange(-89.5, 89.6, np.rad2deg(h * np.sqrt(3) / 2 / R))
GOLD = 0.6180339887498949

def seed(mode):
    pts, l0p, sp = [], None, None
    for i, la in enumerate(rows):
        nx = max(1, round(2 * np.pi * R * np.cos(np.deg2rad(la)) / h)); s = 360 / nx
        if mode == "current":
            lon = -180 + (np.arange(nx) + 0.5 * (i % 2)) * s
        else:
            if l0p is None:
                l0 = -180.0
            else:  # new row exactly staggered against the previous one at a golden-ratio longitude
                lr = -180 + 360 * ((i * GOLD) % 1)
                l0 = l0p + (np.floor((lr - l0p) / sp) + 0.5) * sp
            lon = (l0 + np.arange(nx) * s + 180) % 360 - 180
            l0p, sp = l0, s
        pts.append(np.c_[lon, np.full(nx, la)])
    return np.vstack(pts)

def xyz(ll):
    lam, phi = np.deg2rad(ll[:, 0]), np.deg2rad(ll[:, 1])
    return np.c_[np.cos(phi) * np.cos(lam), np.cos(phi) * np.sin(lam), np.sin(phi)]

def relax(X):
    hb = h / R
    for it in range(nit):
        T = ConvexHull(X).simplices
        E = np.unique(np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1), axis=0)
        bar = X[E[:, 0]] - X[E[:, 1]]; L = np.linalg.norm(bar, axis=1)
        L0 = hb * 1.2 * np.median(L / hb)
        F = np.maximum(L0 - L, 0)[:, None] * bar / L[:, None]
        Ft = np.zeros_like(X); np.add.at(Ft, E[:, 0], F); np.add.at(Ft, E[:, 1], -F)
        X = X + 0.2 * Ft; X /= np.linalg.norm(X, axis=1)[:, None]
    T = ConvexHull(X).simplices
    E = np.unique(np.sort(np.vstack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]]), 1), axis=0)
    return X, np.bincount(E.ravel(), minlength=len(X))

fig, axs = plt.subplots(2, 1, figsize=(14, 12), constrained_layout=True)
for ax, mode in zip(axs, ["current", "golden"]):
    X, deg = relax(xyz(seed(mode)))
    lat = np.rad2deg(np.arcsin(X[:, 2])); lon = np.rad2deg(np.arctan2(X[:, 1], X[:, 0]))
    m = np.abs(lat) < 75; bad = m & (deg != 6)
    hst = np.histogram(lon[bad], bins=360, range=(-180, 180))[0]
    print(f"{mode:8s}: nodes {len(X):,}; |lat|<75 not 6-valent {bad.sum() / m.sum():.2%}; "
          f"max per 1-deg lon bin {hst.max()} (median {np.median(hst):.0f})")
    ax.scatter(lon[bad & (deg == 5)], lat[bad & (deg == 5)], s=1, c="tab:blue", rasterized=True)
    ax.scatter(lon[bad & (deg == 7)], lat[bad & (deg == 7)], s=1, c="tab:red", rasterized=True)
    ax.set_xlim(-180, 180); ax.set_ylim(-75, 75)
    ax.set_title(f"{mode} seeding, uniform {h:.0f} km, {nit} its: non-6-valent nodes (blue 5, red 7)")
fig.savefig(out, dpi=100)
