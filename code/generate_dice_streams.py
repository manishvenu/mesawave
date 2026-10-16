"""Generate a dice.streams.xml for MESACLIP's sea ice.

DICE has no cplhist stream definition, so this holds the fields WW3 needs.
Anything unknown (file variable names, paths, years, ...) is written blank.
"""

import argparse

from cdeps_streams import blank_streams, write_streams

STREAMS = {"MESACLIP.ice": ["Si_ifrac", "Si_thick", "Si_floediam"]}

# WW3 needs concentration and thickness; floe diameter is optional. DICE's
# cplhist datamode reads Si_ifrac but not Si_thick or Si_floediam yet, and
# isn't wired into CESM (DICE_MODE is only ssmi/ssmi_iaf).
REQUIRED = ["Si_ifrac", "Si_thick"]


def write_dice_streams(streams, path):
    """Write dice.streams.xml, checking every required field is provided."""
    write_streams(streams, path, required=REQUIRED)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", default="dice.streams.xml")
    args = parser.parse_args()
    write_dice_streams(blank_streams(STREAMS), args.output)
