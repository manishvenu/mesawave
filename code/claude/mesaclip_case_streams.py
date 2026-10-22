"""List one MESACLIP member's own files in a case, so RCP runs can reach 2100.

usage: python mesaclip_case_streams.py CASEROOT SCENARIO MESACLIP_CASE [LAST_YEAR]

The MESACLIP stream definitions in CDEPS list only the years every member shares
file names for (to 2095 for RCP6.0, 2099 for the other RCPs). This writes
`<stream>:datafiles = ...` for every MESACLIP stream into CASEROOT's
user_nl_{datm,docn,dice}_streams, listing MESACLIP_CASE's files up to LAST_YEAR
(default 2100; 2005 for HIST). Earlier MESACLIP lines in those files are replaced.
Then set the years in the case, e.g. ./xmlchange DATM_YR_END=2100.
"""

import os
import sys

import mesaclip

caseroot, scenario, case = sys.argv[1:4]
last = int(sys.argv[4]) if len(sys.argv) > 4 else (2005 if scenario == "HIST" else 2100)

for comp, fields in mesaclip.FIELDS.items():
    lines = []
    for history, variable in fields.values():
        files = mesaclip.case_files(scenario, case, history, variable, last)
        if not files:
            sys.exit(f"{case} has no {variable} files")
        lines.append(f"{mesaclip.stream_name(scenario, variable)}:datafiles = {','.join(files)}\n")

    path = os.path.join(caseroot, f"user_nl_{comp}_streams")
    kept = []
    if os.path.exists(path):
        with open(path) as f:
            kept = [line for line in f if not line.startswith("MESACLIP_")]
    with open(path, "w") as f:
        f.writelines(kept + lines)
    print(f"{path}: {len(lines)} streams")

for variable, years in mesaclip.missing_years(scenario, case, last).items():
    print(f"  no {variable} files for {years[0]}-{years[-1]} ({len(years)} years)")
print(f"Now: ./xmlchange DATM_YR_END={last}")
