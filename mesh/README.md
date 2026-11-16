# mesh: MESAWAVE WW3 unstructured mesh (wu025r005)

The in-house global WW3 mesh, from Alper Altuntas's project, handed over 2026-11-10.
Handover page (method, status, remaining steps):
https://claude.ai/artifact/SoixsKGcu8FmFGwxruz6yq?sk=h8-kIQFpa46NpAlC69tH-w
Plain-English walkthrough of how the mesh is made:
https://claude.ai/artifact/9jh8PS2qCUT2TfmHYPtbCr

Code is in git here. Large data stays in `/glade/work/manishrv/ww3_mesh/` and is linked in
(see Data). Builds, grid inputs and plots go to `$SCRATCH/mesawave_mesh/` (purged: copy anything
you want to keep to work).

## Layout

| Path | What |
|---|---|
| `mesawave_mesh/` | The pipeline: `regions.py` (size raster), `make_mesh.m` + `run_mesh.sh` (mesh), `check_mesh.py` + `diag/` (checks), `make_grid_inp.sh` (WW3 inputs) |
| `OceanMesh2D/` (link) | OceanMesh2D clone (Projection branch, 754d69a) with Alper's `@meshgen/meshgen.m` edit; `git diff` there shows it. `make_mesh.m` finds it at `../OceanMesh2D` |
| `data/GEBCO_2024_coarse_x4.nc` (link) | Bathymetry |
| `tools/` | From Alper's `cesm3_0_beta09.ww3` sandbox: `ww3_msh_to_esmf.py`, `plot_ww3_unstr.py`, `ww3_scaling_plot.py`, `latlon_to_esmf.py`; `derecho_ww3_env.sh` (the wu025r004 case's module env, which `ww3_grid` was built in). Ours: `msh_to_ptb.py` (any `.msh`, e.g. Ali's, to a `_ptb.mat` the `diag/` scripts read), `defect_compare.py` and `quality_compare.py` (5/7 nodes and triangle quality, several meshes side by side), `icos_rotation.py` (picks the icosahedron's orientation), `stage_grid.sh` (a build as CESM's `wu025r005`, see "In CESM") |
| `tools/grid_inp_template/` (link) | `ww3_grid` binary + namelists |
| `wu025r005_v2/` (link) | Alper's latest mesh (2026-11-10, 1,285,928 nodes), copied off his scratch: `build/wu025r005_v2/` and `grid_inp.wu025r005/` (`mod_def.ww3`, `wu025r005_ESMFmesh.nc`) |
| `smoke_test.pbs` | Whole pipeline on a coarse mesh; rerun to check the setup still works. Passed 2026-11-13 (job 8177725, ~11 min): 79,546 nodes, `ww3_grid` exit 0, ESMF mesh written |
| `icos_test.pbs` | Builds an icosahedral-start mesh and compares it with a rows mesh (see Experiment) |

## Data

These are symlinks into `/glade/work/manishrv/ww3_mesh/` and are git-ignored (`.gitignore`
here). In a fresh clone, recreate them from this folder:

```bash
W=/glade/work/manishrv/ww3_mesh
ln -s $W/OceanMesh2D OceanMesh2D; ln -s $W/data data; ln -s $W/wu025r005_v2 wu025r005_v2
ln -s $W/mesawave_mesh/data mesawave_mesh/data; ln -s $W/mesawave_mesh/regions mesawave_mesh/regions
ln -s $W/mesawave_mesh/plots mesawave_mesh/plots; ln -s $W/tools/grid_inp_template tools/grid_inp_template
```

`mesawave_mesh/regions/` holds what `regions.py` writes (the size rasters, the clamped Antarctic
coastline) and `mesawave_mesh/plots/` holds Alper's reference plots. Old job logs are in
`/glade/work/manishrv/ww3_mesh/logs/`.

## Changes from Alper's copy

`diff -r /glade/work/altuntas/ww3.input/mesh/mesawave_mesh mesawave_mesh`:
`make_mesh.m` reads GEBCO from `data/`, `make_grid_inp.sh` uses `tools/` instead of his
scratch case and sandbox, and `run_mesh.sh` loads `ncarenv/25.10` before MATLAB.

## Experiment: icosahedral starting points

2026-11-13: `make_mesh.m` and `run_mesh.sh` take an optional 4th argument,
`rows` (default, Alper's latitude rows) or `icos` (`initial_points_icos`: one subdivided
icosahedron per size level, rotated by `tools/icos_rotation.py` so 8 of its 12 corners fall on land).
`icos_test.pbs` builds one and compares it with a rows mesh. At full size (`icos_s1`, against v2),
open-ocean 5/7 nodes fell from 5,041 to 1,464, and the deep ones (more than 5 spacings from any coast or
refined zone) from 2,693 to 2. Defects at the edges of the 25 km zone remain, because changing size needs them.
The cost: open-ocean triangles are slightly less equilateral (median quality 0.994, against 0.9996), because
DistMesh's 100 iterations don't fully relax the icosahedron's starting stretch. `tools/quality_compare.py`
measures this. In the resolution map the stretch shows as finer (~23 km) lines along the icosahedron
edges and coarser (~27 km) face centres. The fix to try next is an equal-area starting map.
`defect_compare.py` shows the stretch as the open-ocean edge-length spread: p5–p95 23.3–26.8 km for
`icos_s1`, against 24.1–26.0 km for v2. SCALE 4 builds don't show it (93.4–108.3 km, against 93.1–109.6 km
for rows), so test it at SCALE 1.

