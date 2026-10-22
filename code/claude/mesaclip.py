"""MESACLIP on GDEX: scenarios, default cases, and the DATM/DOCN field maps.

The single source of truth for add_mesaclip_to_cesm.py.
"""

import os

GDEX = "/glade/campaign/collections/gdex/data"
DIN_LOC_ROOT = "/glade/campaign/cesm/cesmdata/inputdata"  # Derecho/Casper
CASE_VAR = "$DATM_MESACLIP_CASE"

# Scenario -> (GDEX dataset, default case, first year, last year).
SCENARIOS = {
    "HIST": (
        "d651007",
        "b.e13.BHISTC5.ne120_t12.cesm-ihesp-hires1.0.46-1920-2005.010",
        1920,
        2005,
    ),
    "RCP26": ("d651043", "b.e13.BRCP26C5.ne120_t12.cesm-ihesp-hires1.0.42.003", 2006, 2100),
    "RCP45": ("d651043", "b.e13.BRCP45C5.ne120_t12.cesm-ihesp-hires1.0.42.003", 2006, 2100),
    "RCP60": (
        "d651008",
        "b.e13.BRCP60C5.ne120_t12.cesm-ihesp-hires1.0.46-2006-2100.010",
        2006,
        2100,
    ),
    "RCP85": (
        "d651009",
        "b.e13.BRCP85C5.ne120_t12.cesm-ihesp-hires1.0.46-2006-2100.010",
        2006,
        2100,
    ),
}

# History files read -> (folder in the case, file tag, mesh, time offset (s), tintalgo).
# h2 snapshots are interpolated linearly. h4, nday1, and nday1_ice means are stamped at
# the end of their window, so shift them back half a window and use the nearest one.
SOURCES = {
    "h2": (
        "atm/proc/tseries/hour_6",
        "cam.h2",
        "$DIN_LOC_ROOT/share/meshes/ne120np4_ESMFmesh_cdf5_c20211018.nc",
        0,
        "linear",
    ),
    "h4": (
        "atm/proc/tseries/hour_6",
        "cam.h4",
        "$DIN_LOC_ROOT/share/meshes/ne120np4_ESMFmesh_cdf5_c20211018.nc",
        -10800,
        "nearest",
    ),
    "nday1": (
        "ocn/proc/tseries/day_1",
        "pop.h.nday1",
        "$DIN_LOC_ROOT/share/meshes/tx0.1v2_ESMFmesh_cd5_c20210105.nc",
        -43200,
        "nearest",
    ),
    "nday1_ice": (
        "ice/proc/tseries/day_1",
        "cice.h1",
        "$DIN_LOC_ROOT/share/meshes/tx0.1v2_ESMFmesh_cd5_c20210105.nc",
        -43200,
        "nearest",
    ),
}

# Shortwave 6 h means use coszen, which spreads each mean over the window with the
# sun's angle; it takes the record's time as the window's start, so shift the h4
# end-of-window stamp back a whole window (CDEPS's JRA streams do the same).
COSZEN = {"FSDS", "SOLSD", "SOLLD"}

# Stream field -> (history file, MESACLIP variable). h2 (instantaneous) wherever it
# has the field; radiation and precipitation are only saved time-averaged, in h4.
# TREFHT/QREFHT/PS are 2 m / surface stand-ins for the lowest-level values, which
# MESACLIP doesn't save 6-hourly. The Faxa_prec* and Faxa_swdn fields are raw CAM
# values the mesaclip datamode converts (precipitation) or splits (shortwave).
FIELDS = {
    "datm": {
        "Sa_u": ("h2", "UBOT"),
        "Sa_v": ("h2", "VBOT"),
        "Sa_z": ("h2", "ZBOT"),
        "Sa_pslv": ("h2", "PSL"),
        "Sa_tbot": ("h2", "TREFHT"),
        "Sa_shum": ("h2", "QREFHT"),
        "Sa_pbot": ("h2", "PS"),
        "Faxa_swdn": ("h4", "FSDS"),
        "Faxa_lwdn": ("h4", "FLDS"),
        "Faxa_swvdf": ("h4", "SOLSD"),
        "Faxa_swndf": ("h4", "SOLLD"),
        "Faxa_prect": ("h4", "PRECT"),
        "Faxa_precc": ("h4", "PRECC"),
        "Faxa_precsc": ("h4", "PRECSC"),
        "Faxa_precsl": ("h4", "PRECSL"),
    },
    "docn": {
        "So_t": ("nday1", "SST"),
        "So_u": ("nday1", "U1_1"),
        "So_v": ("nday1", "V1_1"),
        "So_s": ("nday1", "SSS"),
    },
    "dice": {
        "Si_ifrac": ("nday1_ice", "aice_d"),
        "Si_vice": ("nday1_ice", "hi_d"),
    },
}


