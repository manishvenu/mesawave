"""Regenerate the MESACLIP edits on the cdeps/ submodule (manishvenu/CDEPS, branch mesaclip).

Rewrites the compset modes, the DATM_MESACLIP_CASE variable and the streams (XML in
{datm,docn}/cime_config), and registers the mesaclip datamodes in each component's
cap and CMakeLists.txt. Each of those files is reset to BASE first, so rerunning
gives the same result; review and commit the diff on the mesaclip branch. The
datamode Fortran itself ({datm,docn}/*_datamode_mesaclip_mod.F90) is edited
directly on the branch and isn't touched here. Also reports which members the
streams fit.

    python code/claude/add_mesaclip_to_cesm.py [path/to/cdeps]   # default: the cdeps/ submodule
"""

import argparse
import os
import subprocess

import mesaclip
from cdeps_streams import missing_fields
from generate_datm_streams import REQUIRED as DATM_REQUIRED

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "stream-daterange"  # %daterange support, on cdeps1.0.101 (the tag CESM's crocodash branch uses)
TAG = "MESACLIP: added by mesawave add_mesaclip_to_cesm.py"
CMAKE = f"# {TAG}"
FILES = [
    "datm/cime_config/config_component.xml",
    "datm/cime_config/namelist_definition_datm.xml",
    "datm/cime_config/stream_definition_datm.xml",
    "datm/atm_comp_nuopc.F90",
    "datm/CMakeLists.txt",
    "docn/cime_config/config_component.xml",
    "docn/cime_config/namelist_definition_docn.xml",
    "docn/cime_config/stream_definition_docn.xml",
    "docn/ocn_comp_nuopc.F90",
    "docn/CMakeLists.txt",
    "dice/cime_config/config_component.xml",
    "dice/cime_config/namelist_definition_dice.xml",
    "dice/cime_config/stream_definition_dice.xml",
    "dice/ice_comp_nuopc.F90",
    "dice/CMakeLists.txt",
]
SCENARIOS = list(mesaclip.SCENARIOS)
# Fields the mesaclip datamode computes rather than reads.
DATM_DERIVED = [
    "Faxa_rainc",
    "Faxa_rainl",
    "Faxa_snowc",
    "Faxa_snowl",
    "Sa_ptem",
    "Sa_dens",
    "Faxa_swvdr",
    "Faxa_swndr",
    "Sa_u10m",
    "Sa_v10m",
]


def git(cdeps, *args, check=True):
    return subprocess.run(
        ["git", "-C", cdeps, *args], check=check, capture_output=True, text=True
    ).stdout


def reset(cdeps):
    """Restore our files to BASE, refusing if any has uncommitted changes."""
    if git(cdeps, "diff", "--name-only", "HEAD", "--", *FILES):
        raise SystemExit("uncommitted changes in files this script writes; commit or discard them first")
    git(cdeps, "restore", "--source", BASE, "--worktree", "--", *FILES)


def replace(text, old, new, count=1):
    if text.count(old) != count:
        raise ValueError(f"expected {count} of {old!r}")
    return text.replace(old, new)


def block(lines, indent, mark):
    return "".join(f"\n{indent}{line}" for line in ([mark] if mark else []) + lines)


def add_after_line(text, needle, lines, indent, mark=None, skip=0):
    """Add lines after the line containing needle (which must appear once), or
    after the line `skip` lines below it."""
    replace(text, needle, needle)  # checks it appears once
    end = text.index("\n", text.index(needle))
    for _ in range(skip):
        end = text.index("\n", end + 1)
    return text[:end] + block(lines, indent, mark) + text[end:]


def add_to_values(text, entry_id, lines, indent="      "):
    """Add <value> lines at the end of an entry's <values> block."""
    start = text.index(f'<entry id="{entry_id}">')
    end = text.index("</values>", start)
    if end > text.index("</entry>", start):
        raise ValueError(f"{entry_id} has no <values> block")
    end = text.rindex("\n", 0, end)
    return text[:end] + block(lines, indent, None) + text[end:]


