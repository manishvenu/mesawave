"""Pick an icosahedron orientation whose 12 corners (the only 5-neighbour points of an
icosahedral lattice) fall on land, or failing that in refined (< 25 km) ocean.
usage: icos_rotation.py GEBCO.nc SIZEFX.nc
Prints the rotation matrix Q for initial_points_icos in make_mesh.m.
"""
import sys

import netCDF4
import numpy as np
from scipy.ndimage import minimum_filter
from scipy.spatial.transform import Rotation

gebco, sizefx = sys.argv[1:3]
with netCDF4.Dataset(gebco) as nc:                       # 1 arcmin; keep every 8th (~15 km)
    elev = np.asarray(nc["elevation"][::8, ::8], dtype=np.int16)
    glat, glon = nc["lat"][::8], nc["lon"][::8]
deep_land = minimum_filter(elev, size=3, mode="wrap") > 0   # land within ~15 km all round
with netCDF4.Dataset(sizefx) as nc:
    h = np.asarray(nc["h"][:]); slat, slon = nc["lat"][:], nc["lon"][:]


def lookup(grid, lat, lon, x, y):
    i = np.clip(np.searchsorted(lat, x), 0, len(lat) - 1)
    j = np.clip(np.searchsorted(lon, y), 0, len(lon) - 1)
    return grid[i, j]


phi = (1 + 5 ** 0.5) / 2
V = np.array([[0, 1, phi], [0, -1, phi], [0, 1, -phi], [0, -1, -phi], [1, phi, 0], [-1, phi, 0],
              [1, -phi, 0], [-1, -phi, 0], [phi, 0, 1], [-phi, 0, 1], [phi, 0, -1], [-phi, 0, -1]])
V /= np.linalg.norm(V, axis=1, keepdims=True)

rots = Rotation.random(200_000, random_state=0)
X = np.einsum("rij,vj->rvi", rots.as_matrix(), V)            # rotated corners [rot, 12, 3]
lat = np.degrees(np.arcsin(np.clip(X[..., 2], -1, 1)))
lon = np.degrees(np.arctan2(X[..., 1], X[..., 0]))
land = lookup(deep_land, glat, glon, lat, lon) | (lat < -80)  # south of the mesh = land
open_ocean = ~land & (lookup(h, slat, slon, lat, lon) >= 24990)
cost = (10 * open_ocean + 1 * (~land & ~open_ocean)).sum(axis=1)
b = np.argmin(cost)
print(f"best of {len(rots):,}: {land[b].sum()} corners on land, {(~land[b] & ~open_ocean[b]).sum()} in "
      f"refined ocean, {open_ocean[b].sum()} in 25 km open ocean")
print(f"random orientation, on average: {land.sum(1).mean():.1f} on land, {open_ocean.sum(1).mean():.1f} open ocean")
for k in range(12):
    where = "land" if land[b, k] else ("OPEN OCEAN" if open_ocean[b, k] else "refined ocean")
    print(f"   corner {k + 1:2d}: lon {lon[b, k]:8.2f} lat {lat[b, k]:7.2f}  {where}")
Q = rots[b].as_matrix()
print("Q = [" + "; ".join(" ".join(f"{v:.15f}" for v in row) for row in Q) + "];")