def mode(comp, scenario):
    """MESACLIP_HIST for datm, mesaclip_hist for docn/dice (each follows its own casing)."""
    return f"MESACLIP_{scenario}" if comp == "datm" else f"mesaclip_{scenario.lower()}"


def stream_name(scenario, variable):
    return f"MESACLIP_{scenario}.{variable}"


def case_files(scenario, case, history, variable):
    """GDEX files for one variable of one case that overlap the scenario's years."""
    dataset, _, first, last = SCENARIOS[scenario]
    folder = f"{GDEX}/{dataset}/{case}/{SOURCES[history][0]}"
    prefix = f"{case}.{SOURCES[history][1]}.{variable}."
    files = []
    for name in sorted(os.listdir(folder)):
        if name.startswith(prefix):
            start, end = name[len(prefix) :].split(".")[0].split("-")
            if int(start[:4]) <= last and int(end[:4]) >= first:
                files.append(f"{folder}/{name}")
    return files


def stream_files(scenario, history, variable):
    """One %daterange entry, which buildnml (stream_cdeps.py) expands to the case's
    files for the run's years."""
    dataset = SCENARIOS[scenario][0]
    folder, tag = SOURCES[history][:2]
    return [f"{GDEX}/{dataset}/{CASE_VAR}/{folder}/{CASE_VAR}.{tag}.{variable}.%daterange.nc"]


def stream(comp, scenario, field, case=None):
    """One stream as a dict for cdeps_streams.write_streams.

    Without a case, paths and years stay CESM variables, as written into the
    stream definition file. With a case, they're resolved the way buildnml
    resolves them for that case.
    """
    history, variable = FIELDS[comp][field]
    _, _, mesh, offset, tintalgo = SOURCES[history]
    if variable in COSZEN:
        offset, tintalgo = -21600, "coszen"
    _, _, first, last = SCENARIOS[scenario]
    if case:
        files = case_files(scenario, case, history, variable)
        years = (first, last, first)
        mesh = mesh.replace("$DIN_LOC_ROOT", DIN_LOC_ROOT)
    else:
        files = stream_files(scenario, history, variable)
        years = ("$DATM_YR_START", "$DATM_YR_END", "$DATM_YR_ALIGN")
    return {
        "name": stream_name(scenario, variable),
        # extend, not limit: averaged fields' first and last records sit up to 12 h
        # inside the year, and at a scenario's first or last day there is no file
        # beyond to bracket them. extend holds the edge record there.
        "taxmode": "extend",
        "tintalgo": tintalgo,
        "readmode": "single",
        "mapalgo": "bilinear",
        "dtlimit": "1.e30",
        "year_first": years[0],
        "year_last": years[1],
        "year_align": years[2],
        "vectors": "null",
        "meshfile": mesh,
        "lev_dimname": "null",
        "datafiles": files,
        "datavars": [(variable, field)],
        "offset": offset,
    }


def missing_years(scenario, case):
    """{variable: [years]} for years in the scenario that none of the case's files
    cover, judged from the date ranges in their names (as %daterange does)."""
    _, _, first, last = SCENARIOS[scenario]
    missing = {}
    for comp in FIELDS:
        for history, variable in FIELDS[comp].values():
            folder = f"{GDEX}/{SCENARIOS[scenario][0]}/{case}/{SOURCES[history][0]}"
            if not os.path.isdir(folder):
                missing[variable] = list(range(first, last + 1))
                continue
            covered = set()
            for path in case_files(scenario, case, history, variable):
                start, end = os.path.basename(path).split(".")[-2].split("-")
                # A file ending on Jan 1 (e.g. 2095010100-2096010100) stops at that year's start.
                end_year = int(end[:4]) - (end[4:8] == "0101")
                covered.update(range(int(start[:4]), end_year + 1))
            years = [y for y in range(first, last + 1) if y not in covered]
            if years:
                missing[variable] = years
    return missing


def members(scenario):
    """Every case in the scenario's GDEX dataset (same scenario tag as the default)."""
    dataset, default, _, _ = SCENARIOS[scenario]
    tag = default.split(".")[2]
    return sorted(
        case
        for case in os.listdir(f"{GDEX}/{dataset}")
        if case.startswith("b.e13") and case.split(".")[2] == tag
    )
