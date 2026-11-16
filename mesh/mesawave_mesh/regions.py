"""MESAWAVE mesh regions (5 km US coastal bands, 12 km TC belts) and the size-function raster.

usage: python regions.py GSHHS_SHP_DIR IBTRACS_CSV AUDIT_NPZ OUTDIR
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import shapefile
import scipy.io as sio
from pyproj import Transformer
from scipy import ndimage
from scipy.spatial import cKDTree
from shapely import contains_xy
from shapely.geometry import LineString, Polygon, box, mapping
from shapely.ops import transform, unary_union
from skimage import measure
from skimage.morphology import convex_hull_image

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = 6371.0
US_BAND_KM = 100.0
TC_RADIUS_KM = 300.0
TC_CASES = [(1000.0, 500.0), (500.0, 500.0)]  # belt km from coast (North Atlantic, elsewhere); first is primary
TC_HULL = True  # replace belts by convex hulls (lon-lat): one for the North Atlantic, one per patch elsewhere
TC_MIN_ISLAND_KM2 = 100.0
TC_YEARS = (1980, 2024)
TC_THRESHOLDS = [0.25, 0.5, 1.0]  # storms per year within TC_RADIUS_KM
TC_CHOSEN = 0.5
GRID = 0.5  # deg, TC raster

gshhs_dir, ibtracs_csv, audit_npz, outdir = sys.argv[1:5]
os.makedirs(outdir, exist_ok=True)


def xyz(lon, lat):
    lam, phi = np.deg2rad(lon), np.deg2rad(lat)
    return np.c_[np.cos(phi) * np.cos(lam), np.cos(phi) * np.sin(lam), np.sin(phi)]


def chord(km):
    return 2 * np.sin(km / (2 * R))


def read_l1(res):
    r = shapefile.Reader(os.path.join(gshhs_dir, res, f"GSHHS_{res}_L1"))
    ia = [f[0] for f in r.fields[1:]].index("area")
    for sr in r.iterShapeRecords():
        yield np.asarray(sr.shape.points), float(sr.record[ia])


# ---------------------------------------------------------------- US bands
US = {
    "conus_east": dict(box=(-98, 24.4, -66.95, 45.3), lon0=-80, lat0=33,
                       excl=[(-79.5, 20, -72, 27.5), (-98.5, 20, -96.5, 25.9)]),
    "conus_west": dict(box=(-125.5, 32.5, -117, 49.0), lon0=-121, lat0=41, excl=[]),
    "alaska": dict(box=(-190, 51, -129.9, 72), lon0=-160, lat0=60, wrap=True,
                   excl=[(-141, 68, -129.9, 72), (-133.5, 51, -129.9, 54.6),
                         (-190, 64.0, -169.5, 72), (-190, 56.5, -180, 72)]),
    "puerto_rico": dict(box=(-68, 17.5, -64.4, 18.6), lon0=-66, lat0=18, excl=[]),
    "hawaii": dict(box=(-161, 18.5, -154.5, 22.5), lon0=-157.5, lat0=20.5, excl=[]),
    "american_samoa": dict(box=(-171.2, -14.6, -168.0, -13.9), lon0=-169.6, lat0=-14.2, excl=[]),
}

print("reading GSHHS h L1 ...", flush=True)
l1h = list(read_l1("h"))


def us_band(cfg):
    x0, y0, x1, y1 = cfg["box"]
    reg = box(x0, y0, x1, y1)
    for e in cfg["excl"]:
        reg = reg.difference(box(*e))
    lines = []
    for pts, _ in l1h:
        lon = pts[:, 0].copy()
        if cfg.get("wrap"):
            lon = np.where(lon > 0, lon - 360, lon)
        if lon.max() < x0 or lon.min() > x1 or pts[:, 1].max() < y0 or pts[:, 1].min() > y1:
            continue
        # unwrapping leaves 360-degree jumps; split there so no segment spans the globe
        cuts = np.where(np.abs(np.diff(lon)) > 180)[0] + 1
        for lo, la in zip(np.split(lon, cuts), np.split(pts[:, 1], cuts)):
            if lo.size < 2:
                continue
            g = LineString(np.c_[lo, la]).intersection(reg)
            if not g.is_empty:
                lines.append(g)
    coast = unary_union(lines)
    fwd = Transformer.from_crs("EPSG:4326", f"+proj=aeqd +lon_0={cfg['lon0']} +lat_0={cfg['lat0']} +datum=WGS84",
                               always_xy=True)
    inv = Transformer.from_crs(fwd.target_crs, "EPSG:4326", always_xy=True)
    band = transform(fwd.transform, coast).buffer(US_BAND_KM * 1e3, resolution=8).simplify(2e3)

    def back(x, y, z=None):
        lo, la = inv.transform(x, y)
        lo = np.asarray(lo)
        if cfg.get("wrap"):
            lo = np.where(lo > 0, lo - 360, lo)
        return lo, la

    band = transform(back, band)
    parts = []
    if cfg.get("wrap"):
        west = band.intersection(box(-200, -90, -180, 90))
        east = band.intersection(box(-180, -90, -100, 90))
        if not west.is_empty:
            parts.append(transform(lambda x, y, z=None: (np.asarray(x) + 360, y), west))
        parts.append(east)
    else:
        parts.append(band)
    return parts


def polys(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [Polygon(g.exterior)]
    return [Polygon(p.exterior) for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]


us_polys = {}
for name, cfg in US.items():
    ps = []
    for part in us_band(cfg):
        ps += polys(part)
    us_polys[name] = [p for p in ps if p.area > 1e-4]
    print(f"  US {name}: {len(us_polys[name])} polygon(s), "
          f"{sum(len(p.exterior.coords) for p in us_polys[name])} vertices", flush=True)

# ---------------------------------------------------------------- TC belts
print("reading IBTrACS ...", flush=True)
# keep_default_na=False, or pandas reads the North Atlantic basin code "NA" as missing
df = pd.read_csv(ibtracs_csv, skiprows=[1], low_memory=False, keep_default_na=False,
                 usecols=["SID", "SEASON", "BASIN", "NATURE", "LAT", "LON", "WMO_WIND", "USA_WIND",
                          "TRACK_TYPE"])
for c in ["SEASON", "LAT", "LON", "WMO_WIND", "USA_WIND"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
wind = df.USA_WIND.fillna(df.WMO_WIND)
df = df[(df.TRACK_TYPE == "main") & df.SEASON.between(*TC_YEARS) & (df.NATURE == "TS") & (wind >= 34)]
nyr = TC_YEARS[1] - TC_YEARS[0] + 1
print(f"  {df.SID.nunique()} storms, {len(df)} TS-strength fixes, {nyr} seasons", flush=True)

glon = np.arange(-180 + GRID / 2, 180, GRID)
glat = np.arange(-90 + GRID / 2, 90, GRID)
GX, GY = np.meshgrid(glon, glat)
gtree = cKDTree(xyz(GX.ravel(), GY.ravel()))
count = np.zeros(GX.size)
count_na = np.zeros(GX.size)  # North Atlantic basin fixes only
for sid, g in df.groupby("SID"):
    hits = gtree.query_ball_point(xyz(g.LON.values, g.LAT.values), chord(TC_RADIUS_KM))
    hits = [np.asarray(h, dtype=np.int64) for h in hits]
    count[np.unique(np.concatenate(hits))] += 1
    na = (g.BASIN.values == "NA")
    if na.any():
        count_na[np.unique(np.concatenate([h for h, k in zip(hits, na) if k]))] += 1
freq = (count / nyr).reshape(GX.shape)
freq_na = (count_na / nyr).reshape(GX.shape)
freq_ot = np.maximum(freq - freq_na, 0)
print(f"  NA-basin fixes: {(df.BASIN == 'NA').sum()}", flush=True)

print("distance to coast (islands >= %g km2) ..." % TC_MIN_ISLAND_KM2, flush=True)
cpts = np.concatenate([p[::4] for p, a in l1h if a >= TC_MIN_ISLAND_KM2])
ctree = cKDTree(xyz(cpts[:, 0], cpts[:, 1]))
d, _ = ctree.query(xyz(GX.ravel(), GY.ravel()), workers=4)
dcoast = (2 * R * np.arcsin(np.clip(d / 2, 0, 1))).reshape(GX.shape)
def tc_mask(th, belt_km, f):
    m = f >= th
    m = ndimage.binary_closing(m, iterations=2)
    m = ndimage.binary_dilation(m, iterations=2)  # ~100 km margin for poleward shift
    m &= dcoast <= belt_km
    lab, n = ndimage.label(m)
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    m = np.isin(lab, 1 + np.where(sizes >= 12)[0])
    return ndimage.binary_fill_holes(m)


def mask_to_polys(m):
    pad = np.pad(m.astype(float), 1)
    out = []
    for c in measure.find_contours(pad, 0.5):
        lat = -90 + (c[:, 0] - 1 + 0.5) * GRID
        lon = -180 + (c[:, 1] - 1 + 0.5) * GRID
        p = Polygon(np.c_[lon, lat]).buffer(0)
        p = p.intersection(box(-180, -90, 180, 90)).simplify(0.1)
        out += [q for q in polys(p) if q.area >= 4 * GRID**2]
    return out


def hull(m, whole=False):
    # seam on an empty meridian so patches crossing 180 stay whole
    empty = np.where(~m.any(axis=0))[0]
    s = empty[np.argmin(np.abs(glon[empty]))] if empty.size else 0
    r = np.roll(m, -s, axis=1)
    lab = r.astype(int) if whole else ndimage.label(r)[0]
    out = np.zeros_like(r)
    for k, sl in enumerate(ndimage.find_objects(lab), 1):
        if sl is not None:
            out[sl] |= convex_hull_image(lab[sl] == k)
    return np.roll(out, s, axis=1)


def case_mask(th, b_na, b_ot, hull_on=TC_HULL):
    na, ot = tc_mask(th, b_na, freq_na), tc_mask(th, b_ot, freq_ot)
    if hull_on:
        na, ot = hull(na, whole=True), hull(ot)
    return na | ot


def tag(b_na, b_ot, hull_on=TC_HULL):
    return f"na{b_na:.0f}_ot{b_ot:.0f}" + ("_hull" if hull_on else "")


masks = {th: case_mask(th, *TC_CASES[0]) for th in TC_THRESHOLDS}
tc_case_polys = {}
for b_na, b_ot in TC_CASES:
    tc_case_polys[(b_na, b_ot)] = mask_to_polys(case_mask(TC_CHOSEN, b_na, b_ot))
    print(f"  TC {tag(b_na, b_ot)} (f >= {TC_CHOSEN}/yr): {len(tc_case_polys[(b_na, b_ot)])} polygon(s)", flush=True)
tc_polys = tc_case_polys[TC_CASES[0]]

# ------------------------------------------- node estimate on Ali's mesh nodes
a = np.load(audit_npz)
lon, lat, A, h, dco = a["lon"], a["lat"], a["A"], a["h"], a["dco"]
cal = np.sum(A / h**2) / lon.size
us_pts = []
for name, cfg in US.items():
    x0, y0, x1, y1 = cfg["box"]
    reg = box(x0, y0, x1, y1)
    for e in cfg["excl"]:
        reg = reg.difference(box(*e))
    for pts, _ in l1h:
        lo = np.where(pts[:, 0] > 0, pts[:, 0] - 360, pts[:, 0]) if cfg.get("wrap") else pts[:, 0]
        k = contains_xy(reg, lo, pts[:, 1])
        if k.any():
            us_pts.append(pts[k][::2])
us_pts = np.concatenate(us_pts)
dus, _ = cKDTree(xyz(us_pts[:, 0], us_pts[:, 1])).query(xyz(lon, lat), workers=4)
dus = 2 * R * np.arcsin(np.clip(dus / 2, 0, 1))
ix = np.clip(((lon + 180) / GRID).astype(int), 0, glon.size - 1)
iy = np.clip(((lat + 90) / GRID).astype(int), 0, glat.size - 1)
lines = [f"node-count estimates for {tag(*TC_CASES[0])} (calibrated on wu025r004, +-10-15%):"]
for th in TC_THRESHOLDS:
    for htc in (11.0, 12.0):
        hn = np.minimum(25.0, 10 + 0.15 * dco)
        hn = np.where(masks[th][iy, ix], np.minimum(hn, htc), hn)
        hn = np.minimum(hn, 5 + 0.15 * np.maximum(dus - US_BAND_KM, 0))
        n = np.sum(A / hn**2) / cal
        tc_nodes = np.sum((A / hn**2)[masks[th][iy, ix] & (hn > 6)]) / cal
        lines.append(f"  TC f >= {th:<4}/yr at {htc:.0f} km: total {n/1e6:.2f} M  (TC-belt nodes ~{tc_nodes/1e3:.0f}k)")
        if th == TC_CHOSEN and htc == 12.0:
            h_chosen = hn

# belt-width scenarios: North Atlantic storms vs all other basins
BELTS = [(500, 500), (1000, 500), (1500, 500), (500, 1000), (1000, 1000), (1500, 1000), (1500, 1500), (np.inf, np.inf)]
lines.append("\nbelt scenarios (per-basin exposure; NA belt km / other belt km):")
scen = {}
for th in (0.5, 1.0):
    for b_na, b_ot in BELTS:
        for hl in (False, True):
            mk = case_mask(th, b_na, b_ot, hl)
            scen[(th, b_na, b_ot, hl)] = mk
            hn = np.minimum(25.0, 10 + 0.15 * dco)
            hn = np.where(mk[iy, ix], np.minimum(hn, 12.0), hn)
            hn = np.minimum(hn, 5 + 0.15 * np.maximum(dus - US_BAND_KM, 0))
            n = np.sum(A / hn**2) / cal
            lines.append(f"  f >= {th:<3} {b_na:>6.0f} / {b_ot:<6.0f} km{' hull' if hl else '     '} at 12 km: {n/1e6:.2f} M")
print("\n".join(lines), flush=True)
open(os.path.join(outdir, "estimate.txt"), "w").write("\n".join(lines) + "\n")

fig, axs = plt.subplots(2, 1, figsize=(13, 10), constrained_layout=True)
for ax, key, t in [(axs[0], (0.5, 1500, 1000, False), "1500 km North Atlantic / 1000 km elsewhere"),
                   (axs[1], (0.5, 1000, 500, True), "convex hulls: 1000 km North Atlantic / 500 km elsewhere")]:
    ax.pcolormesh(glon, glat, np.ma.masked_less(freq, 0.05), cmap="magma_r", vmin=0, vmax=3, shading="auto")
    ax.contour(glon, glat, scen[key].astype(float), [0.5], colors="b", linewidths=1)
    ax.plot(cpts[::4, 0], cpts[::4, 1], "k,")
    ax.set_xlim(-180, 180); ax.set_ylim(-50, 60); ax.set_aspect("equal")
    ax.set_title(f"TC belts (blue), f >= 0.5 storms/yr within {TC_RADIUS_KM:.0f} km: {t}")
fig.savefig(os.path.join(outdir, "belt_scenarios.png"), dpi=100)

# ------------------------------------------- size function raster for OceanMesh2D
# h = min(25, 10 + G d_coast, 12 + G d_tc, 5 + G max(d_us - 100, 0)) km, so it is graded by construction
SZ_RES = 0.05
SZ_MIN_ISLAND_KM2 = 25.0
G = 0.15
print("size function raster ...", flush=True)
slon = np.arange(-180 + SZ_RES / 2, 180, SZ_RES)
slat = np.arange(-90 + SZ_RES / 2, 90, SZ_RES)


def dist_km(tree, qlon, qlat):
    d, _ = tree.query(xyz(qlon, qlat), workers=4)
    return 2 * R * np.arcsin(np.clip(d / 2, 0, 1))


r5 = shapefile.Reader(os.path.join(gshhs_dir, "h", "GSHHS_h_L5"))
ant = np.concatenate([np.asarray(s.points) for s in r5.iterShapes()])
ant = ant[ant[:, 1] > -85]  # drop the pole closure
coast = np.concatenate([p for p, a in l1h if a >= SZ_MIN_ISLAND_KM2] + [ant])
coast_tree = cKDTree(xyz(coast[:, 0], coast[:, 1]))
us_tree = cKDTree(xyz(us_pts[:, 0], us_pts[:, 1]))
tcm = case_mask(TC_CHOSEN, *TC_CASES[0])
tc_tree = cKDTree(xyz(GX[tcm], GY[tcm]))


def size_km(qlon, qlat):
    h = np.minimum(25.0, 10 + G * dist_km(coast_tree, qlon, qlat))
    h = np.minimum(h, 12 + G * np.maximum(dist_km(tc_tree, qlon, qlat) - 0.5 * GRID * 111, 0))
    return np.minimum(h, 5 + G * np.maximum(dist_km(us_tree, qlon, qlat) - US_BAND_KM, 0))


hsz = np.empty((slat.size, slon.size), dtype=np.float32)
for j0 in range(0, slat.size, 400):
    LO, LA = np.meshgrid(slon, slat[j0:j0 + 400])
    hsz[j0:j0 + 400] = size_km(LO.ravel(), LA.ravel()).reshape(LO.shape)
n_sz = np.sum(A / size_km(lon, lat) ** 2) / cal
lines = [f"size raster {tag(*TC_CASES[0])}: {n_sz/1e6:.2f} M nodes estimated on wu025r004 nodes "
         f"(TC belts graded outward at {G})"]
print(lines[0], flush=True)
open(os.path.join(outdir, "estimate.txt"), "a").write("\n" + lines[0] + "\n")

import netCDF4
with netCDF4.Dataset(os.path.join(outdir, f"sizefx_{tag(*TC_CASES[0])}.nc"), "w") as nc:
    nc.createDimension("lon", slon.size)
    nc.createDimension("lat", slat.size)
    nc.createVariable("lon", "f8", ("lon",))[:] = slon
    nc.createVariable("lat", "f8", ("lat",))[:] = slat
    v = nc.createVariable("h", "f4", ("lat", "lon"), zlib=True)
    v.units = "m"
    v.long_name = "target element size"
    v[:] = hsz * 1e3
    nc.description = (f"MESAWAVE size function: 25 km open, 10 km coast, 12 km TC belts ({tag(*TC_CASES[0])}, "
                      f"f >= {TC_CHOSEN}/yr), 5 km within {US_BAND_KM:.0f} km of US coasts, grade {G}")

fig, ax = plt.subplots(figsize=(14, 7), constrained_layout=True)
im = ax.imshow(hsz[::4, ::4], origin="lower", extent=[-180, 180, -90, 90], cmap="viridis", vmin=4, vmax=26)
fig.colorbar(im, ax=ax, label="km")
ax.set_title(f"Size function raster {tag(*TC_CASES[0])} (land not masked), ~{n_sz/1e6:.2f} M nodes")
fig.savefig(os.path.join(outdir, f"sizefx_{tag(*TC_CASES[0])}.png"), dpi=90)


# ------------------------- Antarctic ice front with the pole closure moved to 81S
# GSHHS closes the Antarctic halves through 90S, and the eastern half not even as a
# planar polygon (it jumps straight from 180E back to 0E). Rebuild each half as its
# coast from meridian to meridian, closed along 81S (outside the 80S mesh bbox) and
# densified so the closure projects as an arc in the north-polar stereographic plane.
CLAMP_LAT = -81.0


def close_at(pts, lat_c):
    ring = pts[:-1] if np.allclose(pts[0], pts[-1]) else pts
    ring = ring[ring[:, 1] > -85]
    jumps = np.where(np.abs(np.diff(np.r_[ring[:, 0], ring[0, 0]])) > 90)[0]
    assert jumps.size == 1, f"expected one meridian jump, found {jumps.size}"
    path = np.roll(ring, -(jumps[0] + 1), axis=0)
    lon_end, lon_start = path[-1, 0], path[0, 0]
    n = int(np.ceil(abs(lon_end - lon_start) / 0.5))
    closure = np.c_[np.linspace(lon_end, lon_start, n + 1), np.full(n + 1, lat_c)]
    return np.vstack([path, closure, path[:1]])


r5f = shapefile.Reader(os.path.join(gshhs_dir, "f", "GSHHS_f_L5"))
w5 = shapefile.Writer(os.path.join(outdir, "GSHHS_f_L5_clamp81"), shapeType=shapefile.POLYGON)
w5.fields = r5f.fields[1:]
ant_halves = []
for sr in r5f.iterShapeRecords():
    pts = np.asarray(sr.shape.points)
    if pts[:, 1].min() < -85:
        pts = close_at(pts, CLAMP_LAT)
        ant_halves.append(Polygon(pts))
    w5.poly([pts.tolist()])
    w5.record(*sr.record)
w5.close()
for q in ant_halves:
    print(f"  Antarctic half: valid {q.is_valid}, lon {q.bounds[0]:.1f}..{q.bounds[2]:.1f}, "
          f"contains (+-90,-80): {contains_xy(q, 90, -80)}/{contains_xy(q, -90, -80)}, "
          f"contains ocean (+-90,-60): {contains_xy(q, 90, -60)}/{contains_xy(q, -90, -60)}", flush=True)
with open(os.path.join(gshhs_dir, "f", "GSHHS_f_L5.prj")) as fi, \
        open(os.path.join(outdir, "GSHHS_f_L5_clamp81.prj"), "w") as fo:
    fo.write(fi.read())


# ---------------------------------------------------------------- outputs
def cellify(ps):
    c = np.empty(len(ps), dtype=object)
    for i, p in enumerate(ps):
        c[i] = np.asarray(p.exterior.coords)
    return c


us_list = [(n, p) for n, ps in us_polys.items() for p in ps]
for (b_na, b_ot), tps in tc_case_polys.items():
    t = tag(b_na, b_ot)
    sio.savemat(os.path.join(outdir, f"nests_{t}.mat"), {
        "us_names": np.array([n for n, _ in us_list], dtype=object),
        "us_polys": cellify([p for _, p in us_list]),
        "tc_polys": cellify(tps),
        "us_band_km": US_BAND_KM, "tc_threshold": TC_CHOSEN,
        "tc_coast_km_na": b_na, "tc_coast_km_other": b_ot,
    })
    feats = [{"type": "Feature", "properties": {"kind": "us", "name": n}, "geometry": mapping(p)} for n, p in us_list]
    feats += [{"type": "Feature", "properties": {"kind": "tc"}, "geometry": mapping(p)} for p in tps]
    json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(outdir, f"nests_{t}.geojson"), "w"))
np.savez_compressed(os.path.join(outdir, "tc_raster.npz"), lon=glon, lat=glat, freq=freq, freq_na=freq_na,
                    dcoast=dcoast, **{f"mask_{th}": masks[th] for th in TC_THRESHOLDS})

fig, axs = plt.subplots(2, 1, figsize=(13, 13), constrained_layout=True)
im = axs[0].pcolormesh(glon, glat, np.ma.masked_less(freq, 0.05), cmap="magma_r", vmin=0, vmax=3, shading="auto")
fig.colorbar(im, ax=axs[0], label=f"TS-strength storms per year within {TC_RADIUS_KM:.0f} km")
for th, ls in zip(TC_THRESHOLDS, [":", "-", "--"]):
    axs[0].contour(glon, glat, masks[th].astype(float), [0.5], colors="b", linestyles=ls, linewidths=0.8)
axs[0].set_title(f"IBTrACS {TC_YEARS[0]}-{TC_YEARS[1]} exposure; blue: TC belts for f >= "
                 f"{TC_THRESHOLDS} (dotted, solid, dashed), {tag(*TC_CASES[0])} km of coast")
axs[1].scatter(lon[::3], lat[::3], c=h_chosen[::3], s=0.05, cmap="viridis", vmin=4, vmax=26, rasterized=True)
for p in tc_polys:
    axs[1].plot(*p.exterior.xy, "r", lw=0.8)
for _, p in us_list:
    axs[1].plot(*p.exterior.xy, "m", lw=0.8)
axs[1].set_title(f"Target size function on wu025r004 nodes ({tag(*TC_CASES[0])}, f >= {TC_CHOSEN}, 12 km); "
                 "red: TC nests, magenta: US 5 km nests")
for ax in axs:
    ax.set_xlim(-180, 180); ax.set_ylim(-80, 90); ax.set_aspect("equal")
fig.savefig(os.path.join(outdir, "regions.png"), dpi=110)
print("done", flush=True)
