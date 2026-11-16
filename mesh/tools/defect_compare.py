"""Open-ocean neighbour counts, edge lengths and defect clumping for several ptb meshes,
all over the same region (where OUR size function says 25 km).
usage: defect_compare.py SIZEFX.nc A_ptb.mat [B_ptb.mat ...]
"""
import sys

import netCDF4
import numpy as np
import scipy.io as sio
from scipy.interpolate import RegularGridInterpolator
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

with netCDF4.Dataset(sys.argv[1]) as nc:
    F = RegularGridInterpolator((nc["lat"][:], nc["lon"][:]), np.asarray(nc["h"][:]) / 1e3,
                                bounds_error=False, fill_value=None)
for path in sys.argv[2:]:
    d = sio.loadmat(path)
    p, t = d["p"], d["t"].astype(np.int64) - 1
    N = len(p)
    e = np.sort(np.vstack([t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]), axis=1)
    eu, cnt = np.unique(e, axis=0, return_counts=True)
    bnd = np.zeros(N, bool); bnd[eu[cnt == 1].ravel()] = True
    deg = np.bincount(eu.ravel(), minlength=N)
    oo = (F(np.c_[p[:, 1], p[:, 0]]) >= 24.99) & ~bnd           # open-ocean interior nodes

    # edge lengths (km, chord) between open-ocean nodes
    lo, la = np.deg2rad(p[:, 0]), np.deg2rad(p[:, 1])
    x = 6371.0 * np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)]
    L = np.linalg.norm(x[eu[:, 0]] - x[eu[:, 1]], axis=1)[oo[eu].all(axis=1)]

    # defects = open-ocean nodes without 6 neighbours; group touching defects into clumps
    bad = oo & (deg != 6)
    be = eu[bad[eu].all(axis=1)]
    g = coo_matrix((np.ones(len(be)), (be[:, 0], be[:, 1])), shape=(N, N))
    _, lab = connected_components(g, directed=False)
    sizes = np.bincount(lab[bad])
    sizes = sizes[sizes > 0]

    # how deep inside the 25 km zone is each defect? distance to the nearest coastal or
    # refined (< 25 km target) node, in units of the median open-ocean edge length
    edge_or_ref = bnd | ~(F(np.c_[p[:, 1], p[:, 0]]) >= 24.99)
    dist = cKDTree(x[edge_or_ref]).query(x[bad])[0] / np.median(L)
    name = path.split("/")[-1].replace("_ptb.mat", "")
    k = np.bincount(np.clip(deg[oo], 3, 9), minlength=10)
    print(f"\n== {name}: {N:,} nodes total; open-ocean interior {oo.sum():,}")
    print(f"   neighbours: 4-or-fewer {k[3] + k[4]:,}  5: {k[5]:,}  6: {k[6]:,}  7: {k[7]:,}  "
          f"8-or-more {k[8] + k[9]:,}")
    print(f"   not 6: {bad.sum():,} ({bad.sum() / oo.sum():.2%} of open-ocean nodes)")
    print(f"   edge length km: p5 {np.percentile(L, 5):.1f}  p50 {np.percentile(L, 50):.1f}  "
          f"p95 {np.percentile(L, 95):.1f}")
    print(f"   defect clumps: {len(sizes):,}; size 1: {np.sum(sizes == 1):,}, size 2 (isolated pair): "
          f"{np.sum(sizes == 2):,}, 3-4: {np.sum((sizes >= 3) & (sizes <= 4)):,}, 5+: {np.sum(sizes >= 5):,} "
          f"(largest {sizes.max():,} nodes)")
    print(f"   defects by distance from the coast or refined zone (in spacings): "
          f"<=2: {np.sum(dist <= 2.5):,}, 3-5: {np.sum((dist > 2.5) & (dist <= 5.5)):,}, "
          f">5 (deep open ocean): {np.sum(dist > 5.5):,}")
