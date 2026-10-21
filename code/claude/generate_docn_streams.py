"""Generate a CPLHIST-style docn.streams.xml for MESACLIP.

Same fields as DOCN's cplhist stream. Anything unknown (file variable names,
paths, years, ...) is written blank.
"""

import argparse

from cdeps_streams import blank_streams, write_streams

# Same fields as the cplhist stream in CDEPS docn/cime_config/stream_definition_docn.xml.
STREAMS = {"MESACLIP.ocn": ["So_t", "So_u", "So_v", "So_bldepth"]}

# cplhist requires So_t (docn_datamode_cplhist_mod.F90); WW3 needs the
# currents. So_bldepth is optional.
REQUIRED = ["So_t", "So_u", "So_v"]


def write_docn_streams(streams, path):
    """Write docn.streams.xml, checking every required field is provided."""
    write_streams(streams, path, required=REQUIRED)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", default="docn.streams.xml")
    args = parser.parse_args()
    write_docn_streams(blank_streams(STREAMS), args.output)