def add_after_entry(text, entry_id, lines, indent="  "):
    start = text.index(f'<entry id="{entry_id}">')
    end = text.index("</entry>", start) + len("</entry>")
    return text[:end] + "\n" + block(lines, indent, None) + text[end:]


def add_case(text, call, case, new_call, case_indent):
    """Add a `case` block for the mesaclip datamode after an existing call and its
    ChkErr line."""
    lines = [case, f"   {new_call}", "   if (ChkErr(rc,__LINE__,u_FILE_u)) return"]
    return add_after_line(text, call, lines, case_indent, skip=1)


def stream_entry(stream):
    """A stream dict (see mesaclip.stream) in stream_definition_<comp>.xml format."""
    files = "\n".join(f"      <file>{path}</file>" for path in stream["datafiles"])
    variables = "\n".join(f"      <var>{a} {b}</var>" for a, b in stream["datavars"])
    return f"""  <stream_entry name="{stream["name"]}">
    <stream_meshfile>
      <meshfile>{stream["meshfile"]}</meshfile>
    </stream_meshfile>
    <stream_datafiles>
{files}
    </stream_datafiles>
    <stream_datavars>
{variables}
    </stream_datavars>
    <stream_lev_dimname>{stream["lev_dimname"]}</stream_lev_dimname>
    <stream_mapalgo>
      <mapalgo>{stream["mapalgo"]}</mapalgo>
    </stream_mapalgo>
    <stream_vectors>{stream["vectors"]}</stream_vectors>
    <stream_year_align>{stream["year_align"]}</stream_year_align>
    <stream_year_first>{stream["year_first"]}</stream_year_first>
    <stream_year_last>{stream["year_last"]}</stream_year_last>
    <stream_offset>{stream["offset"]}</stream_offset>
    <stream_tintalgo>
      <tintalgo>{stream["tintalgo"]}</tintalgo>
    </stream_tintalgo>
    <stream_taxmode>
      <taxmode>{stream["taxmode"]}</taxmode>
    </stream_taxmode>
    <stream_dtlimit>
      <dtlimit>{stream["dtlimit"]}</dtlimit>
    </stream_dtlimit>
    <stream_readmode>{stream["readmode"]}</stream_readmode>
  </stream_entry>
"""


def streams_xml(comp):
    def change(text):
        entries = "".join(
            stream_entry(mesaclip.stream(comp, s, field))
            for s in SCENARIOS
            for field in mesaclip.FIELDS[comp]
        )
        return replace(text, "\n</stream_data>", f"\n{entries}\n</stream_data>")

    return change


def streamslists(comp):
    return [
        f'<value {comp}_mode="{mesaclip.mode(comp, s)}">'
        + ",".join(mesaclip.stream_name(s, v) for _, v in mesaclip.FIELDS[comp].values())
        + "</value>"
        for s in SCENARIOS
    ]


def modifiers():
    return "".join(f"[%MESACLIP-{s}]" for s in SCENARIOS)


def descs():
    return [
        f'<desc option="MESACLIP-{s}"> MESACLIP {s} from GDEX {dataset} (mesaclip datamode)</desc>'
        for s, (dataset, *_) in mesaclip.SCENARIOS.items()
    ]


