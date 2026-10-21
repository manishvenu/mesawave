# Constructing CDEPS streams from MESACLIP

DATM, DOCN and DICE read MESACLIP through XML stream definitions. Each stream points at the
MESACLIP files for one variable ([MESACLIP experiments](mesaclip_experiments.md#files-and-history-streams))
and names the field it fills
([Variables the models can request](stream_data_requirements.md)). This page covers which
variable fills which field, the time settings, the meshes, and where the XML comes from.

## Variable mapping

GDEX files hold one variable each, so there is one stream per variable. Each stream's `<var>` is
`name_in_file name_in_model`. The `mesaclip` datamodes then convert or combine some fields; the
formulas are in [Adding MESACLIP to CDEPS](adding_mesaclip_to_cdeps.md#datamode-code).

**DATM**

| Stream field | MESACLIP variable | History file | In the datamode |
|---|---|---|---|
| `Sa_u`, `Sa_v` | `UBOT`, `VBOT` | `cam.h2` | as read; also sent to WW3 as `Sa_u10m`, `Sa_v10m` |
| `Sa_z` | `ZBOT` | `cam.h2` | as read |
| `Sa_tbot` | `TREFHT` | `cam.h2` | as read (2 m stand-in for the lowest level); `Sa_ptem` = `Sa_tbot` |
| `Sa_shum` | `QREFHT` | `cam.h2` | as read (2 m stand-in) |
| `Sa_pbot` | `PS` | `cam.h2` | as read (surface stand-in); used for `Sa_dens` |
| `Sa_pslv` | `PSL` | `cam.h2` | as read |
| `Faxa_lwdn` | `FLDS` | `cam.h4` | as read |
| `Faxa_swvdf`, `Faxa_swndf` | `SOLSD`, `SOLLD` | `cam.h4` | as read (diffuse visible, near-IR) |
| `Faxa_swdn` | `FSDS` | `cam.h4` | direct bands = `FSDS` − diffuse, split 0.28 : 0.31 |
| `Faxa_prect`, `Faxa_precc`, `Faxa_precsc`, `Faxa_precsl` | `PRECT`, `PRECC`, `PRECSC`, `PRECSL` | `cam.h4` | split into rain and snow, m/s → kg/m²/s |

**DOCN**

| Stream field | MESACLIP variable | History file | In the datamode |
|---|---|---|---|
| `So_t` | `SST` | `pop.h.nday1` | °C → K |
| `So_s` | `SSS` | `pop.h.nday1` | kg/kg → g/kg (= psu) |
| `So_u`, `So_v` | `U1_1`, `V1_1` | `pop.h.nday1` | cm/s → m/s; not rotated (see [below](#meshes-and-remapping)) |

**DICE**

| Stream field | MESACLIP variable | History file | In the datamode |
|---|---|---|---|
| `Si_ifrac` | `aice_d` | `cice.h1` | % → fraction |

## Stream parameters

The time settings depend on the history file. Tag meanings are in the
[CDEPS streams docs](https://escomp.github.io/CDEPS/versions/master/html/streams.html).

| Tag | cam.h2 | cam.h4 | pop.h.nday1 | cice.h1 |
|-----|--------|--------|-------------|---------|
| `taxmode` | `limit` | `limit` | `limit` | `limit` |
| `tintalgo` | `linear` | `nearest` | `nearest` | `nearest` |
| `offset` (s) | `0` | `-10800` | `-43200` | `-43200` |
| `readmode` | `single` | `single` | `single` | `single` |
| `dtlimit` | `1.e30` | `1.e30` | `1.e30` | `1.e30` |

**`tintalgo` and `offset`:** `cam.h2` fields are snapshots (no `cell_methods`),
so they are interpolated linearly. `cam.h4`, `pop.h.nday1` and `cice.h1` fields
are means (`cell_methods = "time: mean"`) stamped at the end of their window
(`time_bnds` upper bound equals `time`). A negative offset of half a window moves
each stamp to the middle of its window, and `nearest` then picks the mean whose
window contains the model time.

**Years:** `year_first` and `year_last` are `DATM_YR_START` and `DATM_YR_END`, which default to
the scenario's whole data range, and `year_align` equals `year_first`. So model years are data
years, and a run can start anywhere inside the range.

**`taxmode`:** `limit` stops the run if the model time leaves
`year_first`–`year_last`, instead of wrapping around (`cycle`) or holding the end
values (`extend`). Keep `year_first` at the dataset's first year, not the run's,
so a 1950 start is inside the data. A run starting on a dataset's first day
(e.g. RCP runs on 2006-01-01) is before the first daily record (00:00 on
2 January) and stops; start it on 2 January or use `extend` for that run.

**`dtlimit`:** `1.e30` turns off CDEPS's check for gaps in the time axis, so a
missing file is interpolated across without an error. `add_mesaclip_to_cesm.py`
reports missing files per member.

## Meshes and remapping

| History files | Mesh | `mapalgo` |
|---|---|---|
| `cam.h2`, `cam.h4` | `share/meshes/ne120np4_ESMFmesh_cdf5_c20211018.nc` | `bilinear` |
| `pop.h.nday1`, `cice.h1` | `share/meshes/tx0.1v2_ESMFmesh_cd5_c20210105.nc` | `bilinear` |

Mesh paths are under CESM inputdata. The WW3 mesh is set in WW3, not in these streams.

**Winds** need no rotation: CAM-SE's `UBOT` and `VBOT` are already east/north.

**Currents** are not yet rotated. POP's `U1_1` and `V1_1` follow the tripole grid's axes, which
match east/north south of about 29°N and turn by up to 90° in the Arctic. They also sit on U
points but are read on the T-point mesh. The streams' `vectors` tag can't fix this: CDEPS
assumes vector input is already east/north and rotates by longitude only
(`dshr_strdata_mod.F90`).

## Where the stream XML comes from

`code/claude/mesaclip.py` holds the tables on this page: scenarios, history files and their time
settings, and the field mapping. `code/claude/add_mesaclip_to_cesm.py` writes them into CDEPS's
`stream_definition_{datm,docn,dice}.xml`, with `$DATM_MESACLIP_CASE` in every file path and
`$DATM_YR_START`/`END`/`ALIGN` for the years. The case's namelist build fills those in. Every
file is listed, because GDEX file names hold date ranges that CDEPS can't template.

`code/claude/generate_{datm,docn,dice}_streams.py` write blank CPLHIST-style templates and hold the
lists of fields each data model must supply. The MESACLIP modes don't use their output.
