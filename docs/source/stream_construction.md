# Constructing CDEPS streams from MESACLIP

MESACLIP data reaches CESM through three CDEPS data models: DATM (atmosphere),
DOCN (ocean), and DICE (sea ice). Each reads one or more XML stream definitions
that point at MESACLIP NetCDF files and map variables to coupler fields.

For the field-by-field coupling table see [Coupling fields](stream_data_requirements.md).

## How MESACLIP files are organised

Each case produces one NetCDF file per variable per time chunk, named:

```
{case}.{tag}.{VARNAME}.{YYYYMM}-{YYYYMM}.nc
```

They live under:

```
{GDEX}/{case}/
  atm/proc/tseries/hour_6/   ← cam.h2 and cam.h4
  ocn/proc/tseries/day_1/    ← pop.h.nday1
  ice/proc/tseries/day_1/    ← cice.h1
```

Use `code/describe_mesaclip_variables.py` to list all variables with units and
long names for a given case, or see the
[variable glossary](mesaclip_experiments.md#variable-glossary).

## Stream parameters

`code/mesaclip.py` writes one stream per variable. The time settings depend on
the history file the variable comes from. Tag meanings are in the
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

**`taxmode`:** `limit` stops the run if the model time leaves
`year_first`–`year_last`, instead of wrapping around (`cycle`) or holding the end
values (`extend`). Set `year_first` to the dataset's first year, not the run's,
so a 1950 start is inside the data. A run starting on a dataset's first day
(e.g. RCP runs on 2006-01-01) is before the first daily record (00:00 on
2 January) and stops; start it on 2 January or use `extend` for that run.

**`dtlimit`:** `1.e30` turns off CDEPS's check for gaps in the time axis, so a
missing file is interpolated across without an error. `add_mesaclip_to_cesm.py`
reports missing files per member.

## Mesh files

| Data | Mesh file |
|------|-----------|
| `cam.h2`, `cam.h4` | ne120 atmosphere mesh (SE unstructured) |
| `pop.h.nday1` | tx0.1v2 ocean mesh (tripole) |
| `cice.h1` | tx0.1v2 ocean mesh (CICE uses the same grid) |

The WW3 unstructured mesh is set separately in the WW3 namelist, not in the
DATM/DOCN/DICE stream XML.

## Remapping algorithm (`mapalgo`)

| Source → Target | `mapalgo` |
|----------------|-----------|
| ne120 ATM → WW3/CICE/MOM6 | `bilinear` |
| tx0.1v2 OCN → WW3/CICE/MOM6 | `bilinear` |

Bilinear is appropriate for all scalar fields. **Wind components** (`UBOT`,
`VBOT`) and **currents** (`U1_1`, `V1_1`) are grid-relative vectors on their
native grids and require rotation to east/north before or after remapping —
this is not yet handled in the MESACLIP datamodes (see open questions in
CLAUDE.md).

## Year alignment

CDEPS stream blocks require `year_first`, `year_last`, and `year_align`. For
MESACLIP the data years equal the model years (no repeat-year forcing), so:

```xml
<year_first>1950</year_first>
<year_last>2005</year_last>
<year_align>1950</year_align>
```

The active scenario and member are controlled at runtime by the CESM case
variable `DATM_MESACLIP_CASE`, which the `mesaclip` datamodes read to
construct the file paths at model start. This means the stream XML files
contain the path template, not a hardcoded case name.

## Variable mapping

Each `<var>` entry in the stream XML is:

```xml
<var>name_in_file  name_in_model</var>
```

### DATM streams

**cam.h2** (6-hourly instantaneous):

| `name_in_file` | `name_in_model` | Notes |
|----------------|-----------------|-------|
| `UBOT` | `Sa_u` | ~60 m wind; stand-in for 10 m |
| `VBOT` | `Sa_v` | ~60 m wind; stand-in for 10 m |
| `ZBOT` | `Sa_z` | Level height for bulk formulae |
| `TREFHT` | `Sa_tbot` | 2 m temperature; stand-in for lowest level |
| `QREFHT` | `Sa_shum` | 2 m specific humidity; stand-in |
| `PS` | `Sa_pbot` | Surface pressure; stand-in for lowest-level P |
| `PSL` | `Sa_pslv` | Sea-level pressure |

**cam.h4** (6-hourly means):

| `name_in_file` | `name_in_model` | Notes |
|----------------|-----------------|-------|
| `FLDS` | `Faxa_lwdn` | Downwelling LW — direct |
| `FSDS` | — | Used to compute direct SW bands |
| `SOLSD` | `Faxa_swvdf` | Diffuse visible SW — direct |
| `SOLLD` | `Faxa_swndf` | Diffuse near-IR SW — direct |
| `PRECT` | — | Combined with component fields for rain/snow split |
| `PRECC` | — | Convective precipitation fraction |
| `PRECSC` | — | Convective snow fraction |
| `PRECSL` | — | Large-scale snow fraction |

The direct SW bands (`Faxa_swvdr`, `Faxa_swndr`) and precipitation
(`Faxa_rainc`, `Faxa_rainl`, `Faxa_snowc`, `Faxa_snowl`) are computed
in the `mesaclip` datamode from the above inputs. Potential temperature
(`Sa_ptem`) and air density (`Sa_dens`) are also computed from `TREFHT`,
`PS`, and `QREFHT`.

### DOCN stream (pop.h.nday1, daily)

| `name_in_file` | `name_in_model` | Unit conversion |
|----------------|-----------------|-----------------|
| `SST` | `So_t` | °C → K (+273.15) |
| `U1_1` | `So_u` | cm/s → m/s (×0.01) |
| `V1_1` | `So_v` | cm/s → m/s (×0.01) |

### DICE stream (cice.h1, daily)

| `name_in_file` | `name_in_model` | Unit conversion |
|----------------|-----------------|-----------------|
| `aice_d` | `Si_ifrac` | % → fraction (÷100) |

## Generating the stream XML

The scripts `code/generate_datm_streams.py`, `code/generate_docn_streams.py`, and
`code/generate_dice_streams.py` write CPLHIST-style CDEPS stream XML for a given
MESACLIP case. They use the shared writer `code/cdeps_streams.py`.

```bash
python code/generate_datm_streams.py
python code/generate_docn_streams.py
python code/generate_dice_streams.py
```

Review the output XML before placing it in a case. Leave any unknown tags blank
rather than guessing — CDEPS rejects blank `taxmode`, `mapalgo`, `tintalgo`, and
`readmode`, so fill those before a run.