2026-11-16: `run_mesh.sh` and `make_mesh.m` take an optional 5th argument, ITMAX (DistMesh iterations,
default 100), and `icos_test.pbs` reads `ITMAX`. `icos_s1_it700` (job 8205552) rebuilds `icos_s1` with 700
iterations, to see whether more shaking evens out the stretch.

Still read from Alper's space: Ali's wu025r004 mesh, only for comparisons
(`/glade/work/altuntas/ww3.input/ABDOLALI_grid/Global_setup/Global_WIS_option3.msh`).

## Running

Run everything on Derecho compute nodes (develop queue), charged to NCGD0039. Python is
NPL with `-I`. `qcmd` holds your terminal until the job ends; for long runs, put the
command in a PBS script like `smoke_test.pbs` and `qsub` it.

```bash
cd ~/documents/mesawave/mesh/mesawave_mesh
PY="/glade/u/apps/opt/conda/envs/npl/bin/python -I"
Q="qcmd -A NCGD0039 -q develop"
```

**1. Size raster** (edit `TC_CASES`, `TC_HULL`, `TC_CHOSEN`, `US_BAND_KM` at the top of `regions.py`):

```bash
$Q -l select=1:ncpus=4:mem=80GB -l walltime=01:00:00 -- bash -c "cd $PWD && $PY regions.py \
  ../OceanMesh2D/datasets/GSHHS_shp data/ibtracs/ibtracs.since1980.list.v04r01.csv \
  data/audit_nodes.npz regions > regions.log 2>&1"
```

**2. Mesh**: `run_mesh.sh PREFIX SCALE [SIZEFILE] [rows|icos] [ITMAX]`. SCALE 1 = production (~50 min),
2 = twin (~20 min), 4 = quick test (~35 min, ~80k nodes). Output: `$SCRATCH/mesawave_mesh/build/PREFIX/`.

```bash
$Q -l select=1:ncpus=16:mem=200GB -l walltime=06:00:00 -- $PWD/run_mesh.sh try1 4
```

**3. Checks** (spacing vs target, regularity, 5/7-neighbour map):

```bash
P=$SCRATCH/mesawave_mesh/build/try1/try1_ptb.mat     # or ../wu025r005_v2/build/wu025r005_v2/wu025r005_v2_ptb.mat
F=regions/sizefx_na1000_ot500_hull.nc
ALI=/glade/work/altuntas/ww3.input/ABDOLALI_grid/Global_setup/Global_WIS_option3.msh
O=$SCRATCH/mesawave_mesh/plots; mkdir -p $O
$Q -l select=1:ncpus=4:mem=80GB -l walltime=01:00:00 -- bash -c "cd $PWD && \
  $PY check_mesh.py $P $F 4 $O/spacing.png && $PY diag/noise_tc.py $P $F $ALI && \
  $PY diag/defects.py $P $F $O/defects.png"
```

