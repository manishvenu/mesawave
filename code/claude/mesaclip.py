"""MESACLIP on GDEX: scenarios, default cases, and the DATM/DOCN field maps.

The single source of truth for add_mesaclip_to_cesm.py.
"""

import os

GDEX = "/glade/campaign/collections/gdex/data"
DIN_LOC_ROOT = "/glade/campaign/cesm/cesmdata/inputdata"  # Derecho/Casper
CASE_VAR = "$DATM_MESACLIP_CASE"

# Scenario -> (GDEX dataset, default case, first year, last year).
# The years are the ones every usable member stores under the same file names:
# RCP runs end in different years, so the 2100 file name varies by member, and for
# RCP6.0 so does the 2096-2100 ocean file, hence 2095.
SCENARIOS = {
    "HIST": (
        "d651007",
        "b.e13.BHISTC5.ne120_t12.cesm-ihesp-hires1.0.46-1920-2005.010",
        1920,
        2005,
    ),
    "RCP26": ("d651043", "b.e13.BRCP26C5.ne120_t12.cesm-ihesp-hires1.0.42.003", 2006, 2099),
    "RCP45": ("d651043", "b.e13.BRCP45C5.ne120_t12.cesm-ihesp-hires1.0.42.003", 2006, 2099),
    "RCP60": (
        "d651008",
        "b.e13.BRCP60C5.ne120_t12.cesm-ihesp-hires1.0.46-2006-2100.010",
        2006,
        2095,
    ),
    "RCP85": (
        "d651009",
        "b.e13.BRCP85C5.ne120_t12.cesm-ihesp-hires1.0.46-2006-2100.010",
        2006,
        2099,
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
    """The default case's files, with its name replaced by $DATM_MESACLIP_CASE."""
    case = SCENARIOS[scenario][1]
    return [
        path.replace(case, CASE_VAR)
        for path in case_files(scenario, case, history, variable)
    ]


def stream(comp, scenario, field, case=None):
    """One stream as a dict for cdeps_streams.write_streams.

    Without a case, paths and years stay CESM variables, as written into the
    stream definition file. With a case, they're resolved the way buildnml
    resolves them for that case.
    """
    history, variable = FIELDS[comp][field]
    _, _, mesh, offset, tintalgo = SOURCES[history]
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
        "taxmode": "limit",
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


def missing_files(scenario, case):
    """File names the DATM and DOCN streams list that this case doesn't have."""
    dataset = SCENARIOS[scenario][0]
    missing = []
    for comp in FIELDS:
        for history, variable in FIELDS[comp].values():
            folder = f"{GDEX}/{dataset}/{case}/{SOURCES[history][0]}"
            have = set(os.listdir(folder)) if os.path.isdir(folder) else set()
            for path in stream_files(scenario, history, variable):
                name = os.path.basename(path).replace(CASE_VAR, case)
                if name not in have:
                    missing.append(name)
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
