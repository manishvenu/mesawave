"""Generate a CPLHIST-style datm.streams.xml for MESACLIP.

Streams are grouped like DATM's CPLHIST streams. Anything unknown (file
variable names, paths, years, ...) is written blank.
"""

import argparse

from cdeps_streams import blank_streams, write_streams

# Grouped like CPLHISTForcing.* in CDEPS datm/cime_config/stream_definition_datm.xml.
STREAMS = {
    "MESACLIP.Solar": ["Faxa_swndr", "Faxa_swvdr", "Faxa_swndf", "Faxa_swvdf"],
    "MESACLIP.nonSolarFlux": [
        "Faxa_rainc",
        "Faxa_rainl",
        "Faxa_snowc",
        "Faxa_snowl",
        "Faxa_lwdn",
    ],
    "MESACLIP.State": [
        "Sa_z",
        "Sa_tbot",
        "Sa_ptem",
        "Sa_shum",
        "Sa_pbot",
        "Sa_dens",
        "Sa_pslv",
    ],
    "MESACLIP.Wind": ["Sa_u", "Sa_v", "Sa_u10m", "Sa_v10m"],
}

# CPLHIST requires every field above except the 10 m winds
# (datm_datamode_cplhist_mod.F90). WW3 needs the 10 m winds, which CPLHIST
# doesn't export yet. Sa_topo is also required, but comes from the
# DATM_TOPO stream that buildnml adds.
REQUIRED = [field for fields in STREAMS.values() for field in fields]


def write_datm_streams(streams, path):
    """Write datm.streams.xml, checking every required field is provided."""
    write_streams(streams, path, required=REQUIRED)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", default="datm.streams.xml")
    args = parser.parse_args()
    write_datm_streams(blank_streams(STREAMS), args.output)
