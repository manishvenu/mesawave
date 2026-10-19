# CLAUDE.md

Guidance for Claude Code in this repo. Claude: keep this file current. When an
open question is answered, move it to "Decisions" with the answer.

## Project

MESAWAVE: a global ensemble of ocean wave climate projections. WAVEWATCH III
(WW3) runs standalone on a global unstructured mesh, forced one way by MESACLIP
output through CESM's data models (CDEPS). The full plan is
`docs/source/proposal.pdf`. Current thinking is in the newest file in
`docs/source/discussions/`.

- **WW3 mesh:** from a NOAA collaborator. 1.67M nodes, 25 km open ocean,
  10 km coasts, 5 km US coasts, 600 s implicit timestep.
- **MESACLIP:** CESM1.3 high-res (0.25° atmosphere, 0.1° ocean and sea ice).
  https://project.cgd.ucar.edu/projects/MESACLIP/. 10-member historical
  ensemble plus future transient runs; PI control, historical and some future
  runs are on GDEX.
- **Runs:** members 5, 9, 10 with 6-hourly forcing: historical 1950–2005, and
  RCP 2.6/4.5/6.0/8.5 for 2006–2020, 2040–2060, 2080–2100. Member 10 with
  1-hourly forcing for 2000–2020.
- **Forcing:** 6-hourly 10 m winds; daily surface currents, ice concentration
  and ice thickness; floe diameter derived from concentration and thickness.
- **Later:** possible WW3-MOM6-CICE6 coupled runs, which need full DATM
  forcing, not just winds.

## Layout

- `code/`: scripts. `generate_{datm,docn,dice}_streams.py` write CPLHIST-style
  CDEPS streams files for MESACLIP, blank where unknown and checked for
  required fields. `cdeps_streams.py` is the shared writer.
  `add_mesaclip_to_cesm.py` (data in `mesaclip.py`) regenerates the MESACLIP XML
  and cap/CMake registration on the `cdeps/` submodule, starting from
  `cdeps1.0.101`; review and commit the result on its `mesaclip` branch.
