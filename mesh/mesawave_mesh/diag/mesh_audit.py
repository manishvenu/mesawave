"""Audit a WW3 gmsh mesh and estimate node counts for candidate size functions.

usage: python mesh_audit.py mesh.msh outdir
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = 6371.0
path, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)


def read_msh(path):
    with open(path) as f:
        for i, line in enumerate(f):
            if line.startswith("$Nodes"):
                nn = int(next(f)); n0 = i + 2
                break
    nodes = pd.read_csv(path, sep=r"\s+", skiprows=n0, nrows=nn, header=None,
                        engine="c").to_numpy()
    e0 = n0 + nn + 2
    el = pd.read_csv(path, sep=r"\s+", skiprows=e0 + 1, header=None, engine="c",
                     names=range(9), comment="$").to_numpy()
    tri = el[el[:, 1] == 2][:, 6:9].astype(np.int64) - 1
    return nodes[:, 1], nodes[:, 2], nodes[:, 3], tri


lon, lat, dep, tri = read_msh(path)
N = lon.size
lam, phi = np.deg2rad(lon), np.deg2rad(lat)
xyz = np.c_[np.cos(phi) * np.cos(lam), np.cos(phi) * np.sin(lam), np.sin(phi)]

# edges, lengths, node resolution
e = np.vstack([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])
ch = np.linalg.norm(xyz[e[:, 0]] - xyz[e[:, 1]], axis=1)
L = 2 * R * np.arcsin(np.clip(ch / 2, 0, 1))
h = (np.bincount(e[:, 0], L, N) + np.bincount(e[:, 1], L, N)) / \
    (np.bincount(e[:, 0], minlength=N) + np.bincount(e[:, 1], minlength=N))

# triangle and dual areas
a, b, c = xyz[tri[:, 0]], xyz[tri[:, 1]], xyz[tri[:, 2]]
At = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1) * R**2
A = np.bincount(tri.ravel(), np.repeat(At / 3, 3), N)

# boundary edges -> coastline nodes and loops
es = np.sort(e, axis=1)
key = es[:, 0] * N + es[:, 1]
uk, cnt = np.unique(key, return_counts=True)
bk = uk[cnt == 1]
be = np.c_[bk // N, bk % N]
bnodes = np.unique(be)
tree = cKDTree(xyz[bnodes])
dch, _ = tree.query(xyz, k=1, workers=4)
dco = 2 * R * np.arcsin(np.clip(dch / 2, 0, 1))

g = coo_matrix((np.ones(len(be)), (be[:, 0], be[:, 1])), shape=(N, N))
ncomp, lab = connected_components(g, directed=False)
bl = np.linalg.norm(xyz[be[:, 0]] - xyz[be[:, 1]], axis=1) * R
perim = np.bincount(lab[be[:, 0]], bl, ncomp)
loops = perim[np.bincount(lab[be[:, 0]], minlength=ncomp) > 0]

out = []
P = out.append
P(f"nodes {N:,}  triangles {len(tri):,}  area {A.sum()/1e6:.1f} M km2")
P(f"h (mean incident edge, km): min {h.min():.2f}  p1 {np.percentile(h,1):.2f}  "
  f"median {np.median(h):.2f}  p99 {np.percentile(h,99):.2f}  max {h.max():.2f}")
P(f"depth: min {dep.min():.3f}  nodes<1m {np.sum(dep<1)}  <2.5m {np.sum(dep<2.5)}  <5m {np.sum(dep<5)}")
P(f"boundary nodes {len(bnodes):,}  boundary loops {len(loops):,}")
for lo, hi in [(0, 20), (20, 50), (50, 100), (100, 1000), (1000, 1e9)]:
    m = (loops >= lo) & (loops < hi)
    P(f"  loops with perimeter {lo:>5}-{hi:<6.0f} km: {m.sum():6d}")

P("\nnodes / area by resolution bin")
hb = [0, 6, 8, 10, 12, 15, 20, 23, 100]
for lo, hi in zip(hb[:-1], hb[1:]):
    m = (h >= lo) & (h < hi)
    P(f"  h {lo:>3}-{hi:<3} km: {m.sum():>9,} nodes ({100*m.mean():5.1f}%)  area {A[m].sum()/1e6:7.1f} M km2")

P("\nnodes by distance-to-coast bin x resolution bin")
db = [0, 25, 50, 100, 200, 400, 1e5]
hb2 = [0, 8, 12, 18, 100]
P("  dist(km)   " + "".join(f"h<{x:<4}" if i == 0 else f"{hb2[i]}-{x:<5}" for i, x in enumerate(hb2[1:])) + "   total")
for lo, hi in zip(db[:-1], db[1:]):
    m = (dco >= lo) & (dco < hi)
    row = [np.sum(m & (h >= l2) & (h < h2)) for l2, h2 in zip(hb2[:-1], hb2[1:])]
    P(f"  {lo:>4.0f}-{hi:<6.0f}" + "".join(f"{r:>9,}" for r in row) + f"{m.sum():>11,}")

# offshore refinement
off = (h < 15) & (dco > 100)
P(f"\noffshore refined nodes (h<15 km, >100 km from mesh coast): {off.sum():,}")
P(f"  of which depth < 200 m: {np.sum(off & (dep < 200)):,};  200-1000 m: "
  f"{np.sum(off & (dep >= 200) & (dep < 1000)):,};  >1000 m: {np.sum(off & (dep >= 1000)):,}")
cell = (np.floor(lat / 5) * 5).astype(int) * 1000 + (np.floor(lon / 5) * 5).astype(int)
df = pd.DataFrame(dict(cell=cell[off], dep=dep[off], h=h[off]))
top = df.groupby("cell").agg(n=("h", "size"), hmed=("h", "median"), dmed=("dep", "median")) \
        .sort_values("n", ascending=False).head(30)
P("  top 5x5 deg cells (lat0, lon0): n, median h, median depth")
for k, r in top.iterrows():
    la0 = int(np.round(k / 1000)); lo0 = k - la0 * 1000
    P(f"   ({la0:>4},{lo0:>5})  {int(r.n):>7,}  {r.hmed:5.1f} km  {r.dmed:6.0f} m")


def box(x0, x1, y0, y1):
    return (lon >= x0) & (lon <= x1) & (lat >= y0) & (lat <= y1)


regions = {
    "Guam/Marianas 140-150E,10-22N": box(140, 150, 10, 22),
    "Philippine Sea 125-160E,5-30N": box(125, 160, 5, 30),
    "Hawaii": box(-162, -153, 17, 24),
    "French Polynesia": box(-155, -130, -30, -5),
    "US East+Gulf": box(-98, -66, 24, 46),
    "US West": box(-126, -116, 31, 49),
    "Alaska": (box(-180, -129, 50, 72) | box(170, 180, 50, 72)),
    "Puerto Rico/USVI": box(-68.5, -64, 17, 19),
    "Gulf of Mexico": box(-98, -80, 18, 31),
    "Arctic >66N": lat > 66,
    "Southern Ocean <-50": lat < -50,
}
P("\nregions: nodes, median h, nodes with h<8")
for k, m in regions.items():
    P(f"  {k:32s} {m.sum():>9,}  {np.median(h[m]) if m.any() else np.nan:5.1f} km  {np.sum(m & (h<8)):>9,}")

# ------------------------------------------------------------------
# size-function estimator, calibrated so it returns N for the current h
cal = np.sum(A / h**2) / N


def est(hnew):
    return np.sum(A / hnew**2) / cal


def dist_to(mask_b):
    t = cKDTree(xyz[bnodes[mask_b]])
    d, _ = t.query(xyz, k=1, workers=4)
    return 2 * R * np.arcsin(np.clip(d / 2, 0, 1))


bl_, bp_ = lon[bnodes], lat[bnodes]


def bbox(x0, x1, y0, y1):
    return (bl_ >= x0) & (bl_ <= x1) & (bp_ >= y0) & (bp_ <= y1)


conus_b = (bbox(-98, -66.9, 24.4, 45.3) & ~bbox(-79.5, -72, 20, 27.5)) | bbox(-125, -117, 32.4, 49)
ak_b = bbox(-180, -129.9, 51, 72) | bbox(170, 180, 51, 56)
hipr_b = bbox(-161, -154.5, 18.5, 22.5) | bbox(-68, -64.4, 17.5, 18.6)
d_conus = dist_to(conus_b)
d_us_all = dist_to(conus_b | ak_b | hipr_b)

tc_full = (box(-100, -15, 5, 45) | box(-140, -80, 5, 30) | box(100, 180, 0, 45) |
           box(50, 100, 5, 25) | box(30, 130, -35, -5) | box(130, 180, -35, -5) |
           box(-180, -130, -35, -5))
tc_core = (box(-98, -55, 10, 38) | box(-120, -90, 10, 25) | box(115, 160, 8, 35) |
           box(80, 95, 10, 23) | box(40, 115, -25, -10) | box(140, 180, -25, -10))

P(f"\nestimator calibration constant (area per node / h^2): {cal:.3f}")
P(f"node-count estimates (same coastline/domain as this mesh; grade = km of h per km of distance)")


def scenario(name, hc=10, hus=5, us="conus", grade=0.15, tc=None, htc=11,
             tc_coast_km=None, shallow=None, hopen=25):
    hn = np.full(N, float(hopen))
    hn = np.minimum(hn, hc + grade * dco)
    if us is not None:
        d = d_conus if us == "conus" else d_us_all
        hn = np.minimum(hn, hus + grade * d)
    if tc is not None:
        m = tc if tc_coast_km is None else (tc & (dco < tc_coast_km))
        hn = np.where(m, np.minimum(hn, htc), hn)
    if shallow is not None:
        hn = np.where(dep < shallow[0], np.minimum(hn, shallow[1]), hn)
    n = est(hn)
    P(f"  {name:62s} {n/1e6:6.2f} M")
    return hn


P(f"  {'current mesh (check)':62s} {est(h)/1e6:6.2f} M")
scenario("uniform 25 km", hc=25, us=None)
scenario("25 km open, 10 km coast (g=0.15)", us=None)
scenario("25/10 coast + 5 km CONUS", us="conus")
scenario("25/10 coast + 5 km US (CONUS+AK+HI+PR)", us="all")
scenario("25/10/5CONUS + 11 km TC core boxes", us="conus", tc=tc_core)
hA = scenario("25/10/5CONUS + 11 km TC full basins", us="conus", tc=tc_full)
scenario("25/10/5CONUS + 11 km TC full basins, 12 km", us="conus", tc=tc_full, htc=12)
scenario("25/10/5CONUS + 11 km TC basins within 500 km of coast", us="conus", tc=tc_full, tc_coast_km=500)
hB = scenario("25/10/5CONUS + 11 km TC core boxes within 500 km of coast", us="conus", tc=tc_core, tc_coast_km=500)
scenario("  same + shallow banks (<200 m) at <=12 km", us="conus", tc=tc_core, tc_coast_km=500, shallow=(200, 12))
scenario("25/10/5US-all + 11 km TC core within 500 km", us="all", tc=tc_core, tc_coast_km=500)
scenario("grade 0.10 (wider transitions): 25/10/5CONUS + TC core 500km", us="conus", tc=tc_core,
         tc_coast_km=500, grade=0.10)
scenario("grade 0.25 (sharper): 25/10/5CONUS + TC core 500km", us="conus", tc=tc_core,
         tc_coast_km=500, grade=0.25)
scenario("30 km open: 30/10/5CONUS + TC core 500km", us="conus", tc=tc_core, tc_coast_km=500, hopen=30)

P("\nUS 5 km extent variants (all with 25 open / 10 coast / 11 km TC core boxes within 500 km)")
base = np.minimum(np.full(N, 25.0), 10 + 0.15 * dco)
base = np.where(tc_core & (dco < 500), np.minimum(base, 11), base)
gom = box(-98, -80.5, 18, 31)
shelf = dep < 200
for lbl, d in [("CONUS", d_conus), ("US all (CONUS+AK+HI+PR)", d_us_all)]:
    for band in [0, 50, 100, 200]:
        hn = np.minimum(base, 5 + 0.15 * np.maximum(d - band, 0))
        P(f"  {lbl:26s} 5 km band {band:>3} km offshore then graded      {est(hn)/1e6:6.2f} M")
    hn = np.minimum(base, 5 + 0.15 * d)
    hn = np.where(shelf & (d < 400), 5.0, hn)
    P(f"  {lbl:26s} 5 km on shelf (<200 m) within 400 km   {est(hn)/1e6:6.2f} M")
    hn = np.minimum(base, 5 + 0.15 * np.maximum(d - 100, 0))
    hn = np.where(gom, 5.0, hn)
    P(f"  {lbl:26s} 100 km band + all of Gulf of Mexico   {est(hn)/1e6:6.2f} M")
P(f"\nGulf of Mexico area {A[gom].sum()/1e6:.2f} M km2; AK shelf(<200m) area "
  f"{A[regions['Alaska'] & shelf].sum()/1e6:.2f} M km2")

P("\nchosen: 25 open / 10 coast / 11 km TC core boxes within 500 km / 5 km at US coasts")
pr_b = bbox(-68, -64.4, 17.5, 18.6)
hi_b = bbox(-161, -154.5, 18.5, 22.5)
as_b = bbox(-171.2, -168.0, -14.6, -13.9)
sets = {"CONUS+AK+PR": conus_b | ak_b | pr_b,
        "CONUS+AK+PR+HI+AmSamoa": conus_b | ak_b | pr_b | hi_b | as_b}
hC = None
for lbl, mb in sets.items():
    d = dist_to(mb)
    for band in [0, 25, 50, 100, 150]:
        hn = np.minimum(base, 5 + 0.15 * np.maximum(d - band, 0))
        P(f"  {lbl:24s} 5 km band {band:>3} km then graded 0.15   {est(hn)/1e6:6.2f} M")
        if lbl.endswith("AmSamoa") and band == 50:
            hC = hn
P(f"  regional split for chosen (band 50 km, with HI+AmSamoa): "
  f"h<=6 km nodes ~{np.sum(A[hC <= 6] / hC[hC <= 6]**2)/cal/1e3:.0f}k, "
  f"6-12 km ~{np.sum(A[(hC > 6) & (hC <= 12)] / hC[(hC > 6) & (hC <= 12)]**2)/cal/1e3:.0f}k, "
  f">12 km ~{np.sum(A[hC > 12] / hC[hC > 12]**2)/cal/1e3:.0f}k")



open(os.path.join(outdir, "audit.txt"), "w").write("\n".join(out) + "\n")
print("\n".join(out))

# ------------------------------------------------------------------ figures
def binned(v, res=0.5, fn="median"):
    ix = np.clip(((lon + 180) / res).astype(int), 0, int(360 / res) - 1)
    iy = np.clip(((lat + 90) / res).astype(int), 0, int(180 / res) - 1)
    s = pd.DataFrame(dict(k=iy * int(360 / res) + ix, v=v)).groupby("k").v.agg(fn)
    G = np.full(int(180 / res) * int(360 / res), np.nan)
    G[s.index.values] = s.values
    return G.reshape(int(180 / res), int(360 / res))


ext = [-180, 180, -90, 90]
fig, axs = plt.subplots(3, 1, figsize=(11, 15), constrained_layout=True)
im = axs[0].imshow(binned(h, fn="min"), origin="lower", extent=ext, vmin=4, vmax=26, cmap="viridis")
axs[0].set_title(f"Global_WIS_option3 (wu025r004): min node spacing per 0.5 deg cell, {N/1e6:.2f} M nodes")
fig.colorbar(im, ax=axs[0], label="km")
sc = axs[1].scatter(lon[off], lat[off], c=np.minimum(dep[off], 4000), s=0.2, cmap="cividis_r", rasterized=True)
axs[1].set_xlim(-180, 180); axs[1].set_ylim(-90, 90)
axs[1].set_title(f"Offshore refinement: h < 15 km and > 100 km from coast ({off.sum():,} nodes), colored by depth")
fig.colorbar(sc, ax=axs[1], label="depth (m)")
im = axs[2].imshow(binned(hB, fn="min"), origin="lower", extent=ext, vmin=4, vmax=26, cmap="viridis")
axs[2].set_title(f"Candidate size function: 25 km open / 10 km coast / 5 km CONUS / 11 km TC landfall belts "
                 f"(~{est(hB)/1e6:.2f} M nodes)")
fig.colorbar(im, ax=axs[2], label="km")
for ax in axs:
    ax.set_xlabel("lon"); ax.set_ylabel("lat")
fig.savefig(os.path.join(outdir, "audit.png"), dpi=110)

fig, axs = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
axs[0].hexbin(np.log10(np.maximum(dep, 1)), h, gridsize=120, bins="log", mincnt=1)
axs[0].set_xlabel("log10 depth (m)"); axs[0].set_ylabel("h (km)"); axs[0].set_title("resolution vs depth")
axs[1].hexbin(np.log10(np.maximum(dco, 0.1)), h, gridsize=120, bins="log", mincnt=1)
axs[1].set_xlabel("log10 distance to mesh coast (km)"); axs[1].set_title("resolution vs distance to coast")
fig.savefig(os.path.join(outdir, "audit_scatter.png"), dpi=110)
np.savez_compressed(os.path.join(outdir, "audit_nodes.npz"), lon=lon, lat=lat, dep=dep, h=h, A=A, dco=dco)

fig, axs = plt.subplot_mosaic([["g", "g", "g"], ["us", "ak", "car"]], figsize=(14, 11),
                              constrained_layout=True, height_ratios=[1.3, 1])
im = axs["g"].imshow(binned(hC, fn="min"), origin="lower", extent=ext, vmin=4, vmax=26, cmap="viridis")
axs["g"].set_title(f"Chosen size function (estimate ~{est(hC)/1e6:.2f} M nodes): 25 open / 10 coast / "
                   "5 km US coasts (50 km band) / 11 km TC belts")
fig.colorbar(im, ax=axs["g"], label="km", shrink=0.8)
for k, (x0, x1, y0, y1, t) in {"us": (-100, -60, 17, 47, "US East + Gulf"),
                               "ak": (-180, -128, 48, 75, "Alaska"),
                               "car": (-72, -60, 15, 21, "Puerto Rico / USVI")}.items():
    m = box(x0, x1, y0, y1)
    axs[k].scatter(lon[m], lat[m], c=hC[m], s=0.3, vmin=4, vmax=26, cmap="viridis", rasterized=True)
    axs[k].set_xlim(x0, x1); axs[k].set_ylim(y0, y1); axs[k].set_title(t)
fig.savefig(os.path.join(outdir, "chosen.png"), dpi=110)
