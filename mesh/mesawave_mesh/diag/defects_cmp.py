"""Open-ocean non-6-valent nodes, two meshes. usage: defects_cmp.py A.npz B.npz OUT.png"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, axs = plt.subplots(2, 1, figsize=(14, 13), constrained_layout=True)
for ax, f in zip(axs, sys.argv[1:3]):
    z = np.load(f); lon, lat, deg, oo = z["lon"], z["lat"], z["deg"], z["oo"]
    bad = oo & (deg != 6)
    hst = np.histogram(lon[bad & (np.abs(lat) < 60)], bins=360, range=(-180, 180))[0]
    nm = f.split("/")[-1].replace(".npz", "")
    print(f"{nm}: open-ocean interior {oo.sum():,}, not 6-valent {bad.sum():,} ({bad.sum()/oo.sum():.2%}); "
          f"per 1-deg lon bin (|lat|<60) max {hst.max()} median {np.median(hst):.0f}; "
          f"bins at 0/-45/45/-135: {hst[180]+hst[179]}/{hst[134]+hst[135]}/{hst[224]+hst[225]}/{hst[44]+hst[45]}")
    ax.scatter(lon[bad & (deg == 5)], lat[bad & (deg == 5)], s=0.5, c="tab:blue", rasterized=True)
    ax.scatter(lon[bad & (deg == 7)], lat[bad & (deg == 7)], s=0.5, c="tab:red", rasterized=True)
    ax.set_xlim(-180, 180); ax.set_ylim(-80, 90)
    ax.set_title(f"{nm}: open-ocean nodes with 5 (blue) or 7 (red) neighbours, {bad.sum():,} of {oo.sum():,}")
fig.savefig(sys.argv[3], dpi=100)
