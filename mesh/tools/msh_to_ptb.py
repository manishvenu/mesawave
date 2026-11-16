"""Gmsh v2 mesh (.msh / .ww3) -> ptb .mat (p = lon,lat; t = triangles, 1-based; b = depth),
so the mesawave_mesh/diag scripts can read meshes that weren't built by make_mesh.m.
usage: msh_to_ptb.py MESH.msh OUT_ptb.mat
"""
import sys

import numpy as np
import scipy.io as sio

src, out = sys.argv[1:3]
with open(src) as f:
    for line in f:
        if line.startswith("$Nodes"):
            break
    nn = int(next(f))
    nodes = np.array([next(f).split()[:4] for _ in range(nn)], dtype=float)   # id lon lat depth
    for line in f:
        if line.startswith("$Elements"):
            break
    ne = int(next(f))
    tri = []
    for _ in range(ne):
        w = next(f).split()
        if w[1] == "2":                      # element type 2 = 3-node triangle
            tri.append(w[3 + int(w[2]):])    # skip the tags
assert (nodes[:, 0] == np.arange(1, nn + 1)).all(), "node ids are not 1..N in order"
t = np.array(tri, dtype=np.int64)
sio.savemat(out, {"p": nodes[:, 1:3], "t": t, "b": nodes[:, 3:4]})
print(f"{src}: {nn:,} nodes, {len(t):,} triangles -> {out}")