def datm_config(text):
    text = replace(text, '[%SIMPLE]">', f'[%SIMPLE]{modifiers()}">')
    text = add_after_line(text, '<desc option="CPLHIST">', descs(), "    ")
    text = replace(
        text,
        ",ERA5,SIMPLE</valid_values>",
        ",ERA5,SIMPLE," + ",".join(mesaclip.mode("datm", s) for s in SCENARIOS) + "</valid_values>",
    )
    text = add_to_values(
        text,
        "DATM_MODE",
        [f'<value compset="DATM%MESACLIP-{s}">{mesaclip.mode("datm", s)}</value>' for s in SCENARIOS],
    )
    for entry, value in (
        ("DATM_YR_START", lambda s: mesaclip.SCENARIOS[s][2]),
        ("DATM_YR_END", lambda s: mesaclip.SCENARIOS[s][3]),
        ("DATM_YR_ALIGN", lambda s: "$DATM_YR_START"),
        # Sa_topo isn't in MESACLIP, so use DATM's standard topography stream
        # (it's off by default for compsets without an active land model).
        ("DATM_TOPO", lambda s: "observed"),
    ):
        text = add_to_values(
            text, entry, [f'<value compset="DATM%MESACLIP-{s}">{value(s)}</value>' for s in SCENARIOS]
        )
    defaults = [
        f'    <value compset="DATM%MESACLIP-{s}">{case}</value>'
        for s, (_, case, *_) in mesaclip.SCENARIOS.items()
    ]
    return add_after_entry(
        text,
        "DATM_CPLHIST_CASE",
        [
            '<entry id="DATM_MESACLIP_CASE">',
            "  <type>char</type>",
            "  <valid_values></valid_values>",
            "  <default_value>UNSET</default_value>",
            '  <values match="last">',
            *defaults,
            "  </values>",
            "  <group>run_component_datm</group>",
            "  <file>env_run.xml</file>",
            "  <desc>MESACLIP case name on GDEX (picks the ensemble member) when DATM_MODE is MESACLIP_*</desc>",
            "</entry>",
        ],
    )


def datm_namelist(text):
    text = replace(text, ",CPLHIST,1PT</valid_values>", ",CPLHIST,1PT,MESACLIP</valid_values>")
    text = add_to_values(text, "streamslist", streamslists("datm"))
    return add_to_values(text, "datamode", ['<value datm_mode="MESACLIP">MESACLIP</value>'])


def datm_cap(text):
    text = add_after_line(
        text,
        "use datm_datamode_cplhist_mod , only : datm_datamode_cplhist_advance",
        [
            f"use datm_datamode_mesaclip_mod, only : datm_datamode_mesaclip_{name}"
            for name in ("advertise", "init_pointers", "advance")
        ],
        "  ",
    )
    text = replace(
        text, "'CLMNCEP','CPLHIST','GEFS','ERA5','SIMPLE')", "'CLMNCEP','CPLHIST','GEFS','ERA5','SIMPLE','MESACLIP')"
    )
    text = replace(  # restart read and write
        text,
        "'CLMNCEP','CPLHIST','ERA5','GEFS','SIMPLE')",
        "'CLMNCEP','CPLHIST','ERA5','GEFS','SIMPLE','MESACLIP')",
        count=2,
    )
    text = add_case(
        text,
        "call datm_datamode_cplhist_advertise(exportState, fldsExport, flds_scalar_name, rc)",
        "case ('MESACLIP')",
        "call datm_datamode_mesaclip_advertise(exportState, fldsExport, flds_scalar_name, rc)",
        "    ",
    )
    text = add_case(
        text,
        "call datm_datamode_cplhist_init_pointers(importState, exportState, sdat, rc)",
        "case('MESACLIP')",
        "call datm_datamode_mesaclip_init_pointers(importState, exportState, sdat, rc)",
        "       ",
    )
    return add_case(
        text,
        "call datm_datamode_cplhist_advance(rc)",
        "case('MESACLIP')",
        "call datm_datamode_mesaclip_advance(rc)",
        "    ",
    )


def cmake(comp):
    def change(text):
        return add_after_line(
            text,
            f" {comp}_datamode_cplhist_mod.F90",
            [f"{comp}_datamode_mesaclip_mod.F90"],
            "             ",
            CMAKE,
        )

    return change


def docn_config(text):
    text = replace(text, '[%MULTILEV-DOM]">', f'[%MULTILEV-DOM]{modifiers()}">')
    text = add_after_line(text, '<desc option="CPLHIST">', descs(), "    ")
    text = replace(
        text,
        ",multilev_cplhist</valid_values>",
        ",multilev_cplhist," + ",".join(mesaclip.mode("docn", s) for s in SCENARIOS) + "</valid_values>",
    )
    return add_to_values(
        text,
        "DOCN_MODE",
        [f'<value compset="_DOCN%MESACLIP-{s}">{mesaclip.mode("docn", s)}</value>' for s in SCENARIOS],
    )