- `cdeps/`: submodule, `manishvenu/CDEPS` branch `mesaclip` (draft PR
  CROCODILE-CESM/CDEPS#2). All CESM changes live here. Edit the `mesaclip`
  datamode Fortran directly on the branch; regenerate the XML with the script.
- `docs/source/`: Sphinx source, Markdown via MyST. `index.md` links the
  proposal and auto-lists `discussions/*` newest first.
- `docs/source/discussions/YYYY-MM-DD.md`: dated planning notes, one per discussion.

## Docs

- Build: `pip install -r docs/requirements.txt`, then
  `sphinx-build -b html docs/source docs/build/html`.
- `.github/workflows/docs.yml` builds on every push and PR, and deploys to
  https://manishvenu.github.io/mesawave/ from `main` only.
- `docs/build/` is git-ignored. Never commit build output.
- Non-Markdown files (e.g. PDFs) only reach the site if a page links them with
  `{download}`.

## CDEPS stream files

- Format: `<file id="stream" version="2.0">` with one `<stream_info name="...">`
  per stream. Tags: `taxmode`, `tintalgo`, `readmode`, `mapalgo`, `dtlimit`,
  `year_first`, `year_last`, `year_align`, `vectors`, `meshfile`,
  `lev_dimname`, `datafiles/file`, `datavars/var`, `offset`.
- `<var>` is `name_in_file  name_in_model`.
- Leave anything unknown blank rather than guessing. CDEPS rejects blank or
  invalid `taxmode`, `mapalgo`, `tintalgo`, `readmode`, so fill these before a run.
- CDEPS does not convert units or rotate grid-relative vectors.

## Reference CESM source (GLADE)

`~/work/installs/CESM_crocodash/components/`:
- `cdeps/streams/dshr_stream_mod.F90`: stream XML parser.
- `ww3/WW3/model/src/wav_import_export.F90`: WW3 imports `Sa_u10m`, `Sa_v10m`,
  `Sa_tbot`, `So_u`, `So_v`, `So_t`, `Si_ifrac`, `Si_thick`; also `So_bldepth`
  (CESM-coupled) and `Si_floediam` (when coupled to CICE).
- `cmeps/mediator/esmFldsExchange_cesm_mod.F90`: which component supplies each field.

## CrocoDash (regional tests)

CrocoDash builds regional MOM6 cases in CESM, optionally with active WW3 and
CICE. Use it to test MESACLIP forcings on a small regional domain before
global runs.

- Code: `~/documents/croc/regional_mom_workflows/CrocoDash`
  (`CROCODILE-CESM/CrocoDash`), part of the `croc` monorepo, whose `CLAUDE.md`
  has the minimal case-setup pattern. Don't switch that checkout's branch or
  edit it; use a worktree.
- Env: `dev_cd` (`/glade/work/manishrv/conda-envs/dev_cd`) with
  `ESMFMKFILE=/glade/work/manishrv/conda-envs/dev_cd/lib/esmf.mk`. Don't install
  into the shared workshop `CrocoDash` env.
- CESM: `~/work/installs/CESM_crocodash` (`CROCODILE-CESM/CESM`, branch
  `crocodash`). Cases go in `~/croc_cases/`, inputs in `~/scratch/croc_input/`.
- Every case needs `configure_forcings` then `process_forcings`.
  `override=True` wipes the inputdir, so recreate cases against a fresh one.
- Only MOM6 compsets are allowed (`case.py` asserts `"MOM6"` in the compset).
  WW3 reuses the regional ocean grid.
- Regional wave compsets, defined in
  `components/mom/cime_config/config_compsets.xml`:
  - `GWR_JRA`: DATM + CICE + MOM6 + WW3 (wave-ice-ocean).
  - `CWR_JRA`: DATM + DICE%SSMI + MOM6 + WW3 (wave-ocean, data ice).
  - Variants add MARBL BGC (`*1850MARBL*`), GLOFAS runoff (`*_GLOFAS`), or
    repeat-year JRA (`CWR_JRA_RYF`).
- DATM stream changes go in the case's `user_nl_datm_streams` as
  `streamname:field = value`. Only streams the compset already defines can be
  changed (`components/cdeps/cime_config/stream_cdeps.py`).

## MCP servers

`.mcp.json` connects the three croc MCP servers. They run from `dev_cd`, and
their code is in `~/documents/croc/dev/`.
- `crocodash`: create cases, configure and process forcings.
- `cesm-runner`: case setup/build/submit, xmlquery/xmlchange, logs, crocontainer.
- `ocean-debugger`: log triage, MOM_input inspection, CFL/timestep checks,
  expert domain knowledge.

Say so before slow calls (`create_case`, `process_forcings`, `case_build`),
and flag any that run past ~4 minutes.

## Open questions

1. **Sea ice source.** DOCN exports no ice fields. DICE exports `Si_ifrac` but
   not `Si_thick` or `Si_floediam`, and CMEPS only takes `Si_thick` from an ice
   component. Ask Alper Altuntas how the CESM3-style ice attenuation gets its inputs.
2. **POP currents.** `UVEL`/`VVEL` are in cm/s, aligned with the grid's own
   axes, and sit at cell corners on the 0.1° tripole grid. They likely need
   preprocessing before DOCN can use them.
3. **6-hourly variables on GDEX.** Which MESACLIP fields exist at 6-hourly
   decides whether full DATM (MOM6-CICE6) is feasible.
4. **`So_t` and `Sa_tbot`.** WW3 imports them, but they're not in proposal Fig. 2.
   Include them in the streams or not?
5. **Wave-only regional tests.** Plan: run regional WW3 standalone
   (DATM + DOCN + DICE + WW3 on the custom grid). No new WW3 rule is needed:
   DOCN satisfies the existing "WW3 needs an active or data ocean" rule.
   `GWR_JRA` covers wave-ice-ocean tests in the meantime. What still blocks it
   (paths in CrocoDash's embedded `CrocoDash/visualCaseGen/`, which `dev_cd` uses):
   - `visualCaseGen/specs/relational_constraints.py`: "Custom grids can only be
     generated when MOM6 and/or CLM are selected" and "Custom OCN grids can
     only be generated for MOM6". These need relaxing for DOCN.
   - CrocoDash `case.py` also asserts `"MOM6"` in the compset.
   - Injection point: `visualCaseGen/initialize.py` passes
     `get_relational_constraints(cvars)`, a `{constraint: message}` dict, to
     `csp.initialize`. CrocoDash calls it from `Case.__init__` via
     `initialize_visualCaseGen(cesmroot)`.

## Decisions

- **Winds: CAM bottom winds (`UBOT`/`VBOT`) for now** (2026-10-16). WW3
  treats `Sa_u10m` as a 10 m wind, but the lowest CAM level is ~60 m (check
  `ZBOT`), so expect winds and waves biased high until rescaled to 10 m (e.g.
  to CAM's `U10` speed, if saved 6-hourly). Pass `ZBOT` as `Sa_z` for MOM6.
- **No runs span historical and future MESACLIP** (2026-10-16). Each run
  uses one MESACLIP scenario and member; combining them is out of scope.
- **MESACLIP enters CESM as CDEPS modes** (2026-10-16): `DATM%MESACLIP-<scenario>`
  and `DOCN%MESACLIP-<scenario>` with one case variable, `DATM_MESACLIP_CASE`,
  read by `mesaclip` datamodes copied from CPLHIST, which also do the unit
  conversions. Instantaneous `h2` where it exists. DICE is deferred. Limits are
  in `docs/source/mesaclip_cesm_modes.md`.
- **Stand-ins for fields MESACLIP lacks** (2026-10-16): 2 m `TREFHT`/`QREFHT` and
  `PS` (`h2`) for lowest-level T, q and p; potential temperature and density
  computed; direct shortwave = `FSDS` minus diffuse, split with JRA's fractions;
  topography from DATM's observed stream; WW3's 10 m winds = `UBOT`/`VBOT`.

## Working rules

- Keep changes small and simple. Do only what's asked.
- Ask before committing or pushing. No `Co-Authored-By` lines in commits, and
  no @-mentions on GitHub.
- Run `module load gh` before using the `gh` CLI.
- Don't recursively scan GDEX/GLADE data collections. Look up specific paths.
- Never move, copy or delete anything in CESM inputdata.
