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
[Variable glossary](stream_construction.md#variable-glossary) for the full variable list.

| Stream tag | Frequency | Type | Relevant CDEPS mode |
|------------|-----------|------|---------------------|
| `cam.h2` | 6-hourly | Instantaneous snapshot | DATM |
| `cam.h4` | 6-hourly | Time mean (stamped at window end) | DATM |
| `pop.h.nday1` | Daily | Time mean | DOCN |
| `cice.h1` | Daily | Time mean | DICE |