def docn_namelist(text):
    text = replace(text, ",multilev_sstdata,multilev_cplhist</valid_values>", ",multilev_sstdata,multilev_cplhist,mesaclip</valid_values>")
    text = add_to_values(text, "datamode", ['<value docn_mode="mesaclip">mesaclip</value>'])
    return add_to_values(text, "streamslist", streamslists("docn"))


def docn_cap(text):
    text = add_after_line(
        text,
        "use docn_datamode_cplhist_mod          , only : docn_datamode_cplhist_advance",
        [
            f"use docn_datamode_mesaclip_mod         , only : docn_datamode_mesaclip_{name}"
            for name in ("advertise", "init_pointers", "advance")
        ],
        "  ",
    )
    text = replace(
        text,
        "'cplhist', 'sst_aquap_analytic', 'sst_aquap_constant', &",
        "'cplhist', 'mesaclip', 'sst_aquap_analytic', 'sst_aquap_constant', &",
    )
    text = replace(  # restart read and write
        text,
        "'cplhist', 'multilev', 'mulitilev_sstdata', 'multilev_cplhist')",
        "'cplhist', 'multilev', 'mulitilev_sstdata', 'multilev_cplhist', 'mesaclip')",
        count=2,
    )
    text = add_case(
        text,
        "call docn_datamode_cplhist_advertise(exportState, fldsExport, flds_scalar_name, rc)",
        "case('mesaclip')",
        "call docn_datamode_mesaclip_advertise(exportState, fldsExport, flds_scalar_name, rc)",
        "    ",
    )
    text = add_case(
        text,
        "call docn_datamode_cplhist_init_pointers(exportState, sdat, model_frac, rc)",
        "case('mesaclip')",
        "call docn_datamode_mesaclip_init_pointers(exportState, sdat, model_frac, rc)",
        "       ",
    )
    return add_case(
        text,
        "call  docn_datamode_cplhist_advance(sst_constant_value=sst_constant_value, rc=rc)",
        "case('mesaclip')",
        "call docn_datamode_mesaclip_advance(sst_constant_value=sst_constant_value, rc=rc)",
        "    ",
    )


def dice_config(text):
    text = replace(text, '[%IAF]">', f'[%IAF]{modifiers()}">')
    text = add_after_line(text, '<desc option="IAF">', descs(), "    ")
    text = replace(
        text,
        "ssmi,ssmi_iaf</valid_values>",
        "ssmi,ssmi_iaf," + ",".join(mesaclip.mode("dice", s) for s in SCENARIOS) + "</valid_values>",
    )
    return add_to_values(
        text,
        "DICE_MODE",
        [f'<value compset="DICE%MESACLIP-{s}">{mesaclip.mode("dice", s)}</value>' for s in SCENARIOS],
    )


def dice_namelist(text):
    text = replace(text, "ssmi,ssmi_iaf</valid_values>", "ssmi,ssmi_iaf,mesaclip</valid_values>")
    text = add_to_values(text, "datamode", ['<value dice_mode="mesaclip">mesaclip</value>'])
    return add_to_values(text, "streamslist", streamslists("dice"))


