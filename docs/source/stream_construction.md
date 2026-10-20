# Constructing CDEPS streams from MESACLIP

MESACLIP data reaches CESM through three CDEPS data models: DATM (atmosphere),
DOCN (ocean), and DICE (sea ice). Each reads one or more XML stream definitions
that point at MESACLIP NetCDF files and map variables to coupler fields.

For the field-by-field coupling table see [Coupling fields](stream_data_requirements.md).
For a visual overview see [Coupling flow](coupling_flow.md).

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
long names for a given case.

## Stream parameters

Each CDEPS stream block requires several XML tags whose values depend on the
data frequency and timestamp convention.

| Tag | cam.h2 | cam.h4 | pop.h.nday1 | cice.h1 |
|-----|--------|--------|-------------|---------|
| `taxmode` | `extend` | `limit` | `limit` | `limit` |
| `tintalgo` | `linear` | `lower` | `lower` | `lower` |
| `readmode` | `single` | `single` | `single` | `single` |
| `dtlimit` | `1.5` | `1.5` | `1.5` | `1.5` |

**Why `taxmode` differs:** `cam.h2` holds instantaneous snapshots; CDEPS extends
the last known value forward in time (`extend`). `cam.h4` and the daily streams
hold period means stamped at the *end* of the averaging window; `limit` combined
with `tintalgo=lower` tells CDEPS to use the mean that closes at or after the
current time — equivalent to a backward-in-time lookup, which is correct for
end-stamped means.

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

## Variable glossary

Full variable list with units from the actual NetCDF files:

```bash
conda run -n dev_cd python -I code/describe_mesaclip_variables.py
# or for a specific member:
conda run -n dev_cd python -I code/describe_mesaclip_variables.py \
    --case b.e13.BHISTC5.ne120_t12.cesm-ihesp-hires1.0.46-1920-2005.005
```

### cam.h2 — 6-hourly instantaneous

| Variable | Units | Description |
|----------|-------|-------------|
| `UBOT` | m/s | Lowest model level zonal wind |
| `VBOT` | m/s | Lowest model level meridional wind |
| `ZBOT` | m | Lowest model level height |
| `U10` | m/s | 10 m wind speed (scalar magnitude only) |
| `PS` | Pa | Surface pressure |
| `PSL` | Pa | Sea level pressure |
| `TREFHT` | K | 2 m (reference height) temperature |
| `QREFHT` | kg/kg | 2 m specific humidity |
| `TS` | K | Surface radiative temperature |
| `PRECT` | m/s | Total precipitation rate |
| `FLUT` | W/m² | Upwelling LW at top of model |
| `IVT` | kg/m/s | Vertically integrated vapour transport |
| `uIVT`, `vIVT` | kg/m/s | IVT components |
| `TMQ` | kg/m² | Precipitable water |
| `T200`, `T500` | K | Temperature at 200/500 hPa |
| `U250`–`U925` | m/s | Zonal wind at pressure levels |
| `V250`–`V925` | m/s | Meridional wind at pressure levels |
| `Z250`, `Z500` | m | Geopotential height at 250/500 hPa |

### cam.h4 — 6-hourly time means

| Variable | Units | Description |
|----------|-------|-------------|
| `FLDS` | W/m² | Downwelling LW at surface |
| `FSDS` | W/m² | Downwelling SW at surface (total) |
| `SOLSD` | W/m² | Diffuse visible SW |
| `SOLLD` | W/m² | Diffuse near-IR SW |
| `FLDSC`, `FSDSC` | W/m² | Clear-sky LW/SW |
| `FLNS`, `FSNS` | W/m² | Net LW/SW at surface |
| `LHFLX`, `SHFLX` | W/m² | Latent/sensible heat flux |
| `PRECT` | m/s | Total precipitation |
| `PRECC` | m/s | Convective precipitation |
| `PRECSC` | m/s | Convective snow rate |
| `PRECSL` | m/s | Large-scale snow rate |
| `QFLX` | kg/m²/s | Surface water flux |
| `CLDTOT` | fraction | Total cloud fraction |
| `TREFHTMN`, `TREFHTMX` | K | Min/max 2 m temperature over period |

### pop.h.nday1 — daily ocean

| Variable | Units | Description |
|----------|-------|-------------|
| `SST` | °C | Surface potential temperature |
| `SSS` | g/kg | Surface salinity |
| `U1_1`, `V1_1` | cm/s | Surface (level 1) velocity |
| `U2_2`, `V2_2` | cm/s | Level 2 velocity |
| `SSH_2` | cm | Sea surface height |
| `HMXL`, `XMXL` | cm | Mixed-layer / max mixed-layer depth |
| `TAUX`, `TAUY` | dyne/cm² | Wind stress (grid-relative, tripole) |
| `SHF`, `SHF_QSW` | W/m² | Total / solar surface heat flux |
| `EVAP_F`, `PREC_F`, `SNOW_F`, `MELT_F`, `ROFF_F` | kg/m²/s | Freshwater flux components (coupler diagnostics) |
| `SALT_F` | kg/m²/s | Salt flux (coupler diagnostic) |
| `LWDN_F`, `LWUP_F`, `SENH_F`, `MELTH_F` | W/m² | Heat flux components (coupler diagnostics) |

**Note:** Fields ending in `_F` are fluxes that the coupler sent *to* POP in the
original coupled run. They are coupler diagnostics, not useful as DATM/DOCN inputs.

### cice.h1 — daily ice

| Variable | Units | Description |
|----------|-------|-------------|
| `aice_d` | % | Ice concentration |
| `hi_d` | m | Grid-cell mean ice thickness |
| `hs_d` | m | Grid-cell mean snow thickness |
| `Tsfc_d` | °C | Snow/ice surface temperature |
| `uvel_d`, `vvel_d` | cm/s | Ice velocity |
| `fswabs_d` | W/m² | Absorbed SW (ice + ocean) |
| `fswdn_d` | W/m² | Downward SW |
| `fswthru_d` | W/m² | SW transmitted through ice to ocean |
| `ice_present_d` | 1 | Fraction of period any ice was present |