The `4` in `check_mesh.py` is the SCALE the mesh was built with.

**4. WW3 grid inputs** (`mod_def.ww3` and `PREFIX_ESMFmesh.nc`):

```bash
G=$SCRATCH/mesawave_mesh/grid_inp.try1
mkdir -p $G && cp ../tools/grid_inp_template/* $G/
ln -sfn $SCRATCH/mesawave_mesh/build/try1/try1.ww3 $G/mesh.msh
$Q -l select=1:ncpus=2:mem=60GB -l walltime=00:45:00 -- $PWD/make_grid_inp.sh $G try1
```

**5. Plot**:

```bash
$Q -l select=1:ncpus=2:mem=40GB -l walltime=00:30:00 -- $PY ../tools/plot_ww3_unstr.py \
  --mesh $G/mesh.msh --outdir $SCRATCH/mesawave_mesh/plots --title try1 \
  --zoom "Gulf:-98,-80,18,31" --zoom "Alaska:-170,-130,52,72"
```

## In CESM

`wu025r005` is registered (uncommitted) in the sandbox `/glade/work/manishrv/installs/CESM_wu2r05`, next to
`wu2r05`: `components/ww3/cime_config/config_component.xml` and `namelist_definition_ww3.xml` (300 s
timesteps, as Alper's `wu025r004`), and `ccs_config/component_grids_nuopc.xml`. Every path points at
`/glade/work/manishrv/ww3_mesh/grid_inp/wu025r005`, a link to one staged build in that folder, so swapping the
mesh needs no re-registration and no new case. The smoke-run case is `~/croc_cases/mesaclip_ww3_wu025r005`
(MESACLIP HIST member 010 from 2000-01-01, DOCN/DICE on the wave mesh; `replay.sh` there).

To try another build in the case (a compute-node job, ~10 min; the 2nd argument makes `mod_def.ww3` with the
case's own `ww3_grid`, so it matches the case's WW3 build):

```bash
cd ~/documents/mesawave/mesh
qsub -N ww3_stage -A NCGD0039 -q develop -l select=1:ncpus=2:mem=60GB -l walltime=00:45:00 -j oe -o $PWD/ \
  -- $PWD/tools/stage_grid.sh BUILD ~/croc_cases/mesaclip_ww3_wu025r005
```

then resubmit the case. The case sets `WW3_MODDEF` to the staged `mod_def.ww3`, which `buildnml` copies
whenever it differs; with `WW3_GRID_INP_DIR` alone, `buildnml` would keep the first mesh's files in
`$RUNDIR/ww3_moddef_create` and run `ww3_grid` on a login node. `WAV_NX`, `OCN_NX` and `ICE_NX` stay at the
first build's node count (1,291,302, `icos_s1`); the data models don't use them, and the mediator only uses them for
history dimensions (it warns when they don't match).

## Gotchas

- MATLAB R2024b on Derecho needs `ncarenv/24.12` or newer, but your login loads
  `ncarenv/23.09`, so `run_mesh.sh` loads `ncarenv/25.10` first. Without that the job fails
  at once with "exist but cannot be loaded as requested".
- "too many iterations, exit" in the mesh log is normal: OceanMesh2D always stops at its
  100-iteration cap (Alper's v2 log has it too). `ww3_grid`'s CICE0.NE.CICEN warning is also in
  his v2 log, and `ww3_grid` corrects the parameter itself.
- WW3 timesteps come from `wav_in`, not `ww3_grid.nml`: change them in
  `namelist_definition_ww3.xml` or `user_nl_ww3`.
- Don't build in, or run `git-fleximod update` in, Alper's `cesm3_0_beta09.ww3` sandbox, and
  leave his `cesm3_0_alpha11b.sbx` alone.