def dice_cap(text):
    text = add_after_line(
        text,
        "use dice_datamode_cplhist_mod , only : dice_datamode_cplhist_restart_write",
        [
            f"use dice_datamode_mesaclip_mod , only : dice_datamode_mesaclip_{name}"
            for name in ("advertise", "init_pointers", "advance", "restart_read", "restart_write")
        ],
        "  ",
    )
    text = replace(
        text,
        "case('ssmi','ssmi_iaf','cplhist')",
        "case('ssmi','ssmi_iaf','cplhist','mesaclip')",
    )
    # advertise: flds_i2o_per_cat attribute read + multiline call
    text = add_after_line(
        text,
        "call dice_datamode_cplhist_advertise(exportState, fldsexport, flds_scalar_name, rc)",
        [
            "case('mesaclip')",
            "   call NUOPC_CompAttributeGet(gcomp, name='flds_i2o_per_cat', value=cvalue, rc=rc)",
            "   if (ChkErr(rc,__LINE__,u_FILE_u)) return",
            "   read(cvalue,*) flds_i2o_per_cat  ! module variable",
            "   call dice_datamode_mesaclip_advertise(importState, exportState, fldsimport, fldsexport, &",
            "        flds_scalar_name, flds_i2o_per_cat, rc)",
            "   if (ChkErr(rc,__LINE__,u_FILE_u)) return",
        ],
        "    ",
        skip=1,
    )
    # init_pointers (uses chkerr, consistent with surrounding ssmi/cplhist blocks)
    text = add_after_line(
        text,
        "call dice_datamode_cplhist_init_pointers(exportState, sdat, rc)",
        [
            "case('mesaclip')",
            "   call dice_datamode_mesaclip_init_pointers(importState, exportState, sdat, flds_i2o_per_cat, rc)",
            "   if (chkerr(rc,__LINE__,u_FILE_u)) return",
        ],
        "       ",
        skip=1,
    )
    # restart_read: cplhist has no ChkErr after the call, insert immediately after
    text = add_after_line(
        text,
        "call dice_datamode_cplhist_restart_read(restfilm, rpfile, logunit, my_task, mpicom, sdat)",
        [
            "case('mesaclip')",
            "   call dice_datamode_mesaclip_restart_read(restfilm, rpfile, logunit, my_task, mpicom, sdat, rc)",
            "   if (ChkErr(rc,__LINE__,u_FILE_u)) return",
        ],
        "          ",
        skip=0,
    )
    # advance: multiline mesaclip call
    text = add_after_line(
        text,
        "call dice_datamode_cplhist_advance(sdat, rc)",
        [
            "case ('mesaclip')",
            "   call dice_datamode_mesaclip_advance(exportState, importState, cosarg, flds_i2o_per_cat, &",
            "        flux_swpf, flux_Qmin, flux_Qacc, flux_Qacc0, dt, logunit, restart_read, rc)",
            "   if (ChkErr(rc,__LINE__,u_FILE_u)) return",
        ],
        "    ",
        skip=1,
    )
    # restart_write: cplhist call spans two lines, skip past the closing paren line
    text = add_after_line(
        text,
        "call dice_datamode_cplhist_restart_write(rpfile, case_name, inst_suffix, target_ymd, target_tod, &",
        [
            "case ('mesaclip')",
            "   call dice_datamode_mesaclip_restart_write(rpfile, case_name, inst_suffix, target_ymd, target_tod, &",
            "        logunit, my_task, sdat, rc)",
            "   if (ChkErr(rc,__LINE__,u_FILE_u)) return",
        ],
        "       ",
        skip=1,
    )
    return text


EDITS = dict(
    zip(
        FILES,
        [
            datm_config,
            datm_namelist,
            streams_xml("datm"),
            datm_cap,
            cmake("datm"),
            docn_config,
            docn_namelist,
            streams_xml("docn"),
            docn_cap,
            cmake("docn"),
            dice_config,
            dice_namelist,
            streams_xml("dice"),
            dice_cap,
            cmake("dice"),
        ],
    )
)


def apply(cdeps):
    reset(cdeps)
    for relpath, change in EDITS.items():
        path = os.path.join(cdeps, relpath)
        with open(path) as f:
            text = change(f.read())
        with open(path, "w") as f:
            f.write(text)


def report_fields():
    provided = [{"datavars": [("", field) for field in [*mesaclip.FIELDS["datm"], *DATM_DERIVED]]}]
    missing = missing_fields(provided, DATM_REQUIRED)
    print("DATM fields the mesaclip datamode requires that MESACLIP can't supply yet:")
    print("  " + (", ".join(missing) or "none"))


def report_members():
    for s in SCENARIOS:
        print(f"{s}:")
        for case in mesaclip.members(s):
            missing = mesaclip.missing_years(s, case)
            gaps = "; ".join(f"{v} {y[0]}-{y[-1]}" if len(y) > 1 else f"{v} {y[0]}" for v, y in missing.items())
            print(f"  {'ok' if not missing else 'no files for ' + gaps}  {case}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("cdeps", nargs="?", default=os.path.join(HERE, "..", "..", "cdeps"))
    args = parser.parse_args()
    apply(os.path.expanduser(args.cdeps))
    report_fields()
    report_members()
