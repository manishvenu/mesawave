# MESACLIP experiments

MESACLIP is an NSF NCAR ensemble of CESM1.3 high-resolution runs (0.25° atmosphere,
0.1° ocean and sea ice) produced for the CESM High-Resolution Decadal Prediction (HRDP)
project. MESAWAVE forces WAVEWATCH III from this ensemble.

## Model grids

Confirmed from the NetCDF global attributes in the GDEX time-series files:

| Component | Grid name | Resolution |
|-----------|-----------|-----------|
| Atmosphere (CAM5-SE) | `ne120` (ne=120 spectral elements) | ~0.25° |
| Ocean (POP2) | `tx0.1v2` (tripole, 0.1° nominal) | ~0.1° |
| Sea ice (CICE) | `tx0.1v2` | ~0.1° |

## Available datasets

All datasets are on the NSF NCAR Research Data Archive (RDA). GLADE users access
them at `/glade/campaign/collections/rda/data/d651XXX/`.

| Scenario | RDA ID | Members | Period |
|----------|--------|---------|--------|
| PI control (perpetual 1850) | d651029 | 1 (500 yr) | — |
| Historical | d651007 | 10 (001–010) | 1920–2005 |
| RCP 6.0 | d651008 | 10 | 2006–2100 |
| RCP 8.5 | d651009 | 10 | 2006–2100 |
| RCP 4.5 + RCP 2.6 | d651043 | 1 each | 2006–2100 |

Historical data (d651007) is also mirrored on GDEX at
`/glade/campaign/collections/gdex/data/d651007/`.

## Case naming convention

```
b.e13.BHISTC5.ne120_t12.cesm-ihesp-hires1.0.46-1920-2005.010
│  │   │       │         │                   │         │
│  │   │       │         │                   period    member
│  │   │       │         model version
│  │   │       grid
│  │   compset (B = fully coupled, HIST = historical, C5 = CAM5)
│  CESM version
fully coupled
```

Member numbers run `001`–`010`. The model version suffix (e.g. `.44`, `.45`, `.46`)
varies by member; use the actual directory name when constructing paths.

## MESAWAVE run matrix

The table below maps each MESAWAVE production run to the MESACLIP source dataset.
Time slices are non-contiguous segments of the future scenario runs.

| MESAWAVE experiment | MESACLIP dataset | Members | Period(s) |
|---------------------|-----------------|---------|-----------|
| Historical | d651007 | 005, 009, 010 | 1950–2005 |
| RCP 2.6 | d651043 | 3 (planned) | 2006–2020, 2040–2060, 2080–2100 |
| RCP 4.5 | d651043 | 3 (planned) | 2006–2020, 2040–2060, 2080–2100 |
| RCP 6.0 | d651008 | 005, 009, 010 | 2006–2020, 2040–2060, 2080–2100 |
| RCP 8.5 | d651009 | 005, 009, 010 | 2006–2020, 2040–2060, 2080–2100 |

**Note:** RCP 2.6 and 4.5 currently have 1 member in MESACLIP (d651043); 3 members
are planned. Check the dataset before running.

## Output streams and frequencies

Each MESACLIP case produces four time-series streams. See
[Variable glossary](#variable-glossary) for the full variable list.

| Stream tag | Frequency | Type | Relevant CDEPS mode |
|------------|-----------|------|---------------------|
| `cam.h2` | 6-hourly | Instantaneous snapshot | DATM |
| `cam.h4` | 6-hourly | Time mean (stamped at window end) | DATM |
| `pop.h.nday1` | Daily | Time mean | DOCN |
| `cice.h1` | Daily | Time mean | DICE |

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
